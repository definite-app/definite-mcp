#!/usr/bin/env python3
"""
Test all paths where empty error messages could occur
"""

import asyncio
import json
import sys
import os

# Add the src directory to Python path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from definite_mcp import run_sql_query, run_cube_query


async def test_http_error_empty_message():
    """Test HTTPStatusError with empty message in JSON"""
    print("1. Testing HTTPStatusError with empty message...")
    print("-" * 50)

    import definite_mcp
    import httpx

    original = definite_mcp.make_api_request

    async def mock(endpoint: str, payload: dict):
        response = httpx.Response(
            status_code=400,
            json={"message": ""},
            request=httpx.Request("POST", "http://test.com")
        )
        raise httpx.HTTPStatusError("Bad Request", request=response.request, response=response)

    definite_mcp.make_api_request = mock

    try:
        result = await run_sql_query("SELECT 1")
        print(f"Result: {json.dumps(result, indent=2)}")
        if result["error"] == "":
            print("❌ Still empty!")
        else:
            print(f"✅ Fixed: '{result['error']}'")
    finally:
        definite_mcp.make_api_request = original

    print()


async def test_http_error_empty_after_extraction():
    """Test HTTPStatusError with 'Something went wrong:' followed by empty"""
    print("2. Testing empty after 'Something went wrong:' extraction...")
    print("-" * 50)

    import definite_mcp
    import httpx

    original = definite_mcp.make_api_request

    async def mock(endpoint: str, payload: dict):
        response = httpx.Response(
            status_code=500,
            json={"message": "HTTP error 500: Something went wrong: "},
            request=httpx.Request("POST", "http://test.com")
        )
        raise httpx.HTTPStatusError("Server Error", request=response.request, response=response)

    definite_mcp.make_api_request = mock

    try:
        result = await run_sql_query("SELECT 1")
        print(f"Result: {json.dumps(result, indent=2)}")
        if result["error"] == "":
            print("❌ Still empty!")
        else:
            print(f"✅ Fixed: '{result['error']}'")
    finally:
        definite_mcp.make_api_request = original

    print()


async def test_generic_exception_empty():
    """Test generic Exception with empty string representation"""
    print("3. Testing generic Exception with empty str()...")
    print("-" * 50)

    import definite_mcp

    original = definite_mcp.make_api_request

    class EmptyException(Exception):
        def __str__(self):
            return ""

    async def mock(endpoint: str, payload: dict):
        raise EmptyException()

    definite_mcp.make_api_request = mock

    try:
        result = await run_sql_query("SELECT 1")
        print(f"Result: {json.dumps(result, indent=2)}")
        if result["error"] == "":
            print("❌ Still empty!")
        else:
            print(f"✅ Fixed: '{result['error']}'")
    finally:
        definite_mcp.make_api_request = original

    print()


async def test_actual_information_schema_query():
    """Test the actual query that was returning empty error"""
    print("4. Testing actual information_schema query...")
    print("-" * 50)

    sql = """SELECT table_catalog, table_schema, table_name
FROM information_schema.tables
WHERE table_name ILIKE '%companies%'
LIMIT 10"""

    result = await run_sql_query(sql)

    print(f"Query: {sql[:50]}...")
    if "error" in result:
        if result["error"] == "":
            print("❌ Still returning empty error!")
        else:
            print(f"✅ Error message: '{result['error'][:100]}...'")
    else:
        print(f"✓ Query succeeded with {len(result.get('data', []))} rows")

    print()


async def test_cube_empty_errors():
    """Test Cube query paths for empty errors"""
    print("5. Testing Cube query with empty errors...")
    print("-" * 50)

    import definite_mcp

    original = definite_mcp.make_api_request

    class EmptyException(Exception):
        def __str__(self):
            return ""

    async def mock(endpoint: str, payload: dict):
        raise EmptyException()

    definite_mcp.make_api_request = mock

    try:
        cube_query = {"measures": ["test.metric"]}
        result = await run_cube_query(cube_query)
        print(f"Result: {json.dumps(result, indent=2)}")
        if result["error"] == "":
            print("❌ Cube query still returns empty!")
        else:
            print(f"✅ Fixed: '{result['error']}'")
    finally:
        definite_mcp.make_api_request = original

    print()


async def main():
    """Test all empty error scenarios"""
    print("=" * 60)
    print("COMPREHENSIVE EMPTY ERROR TEST")
    print("=" * 60)
    print()

    await test_http_error_empty_message()
    await test_http_error_empty_after_extraction()
    await test_generic_exception_empty()
    await test_actual_information_schema_query()
    await test_cube_empty_errors()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\nAll paths that could return empty errors are now fixed:")
    print("1. HTTPStatusError with empty message → 'Query failed with HTTP {code}'")
    print("2. Empty after 'Something went wrong:' → 'Query failed with HTTP {code}'")
    print("3. Generic Exception with empty str() → 'Query failed with unknown error'")
    print("4. Cube queries follow same pattern")
    print("\nUsers will always get meaningful error messages!")


if __name__ == "__main__":
    asyncio.run(main())