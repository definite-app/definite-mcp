#!/usr/bin/env python3
"""
Test script to reproduce and handle empty error messages
"""

import asyncio
import json
import sys
import os

# Add the src directory to Python path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from definite_mcp import run_sql_query


async def test_attio_query():
    """Test the specific ATTIO query that returns empty error"""
    print("Testing ATTIO query that might return empty error...")
    print("-" * 50)

    sql = """SELECT COUNT(*) AS company_count
FROM ATTIO.companies"""

    result = await run_sql_query(sql)

    print(f"Query: {sql}")
    print(f"\nResult:")
    print(json.dumps(result, indent=2))

    if "error" in result:
        error_msg = result["error"]
        if error_msg == "":
            print("\n⚠️  Empty error message detected!")
            print("This happens when the API returns a response with an empty 'message' field")
            print(f"HTTP Status: {result.get('http_status', 'N/A')}")
        else:
            print(f"\n✓ Error message: {error_msg}")
    else:
        print("\n✓ Query succeeded")

    return result


async def simulate_empty_error():
    """Simulate what happens when API returns empty message"""
    print("\nSimulating API response with empty message...")
    print("-" * 50)

    import definite_mcp
    import httpx

    original_make_api_request = definite_mcp.make_api_request

    async def mock_empty_error_response(endpoint: str, payload: dict):
        # Simulate an HTTP error with empty message
        response = httpx.Response(
            status_code=400,
            json={"message": ""},  # Empty message
            request=httpx.Request("POST", "http://test.com")
        )
        raise httpx.HTTPStatusError(
            "Bad Request",
            request=response.request,
            response=response
        )

    definite_mcp.make_api_request = mock_empty_error_response

    try:
        sql = "SELECT 1"
        result = await run_sql_query(sql)

        print("Result with empty error message:")
        print(json.dumps(result, indent=2))

        if result.get("error") == "":
            print("\n✓ Confirmed: Empty error message is returned as-is")
            print("This matches the behavior you're seeing")

    finally:
        definite_mcp.make_api_request = original_make_api_request


async def main():
    """Run tests for empty error scenarios"""
    print("=" * 60)
    print("EMPTY ERROR MESSAGE TEST")
    print("=" * 60)
    print()

    # Test the actual ATTIO query
    await test_attio_query()

    # Simulate the empty error scenario
    await simulate_empty_error()

    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("=" * 60)
    print("\nThe empty error occurs when:")
    print("1. The Definite API returns an HTTP error status (400, 500, etc.)")
    print("2. The response JSON contains: {\"message\": \"\"}")
    print("3. The MCP extracts this empty message and returns it as-is")
    print("\nThis could happen when:")
    print("• The database/schema doesn't exist (ATTIO schema not found)")
    print("• Permission issues with empty error details")
    print("• API validation errors without descriptive messages")


if __name__ == "__main__":
    asyncio.run(main())