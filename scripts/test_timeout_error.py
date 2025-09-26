#!/usr/bin/env python3
"""
Test what error message is returned when the MCP hits a timeout
"""

import asyncio
import json
import sys
import os
import time

# Add the src directory to Python path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from definite_mcp import run_sql_query


async def simulate_timeout_with_mock():
    """Try to simulate a timeout by mocking the httpx client"""
    print("Simulating timeout scenario...")
    print("-" * 50)

    # We'll patch the make_api_request to simulate a timeout
    import definite_mcp
    import httpx

    # Save original function
    original_make_api_request = definite_mcp.make_api_request

    # Create a function that will timeout
    async def mock_timeout_request(endpoint: str, payload: dict):
        # Simulate a request that takes too long
        raise httpx.ReadTimeout("The read operation timed out")

    # Patch the function
    definite_mcp.make_api_request = mock_timeout_request

    try:
        # Try to run a query
        sql = "SELECT 1 as test"
        print(f"Query: {sql}")
        print("\nAttempting query with simulated timeout...")

        result = await run_sql_query(sql)

        print("\nResult structure:")
        print(json.dumps(result, indent=2))

        if "error" in result:
            print(f"\n✓ Timeout error captured!")
            print(f"Error field: {result['error']}")
            print(f"Status field: {result.get('status')}")
            print(f"HTTP status field: {result.get('http_status', 'Not present')}")
            print(f"Query field present: {'query' in result}")

    finally:
        # Restore original function
        definite_mcp.make_api_request = original_make_api_request

    print()


async def simulate_connect_timeout():
    """Simulate a connection timeout"""
    print("Simulating connection timeout...")
    print("-" * 50)

    import definite_mcp
    import httpx

    original_make_api_request = definite_mcp.make_api_request

    async def mock_connect_timeout(endpoint: str, payload: dict):
        raise httpx.ConnectTimeout("Connection timeout")

    definite_mcp.make_api_request = mock_connect_timeout

    try:
        sql = "SELECT 2 as test"
        print(f"Query: {sql}")
        print("\nAttempting query with simulated connection timeout...")

        result = await run_sql_query(sql)

        print("\nResult structure:")
        print(json.dumps(result, indent=2))

        if "error" in result:
            print(f"\n✓ Connection timeout error captured!")
            print(f"Error message: {result['error']}")

    finally:
        definite_mcp.make_api_request = original_make_api_request

    print()


async def simulate_generic_timeout():
    """Simulate a generic timeout error"""
    print("Simulating generic timeout...")
    print("-" * 50)

    import definite_mcp
    import httpx

    original_make_api_request = definite_mcp.make_api_request

    async def mock_generic_timeout(endpoint: str, payload: dict):
        raise httpx.TimeoutException("Request timed out")

    definite_mcp.make_api_request = mock_generic_timeout

    try:
        sql = "SELECT 3 as test"
        print(f"Query: {sql}")
        print("\nAttempting query with simulated generic timeout...")

        result = await run_sql_query(sql)

        print("\nResult structure:")
        print(json.dumps(result, indent=2))

        if "error" in result:
            print(f"\n✓ Generic timeout error captured!")
            print(f"Error message: {result['error']}")

    finally:
        definite_mcp.make_api_request = original_make_api_request

    print()


async def main():
    """Test timeout error handling"""
    print("=" * 60)
    print("MCP TIMEOUT ERROR MESSAGE TEST")
    print("=" * 60)
    print()

    await simulate_timeout_with_mock()
    await simulate_connect_timeout()
    await simulate_generic_timeout()

    print("=" * 60)
    print("TIMEOUT ERROR SUMMARY")
    print("=" * 60)
    print("\nWhen a timeout occurs, the MCP returns:")
    print("• error: The exception message (e.g., 'The read operation timed out')")
    print("• status: 'failed'")
    print("• query: The original SQL query")
    print("• http_status: Not present (since no HTTP response was received)")
    print("\nThe error is caught by the generic Exception handler since")
    print("httpx timeout errors are not HTTPStatusError exceptions.")


if __name__ == "__main__":
    asyncio.run(main())