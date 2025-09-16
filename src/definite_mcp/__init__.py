#!/usr/bin/env python3
"""
Definite API MCP Server

A Model Context Protocol server that provides access to Definite API
for running SQL and Cube queries.
"""

import os
import json
import sys
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
    """Make an authenticated request to the Definite API"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/v1/{endpoint}",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()


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

    try:
        result = await make_api_request("query", payload)
        return result
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "status": "failed"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }


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
        return {
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "status": "failed"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }


def main():
    """Entry point for the definite-mcp command"""
    mcp.run()


if __name__ == "__main__":
    main()