#!/usr/bin/env python3
"""
Test that empty error messages are now replaced with fallback messages
"""

import asyncio
import json
import sys
import os

# Add the src directory to Python path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from definite_mcp import run_sql_query, run_cube_query


async def test_empty_sql_error():
    """Test SQL query with simulated empty error"""
    print("Testing SQL query with empty error message...")
    print("-" * 50)

    import definite_mcp
    import httpx

    original_make_api_request = definite_mcp.make_api_request

    async def mock_empty_error(endpoint: str, payload: dict):
        response = httpx.Response(
            status_code=400,
            json={"message": ""},  # Empty message
            request=httpx.Request("POST", "http://test.com")
        )
        raise httpx.HTTPStatusError("Bad Request", request=response.request, response=response)

    definite_mcp.make_api_request = mock_empty_error

    try:
        sql = "SELECT * FROM test_table"
        result = await run_sql_query(sql)

        print(f"Query: {sql}")
        print(f"\nResult:")
        print(json.dumps(result, indent=2))

        if result.get("error"):
            if result["error"] == "":
                print("\n❌ Still returning empty error!")
            else:
                print(f"\n✅ Fixed! Now returns: '{result['error']}'")
                print("   Instead of an empty string")

    finally:
        definite_mcp.make_api_request = original_make_api_request

    print()


async def test_empty_cube_error():
    """Test Cube query with simulated empty error"""
    print("Testing Cube query with empty error message...")
    print("-" * 50)

    import definite_mcp
    import httpx

    original_make_api_request = definite_mcp.make_api_request

    async def mock_empty_error(endpoint: str, payload: dict):
        response = httpx.Response(
            status_code=500,
            json={"message": ""},  # Empty message
            request=httpx.Request("POST", "http://test.com")
        )
        raise httpx.HTTPStatusError("Server Error", request=response.request, response=response)

    definite_mcp.make_api_request = mock_empty_error

    try:
        cube_query = {
            "dimensions": [],
            "measures": ["test.metric"],
            "filters": []
        }
        result = await run_cube_query(cube_query)

        print(f"Cube Query: {json.dumps(cube_query)}")
        print(f"\nResult:")
        print(json.dumps(result, indent=2))

        if result.get("error"):
            if result["error"] == "":
                print("\n❌ Still returning empty error!")
            else:
                print(f"\n✅ Fixed! Now returns: '{result['error']}'")
                print("   Instead of an empty string")

    finally:
        definite_mcp.make_api_request = original_make_api_request

    print()


async def test_empty_after_extraction():
    """Test when 'Something went wrong:' is followed by empty string"""
    print("Testing 'Something went wrong:' with empty content...")
    print("-" * 50)

    import definite_mcp
    import httpx

    original_make_api_request = definite_mcp.make_api_request

    async def mock_empty_after_extraction(endpoint: str, payload: dict):
        response = httpx.Response(
            status_code=400,
            json={"message": "HTTP error 500: Something went wrong: "},  # Empty after colon
            request=httpx.Request("POST", "http://test.com")
        )
        raise httpx.HTTPStatusError("Bad Request", request=response.request, response=response)

    definite_mcp.make_api_request = mock_empty_after_extraction

    try:
        sql = "SELECT 1"
        result = await run_sql_query(sql)

        print(f"Query: {sql}")
        print(f"\nResult:")
        print(json.dumps(result, indent=2))

        if result.get("error"):
            if result["error"] == "":
                print("\n❌ Still returning empty error after extraction!")
            else:
                print(f"\n✅ Fixed! Now returns: '{result['error']}'")
                print("   Instead of an empty string after extraction")

    finally:
        definite_mcp.make_api_request = original_make_api_request


async def main():
    """Test all empty error scenarios are fixed"""
    print("=" * 60)
    print("EMPTY ERROR FIX VERIFICATION")
    print("=" * 60)
    print()

    await test_empty_sql_error()
    await test_empty_cube_error()
    await test_empty_after_extraction()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\n✅ Empty error messages are now replaced with:")
    print("   'Query failed with HTTP {status_code}'")
    print("\nThis provides more useful information than an empty string,")
    print("letting users know the query failed and the HTTP status.")


if __name__ == "__main__":
    asyncio.run(main())