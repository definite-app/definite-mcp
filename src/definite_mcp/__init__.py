#!/usr/bin/env python3
"""
Definite API MCP Server

A Model Context Protocol server that provides access to Definite API
for running SQL and Cube queries.
"""

import os
import json
import sys
import asyncio
from typing import Optional, Dict, Any, List, Union
from dotenv import load_dotenv
import httpx
from mcp.server.fastmcp import FastMCP

# Load .env file if it exists (for local development)
# When installed via uvx, environment variables are passed via MCP config
try:
    load_dotenv()
except Exception:
    # Ignore if .env file doesn't exist or can't be loaded
    pass

mcp = FastMCP("definite-api")

API_KEY = os.getenv("DEFINITE_API_KEY")
API_BASE_URL = os.getenv("DEFINITE_API_BASE_URL", "https://api.definite.app")

# Debug: Show configuration info
print(f"Definite MCP Server starting...", file=sys.stderr)
print(f"API Base URL: {API_BASE_URL}", file=sys.stderr)
print(f"API Key configured: {'Yes' if API_KEY else 'No'}", file=sys.stderr)

if not API_KEY:
    print("ERROR: DEFINITE_API_KEY environment variable is required", file=sys.stderr)
    print("Make sure to set DEFINITE_API_KEY in your MCP configuration", file=sys.stderr)
    sys.exit(1)


async def make_api_request(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Make an authenticated request to the Definite API with retry logic"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    max_retries = 3
    url = f"{API_BASE_URL}/v1/{endpoint}"

    for attempt in range(max_retries):
        # Use 1 second connect timeout for first attempts, 30 seconds for final attempt
        connect_timeout = 1.0 if attempt < max_retries - 1 else 30.0

        timeout = httpx.Timeout(
            timeout=120.0,      # Total timeout
            connect=connect_timeout,  # Connection timeout (1s for retries, 30s for final)
            read=120.0,         # Read timeout for long-running queries
            write=30.0,         # Write timeout
            pool=10.0           # Pool timeout
        )

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.ConnectTimeout as e:
            # Only retry on connection timeouts, not on other errors
            if attempt < max_retries - 1:
                # Exponential backoff: wait 1s, 2s before retrying
                wait_time = 2 ** attempt  # 1, 2 seconds
                print(f"Connection timeout after {connect_timeout}s, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
                await asyncio.sleep(wait_time)
                continue
            else:
                # Final attempt failed, re-raise the exception
                print(f"Connection timeout after {connect_timeout}s on final attempt", file=sys.stderr)
                raise
        except Exception:
            # For any other exception, don't retry, just raise
            raise


@mcp.tool()
async def run_sql_query(sql: str, integration_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute a SQL query on a Definite database integration.

    Args:
        sql: The SQL query to execute
        integration_id: Optional integration ID. If not provided, uses the default integration

    Returns:
        The query results as returned by the Definite API
    """
    payload = {"sql": sql}
    if integration_id:
        payload["integration_id"] = integration_id
    else:
        # If no integration ID is provided, use the default one from the environment
        _TABLE_INTEGRATION_ID = os.getenv("_TABLE_INTEGRATION_ID")
        if _TABLE_INTEGRATION_ID:
            payload["integration_id"] = _TABLE_INTEGRATION_ID

        

    try:
        result = await make_api_request("query", payload)
        return result
    except httpx.HTTPStatusError as e:
        # Try to extract the actual error message from the response
        error_detail = e.response.text
        try:
            error_json = json.loads(error_detail)
            if "message" in error_json:
                # Extract the actual SQL error from nested message
                msg = error_json["message"]
                if "Something went wrong:" in msg:
                    # Extract just the SQL error part
                    sql_error = msg.split("Something went wrong:", 1)[1].strip()
                    return {
                        "error": sql_error if sql_error else f"Query failed with HTTP {e.response.status_code}",
                        "status": "failed",
                        "http_status": e.response.status_code,
                        "query": sql,
                        "request_details": {
                            "url": f"{API_BASE_URL}/v1/query",
                            "payload": payload,
                            "api_key_configured": bool(API_KEY),
                            "timeout": "connect: 1s (with retry), read: 120s, total: 120s"
                        }
                    }
                else:
                    # If message is empty, provide a fallback error message
                    error_msg = msg if msg else f"Query failed with HTTP {e.response.status_code}"
                    return {
                        "error": error_msg,
                        "status": "failed",
                        "http_status": e.response.status_code,
                        "query": sql,
                        "request_details": {
                            "url": f"{API_BASE_URL}/v1/query",
                            "payload": payload,
                            "api_key_configured": bool(API_KEY),
                            "timeout": "connect: 1s (with retry), read: 120s, total: 120s"
                        }
                    }
        except (json.JSONDecodeError, KeyError):
            pass

        return {
            "error": f"HTTP {e.response.status_code}: {error_detail}",
            "status": "failed",
            "query": sql,
            "request_details": {
                "url": f"{API_BASE_URL}/v1/query",
                "payload": payload,
                "api_key_configured": bool(API_KEY),
                "timeout": "connect: 30s, read: 120s, total: 120s"
            }
        }
    except Exception as e:
        error_msg = str(e)

        # If empty message, provide more specific error based on exception type
        if not error_msg:
            if e.__class__.__module__ == 'httpx':
                # Include the exception class name for httpx errors
                error_msg = f"Query failed with {e.__class__.__name__}"
            else:
                error_msg = f"Query failed with {e.__class__.__name__}: unknown error"

        # Build error response with additional context
        error_response = {
            "error": error_msg,
            "status": "failed",
            "query": sql
        }

        # Add exception type for debugging
        error_response["exception_type"] = f"{e.__class__.__module__}.{e.__class__.__name__}"

        # Add request details for debugging
        error_response["request_details"] = {
            "url": f"{API_BASE_URL}/v1/query",
            "payload": payload,
            "api_key_configured": bool(API_KEY),
            "timeout": "connect: 30s, read: 120s, total: 120s"
        }

        return error_response


@mcp.tool()
async def run_cube_query(
    cube_query: Dict[str, Any],
    integration_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a Cube query on a Definite Cube integration.

    Args:
        cube_query: The Cube query in JSON format with dimensions, filters, measures, etc.
        integration_id: Optional integration ID. If not provided, uses the default integration

    Returns:
        The query results as returned by the Definite API

    Example cube_query:
    {
        "dimensions": [],
        "filters": [],
        "measures": ["hubspot_deals.win_rate"],
        "timeDimensions": [{
            "dimension": "hubspot_deals.close_date",
            "granularity": "month"
        }],
        "order": [],
        "limit": 2000
    }
    """
    payload = {"cube_query": cube_query}
    if integration_id:
        payload["integration_id"] = integration_id

    try:
        result = await make_api_request("query", payload)
        return result
    except httpx.HTTPStatusError as e:
        # Try to extract the actual error message from the response
        error_detail = e.response.text
        try:
            error_json = json.loads(error_detail)
            if "message" in error_json:
                # Extract the actual error from nested message
                msg = error_json["message"]
                if "Something went wrong:" in msg:
                    # Extract just the error part
                    cube_error = msg.split("Something went wrong:", 1)[1].strip()
                    return {
                        "error": cube_error if cube_error else f"Query failed with HTTP {e.response.status_code}",
                        "status": "failed",
                        "http_status": e.response.status_code,
                        "cube_query": cube_query,
                        "request_details": {
                            "url": f"{API_BASE_URL}/v1/query",
                            "payload": payload,
                            "api_key_configured": bool(API_KEY),
                            "timeout": "connect: 1s (with retry), read: 120s, total: 120s"
                        }
                    }
                else:
                    # If message is empty, provide a fallback error message
                    error_msg = msg if msg else f"Query failed with HTTP {e.response.status_code}"
                    return {
                        "error": error_msg,
                        "status": "failed",
                        "http_status": e.response.status_code,
                        "cube_query": cube_query,
                        "request_details": {
                            "url": f"{API_BASE_URL}/v1/query",
                            "payload": payload,
                            "api_key_configured": bool(API_KEY),
                            "timeout": "connect: 1s (with retry), read: 120s, total: 120s"
                        }
                    }
        except (json.JSONDecodeError, KeyError):
            pass

        return {
            "error": f"HTTP {e.response.status_code}: {error_detail}",
            "status": "failed",
            "cube_query": cube_query,
            "request_details": {
                "url": f"{API_BASE_URL}/v1/query",
                "payload": payload,
                "api_key_configured": bool(API_KEY),
                "timeout": "connect: 30s, read: 120s, total: 120s"
            }
        }
    except Exception as e:
        error_msg = str(e)

        # If empty message, provide more specific error based on exception type
        if not error_msg:
            if e.__class__.__module__ == 'httpx':
                # Include the exception class name for httpx errors
                error_msg = f"Query failed with {e.__class__.__name__}"
            else:
                error_msg = f"Query failed with {e.__class__.__name__}: unknown error"

        # Build error response with additional context
        error_response = {
            "error": error_msg,
            "status": "failed",
            "cube_query": cube_query
        }

        # Add exception type for debugging
        error_response["exception_type"] = f"{e.__class__.__module__}.{e.__class__.__name__}"

        # Add request details for debugging
        error_response["request_details"] = {
            "url": f"{API_BASE_URL}/v1/query",
            "payload": payload,
            "api_key_configured": bool(API_KEY),
            "timeout": "connect: 30s, read: 120s, total: 120s"
        }

        return error_response


def main():
    """Entry point for the definite-mcp command"""
    mcp.run()


if __name__ == "__main__":
    main()