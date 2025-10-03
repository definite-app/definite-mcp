#!/usr/bin/env python3
"""
Definite API MCP Server

A Model Context Protocol server that provides access to the Definite API
for running SQL and Cube queries.

Key client transport changes vs. the original:
- Single shared httpx.AsyncClient (connection reuse; avoids pool thrash)
- trust_env=False (ignore env proxies that can stall)
- http2=False (avoid ALPN/HTTP2 stalls)
- Fast connect timeout + per-attempt overall deadline + retries
- Better diagnostics: X-Request-Id, custom User-Agent, phase tagging, DNS log
"""

import os
import sys
import json
import uuid
import time
import socket
import asyncio
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import httpx
from mcp.server.fastmcp import FastMCP

# -------------------------
# Environment / logging
# -------------------------

# Load .env for local dev; MCP config envs will override
try:
    load_dotenv()
except Exception:
    pass

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(stream=sys.stderr, level=LOG_LEVEL)
log = logging.getLogger("definite-mcp")

mcp = FastMCP("definite-api")

API_KEY = os.getenv("DEFINITE_API_KEY")
API_BASE_URL = os.getenv("DEFINITE_API_BASE_URL", "https://api.definite.app").rstrip("/")

print("Definite MCP Server starting...", file=sys.stderr)
print(f"API Base URL: {API_BASE_URL}", file=sys.stderr)
print(f"API Key configured: {'Yes' if bool(API_KEY) else 'No'}", file=sys.stderr)

if not API_KEY:
    print("ERROR: DEFINITE_API_KEY environment variable is required", file=sys.stderr)
    print("Make sure to set DEFINITE_API_KEY in your MCP configuration", file=sys.stderr)
    sys.exit(1)

# -------------------------
# HTTP client config
# -------------------------

# Fast connect to detect bad routes quickly;
# generous read for long-running queries; short pool to avoid head-of-line waits.
CONNECT_TIMEOUT_S = float(os.getenv("DEFINITE_CONNECT_TIMEOUT_S", "2.0"))
READ_TIMEOUT_S = float(os.getenv("DEFINITE_READ_TIMEOUT_S", "120.0"))
WRITE_TIMEOUT_S = float(os.getenv("DEFINITE_WRITE_TIMEOUT_S", "10.0"))
POOL_TIMEOUT_S = float(os.getenv("DEFINITE_POOL_TIMEOUT_S", "2.0"))

# Overall per-attempt deadline (connect + TLS + write + first-byte)
ATTEMPT_DEADLINE_S = float(os.getenv("DEFINITE_ATTEMPT_DEADLINE_S", "15.0"))

# Retry policy
RETRIES = int(os.getenv("DEFINITE_RETRIES", "4"))
BACKOFF_BASE_S = float(os.getenv("DEFINITE_BACKOFF_BASE_S", "0.5"))

# Client concurrency limits
LIMITS = httpx.Limits(
    max_connections=int(os.getenv("DEFINITE_MAX_CONNECTIONS", "50")),
    max_keepalive_connections=int(os.getenv("DEFINITE_MAX_KEEPALIVE", "20")),
)

TIMEOUT = httpx.Timeout(
    connect=CONNECT_TIMEOUT_S,
    read=READ_TIMEOUT_S,
    write=WRITE_TIMEOUT_S,
    pool=POOL_TIMEOUT_S,
)

# One shared client for the process
_HTTP = httpx.AsyncClient(
    base_url=API_BASE_URL,
    timeout=TIMEOUT,
    limits=LIMITS,
    trust_env=False,          # ignore HTTP(S)_PROXY / NO_PROXY surprises
    http2=False,              # avoid ALPN/HTTP2 stalls on some edges/proxies
    follow_redirects=True,
)

def _timeout_string() -> str:
    return (
        f"connect: {CONNECT_TIMEOUT_S:.0f}s, read: {READ_TIMEOUT_S:.0f}s, "
        f"write: {WRITE_TIMEOUT_S:.0f}s, pool: {POOL_TIMEOUT_S:.0f}s, "
        f"attempt_deadline: {ATTEMPT_DEADLINE_S:.0f}s, retries: {RETRIES}, "
        f"http2: false, trust_env: false"
    )

# -------------------------
# Diagnostics helpers
# -------------------------

def _resolve_dns_once(host: str) -> None:
    """Log DNS resolution results for visibility."""
    try:
        addrs = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
        uniq = sorted({f"{fam}/{socktype}/{proto}@{addr[0]}" for fam, socktype, proto, _, addr in addrs})
        log.info("DNS %s -> %s", host, uniq)
    except Exception as e:
        log.debug("DNS resolution failed for %s: %s", host, e)

_DNS_LOGGED = False

async def _preflight_health() -> None:
    """
    Optional preflight to validate the network path. 404 is fine (no route),
    we only care about reachability and fast response.
    """
    try:
        r = await asyncio.wait_for(
            _HTTP.head("/v1/healthz", headers={"User-Agent": "definite-mcp/health"}),
            timeout=5.0,
        )
        log.info("Preflight /v1/healthz status=%s", r.status_code)
    except Exception as e:
        # Non-fatal: this is a hint if the path is broken
        log.warning("Preflight /v1/healthz failed: %s", e)

async def _post_with_retries(path: str, json_body: Dict[str, Any], headers: Dict[str, str]) -> httpx.Response:
    """
    POST with fast connect, per-attempt deadline, exponential backoff retries.
    """
    attempt = 0
    backoff = BACKOFF_BASE_S
    while True:
        attempt += 1
        try:
            log.info("[%s] POST %s attempt %d/%d", headers.get("X-Request-Id"), path, attempt, RETRIES)
            # Per-attempt overall deadline (connect+TLS+write+first-byte)
            resp = await asyncio.wait_for(
                _HTTP.post(path, json=json_body, headers=headers),
                timeout=ATTEMPT_DEADLINE_S,
            )
            resp.raise_for_status()
            return resp
        except (httpx.ConnectTimeout, httpx.ConnectError,
                httpx.ReadTimeout, httpx.RemoteProtocolError,
                httpx.PoolTimeout, asyncio.TimeoutError) as e:
            log.warning("[%s] attempt %d/%d %s: %s",
                        headers.get("X-Request-Id"), attempt, RETRIES, e.__class__.__name__, e)
            if attempt >= RETRIES:
                raise
            await asyncio.sleep(backoff)
            backoff *= 2.0

async def make_api_request(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Make an authenticated request to the Definite API with robust connect handling.
    """
    rid = str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "definite-mcp/0.2",
        "X-Request-Id": rid,
    }

    # One-time DNS visibility
    global _DNS_LOGGED
    if not _DNS_LOGGED:
        _DNS_LOGGED = True
        try:
            host = API_BASE_URL.split("://", 1)[1].split("/", 1)[0]
            _resolve_dns_once(host)
        except Exception:
            pass

    # Optional preflight (does not fail the main call)
    await _preflight_health()

    path = f"/v1/{endpoint.lstrip('/')}"
    t0 = time.monotonic()
    try:
        resp = await _post_with_retries(path, payload, headers)
        log.info("[%s] OK %s %s in %.0fms", rid, resp.status_code, path, (time.monotonic() - t0) * 1000)
        return resp.json()
    except Exception as e:
        # Re-raise; callers convert into structured error payloads
        log.error("[%s] POST %s failed after %.0fms: %s",
                  rid, path, (time.monotonic() - t0) * 1000, repr(e))
        raise

# -------------------------
# Error helpers
# -------------------------

def _phase_for_exception(exc: Exception) -> str:
    if isinstance(exc, httpx.ConnectTimeout):
        return "connect_timeout"
    if isinstance(exc, httpx.ReadTimeout):
        return "read_timeout"
    if isinstance(exc, httpx.PoolTimeout):
        return "pool_timeout"
    if isinstance(exc, asyncio.TimeoutError):
        return "attempt_deadline_timeout"
    if isinstance(exc, httpx.ConnectError):
        return "connect_error"
    if isinstance(exc, httpx.RemoteProtocolError):
        return "protocol_error"
    return exc.__class__.__name__

def _common_request_details(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "url": f"{API_BASE_URL}/v1/{endpoint}",
        "payload": payload,
        "api_key_configured": bool(API_KEY),
        "timeouts": _timeout_string(),
    }

# -------------------------
# MCP tools
# -------------------------

@mcp.tool()
async def run_sql_query(sql: str, integration_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute a SQL query on a Definite database integration.
    """
    payload: Dict[str, Any] = {"sql": sql}
    if integration_id:
        payload["integration_id"] = integration_id
    else:
        # Fallback default integration id from env if present
        _TABLE_INTEGRATION_ID = os.getenv("_TABLE_INTEGRATION_ID")
        if _TABLE_INTEGRATION_ID:
            payload["integration_id"] = _TABLE_INTEGRATION_ID

    try:
        result = await make_api_request("query", payload)
        return result

    except httpx.HTTPStatusError as e:
        # Server responded with non-2xx
        error_detail = e.response.text
        # Try to extract nested "message" and trim "Something went wrong:"
        try:
            error_json = json.loads(error_detail)
            msg = error_json.get("message", "")
            if msg:
                if "Something went wrong:" in msg:
                    msg = msg.split("Something went wrong:", 1)[1].strip() or msg
                return {
                    "error": msg,
                    "status": "failed",
                    "http_status": e.response.status_code,
                    "query": sql,
                    "request_details": _common_request_details("query", payload),
                }
        except (json.JSONDecodeError, KeyError):
            pass

        return {
            "error": f"HTTP {e.response.status_code}: {error_detail}",
            "status": "failed",
            "query": sql,
            "request_details": _common_request_details("query", payload),
        }

    except Exception as e:
        # Transport or attempt-deadline errors
        phase = _phase_for_exception(e)
        msg = str(e) or f"Query failed with {e.__class__.__name__}"
        return {
            "error": msg,
            "status": "failed",
            "query": sql,
            "exception_type": f"{e.__class__.__module__}.{e.__class__.__name__}",
            "request_details": {
                **_common_request_details("query", payload),
                "phase": phase,
            },
        }


@mcp.tool()
async def run_cube_query(
    cube_query: Dict[str, Any],
    integration_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a Cube query on a Definite Cube integration.
    """
    payload: Dict[str, Any] = {"cube_query": cube_query}
    if integration_id:
        payload["integration_id"] = integration_id
    else:
        # Fallback default integration id from env if present
        _CUBE_INTEGRATION_ID = os.getenv("_CUBE_INTEGRATION_ID")
        if _CUBE_INTEGRATION_ID:
            payload["integration_id"] = _CUBE_INTEGRATION_ID

    try:
        result = await make_api_request("query", payload)
        return result

    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        try:
            error_json = json.loads(error_detail)
            msg = error_json.get("message", "")
            if msg:
                if "Something went wrong:" in msg:
                    msg = msg.split("Something went wrong:", 1)[1].strip() or msg
                return {
                    "error": msg,
                    "status": "failed",
                    "http_status": e.response.status_code,
                    "cube_query": cube_query,
                    "request_details": _common_request_details("query", payload),
                }
        except (json.JSONDecodeError, KeyError):
            pass

        return {
            "error": f"HTTP {e.response.status_code}: {error_detail}",
            "status": "failed",
            "cube_query": cube_query,
            "request_details": _common_request_details("query", payload),
        }

    except Exception as e:
        phase = _phase_for_exception(e)
        msg = str(e) or f"Query failed with {e.__class__.__name__}"
        return {
            "error": msg,
            "status": "failed",
            "cube_query": cube_query,
            "exception_type": f"{e.__class__.__module__}.{e.__class__.__name__}",
            "request_details": {
                **_common_request_details("query", payload),
                "phase": phase,
            },
        }

# -------------------------
# Entrypoint
# -------------------------

def main():
    """Entry point for the definite-mcp command"""
    # Note: FastMCP is long-lived; we intentionally keep _HTTP open for reuse.
    # If you add a shutdown hook in the future, call: await _HTTP.aclose()
    mcp.run()

if __name__ == "__main__":
    main()