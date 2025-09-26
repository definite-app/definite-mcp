#!/usr/bin/env python3
"""
Test the improved error messages with exception details
"""

import asyncio
import json
import sys
import os

# Add the src directory to Python path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from definite_mcp import run_sql_query, run_cube_query


async def test_various_exceptions():
    """Test how different exceptions are reported"""
    print("Testing improved error messages with exception details...")
    print("=" * 60)

    import definite_mcp
    import httpx

    original = definite_mcp.make_api_request

    # Test different exception types
    test_cases = [
        (httpx.ConnectError(""), "ConnectError with empty message"),
        (httpx.TimeoutException(""), "TimeoutException with empty message"),
        (httpx.NetworkError(""), "NetworkError with empty message"),
        (httpx.ProtocolError(""), "ProtocolError with empty message"),
        (ConnectionError(""), "Standard ConnectionError with empty message"),
        (ValueError(""), "ValueError with empty message"),
        (Exception(""), "Generic Exception with empty message"),
        (httpx.ConnectError("Connection refused"), "ConnectError with message"),
    ]

    for exc, description in test_cases:
        print(f"\n{description}:")
        print("-" * 40)

        async def mock_error(endpoint: str, payload: dict):
            raise exc

        definite_mcp.make_api_request = mock_error

        try:
            result = await run_sql_query("SELECT 1")

            print(f"Error message: {result['error']}")
            if 'exception_type' in result:
                print(f"Exception type: {result['exception_type']}")
            print(f"Status: {result['status']}")

            # Check if it's more informative than before
            if result['error'] != "Query failed with unknown error":
                print("✅ More specific than 'unknown error'")
            else:
                print("❌ Still shows 'unknown error'")

        except Exception as e:
            print(f"Unexpected error: {e}")

        finally:
            definite_mcp.make_api_request = original

    print("\n" + "=" * 60)


async def test_cube_errors():
    """Test Cube query error handling"""
    print("\nTesting Cube query error handling...")
    print("=" * 60)

    import definite_mcp
    import httpx

    original = definite_mcp.make_api_request

    async def mock_timeout(endpoint: str, payload: dict):
        raise httpx.TimeoutException("")

    definite_mcp.make_api_request = mock_timeout

    try:
        cube_query = {"measures": ["test.metric"]}
        result = await run_cube_query(cube_query)

        print(f"Cube error message: {result['error']}")
        if 'exception_type' in result:
            print(f"Exception type: {result['exception_type']}")
        print(f"Status: {result['status']}")

    finally:
        definite_mcp.make_api_request = original


async def test_real_query():
    """Test with a real query to see actual error"""
    print("\nTesting with actual query...")
    print("=" * 60)

    sql = """SELECT table_catalog, table_schema, table_name
FROM information_schema.tables
WHERE table_name ILIKE '%test%'
LIMIT 5"""

    result = await run_sql_query(sql)

    if "error" in result:
        print(f"Error: {result['error']}")
        if 'exception_type' in result:
            print(f"Exception type: {result['exception_type']}")
    else:
        print(f"Query succeeded with {len(result.get('data', []))} rows")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("TESTING IMPROVED ERROR MESSAGES")
    print("=" * 60)
    print()

    await test_various_exceptions()
    await test_cube_errors()
    await test_real_query()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\nError messages now include:")
    print("• Specific exception class name when message is empty")
    print("• exception_type field with full module.ClassName")
    print("• Better context for debugging network/connection issues")


if __name__ == "__main__":
    asyncio.run(main())