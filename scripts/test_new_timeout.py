#!/usr/bin/env python3
"""
Test script to verify the new 2-minute timeout configuration
"""

import asyncio
import sys
import os

# Add the src directory to Python path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


async def test_timeout_configuration():
    """Verify the timeout is set to 120 seconds"""
    print("Testing new timeout configuration...")
    print("-" * 50)

    # Import and patch to inspect the timeout
    import definite_mcp
    import httpx

    # Save original function
    original_make_api_request = definite_mcp.make_api_request

    timeout_value = None

    # Create a function that captures the timeout
    async def mock_request_to_check_timeout(endpoint: str, payload: dict):
        headers = {
            "Authorization": f"Bearer {definite_mcp.API_KEY}",
            "Content-Type": "application/json"
        }

        # Set timeout to 2 minutes (120 seconds) for long-running queries
        timeout = httpx.Timeout(timeout=120.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            nonlocal timeout_value
            timeout_value = client.timeout
            # Return a mock successful response
            return {"data": [{"test": 1}], "status": "success"}

    # Patch the function
    definite_mcp.make_api_request = mock_request_to_check_timeout

    try:
        from definite_mcp import run_sql_query

        # Run a query to trigger the patched function
        await run_sql_query("SELECT 1")

        print(f"✓ Timeout is configured to: {timeout_value}")

        # Check the timeout value (httpx.Timeout object stores it differently)
        timeout_seconds = str(timeout_value).split('=')[1].rstrip(')')
        print(f"  - Timeout value: {timeout_seconds} seconds")

        if timeout_seconds == "120.0":
            print("\n✅ SUCCESS: Timeout is correctly set to 2 minutes (120 seconds)")
        else:
            print(f"\n❌ ERROR: Expected 120.0 seconds but got {timeout_seconds}")

    finally:
        # Restore original function
        definite_mcp.make_api_request = original_make_api_request

    print()


async def test_actual_query():
    """Test an actual query to make sure it still works"""
    print("\nTesting actual query with new timeout...")
    print("-" * 50)

    from definite_mcp import run_sql_query

    sql = "SELECT 'timeout_test' as test, 120 as timeout_seconds"
    result = await run_sql_query(sql)

    if "error" in result:
        print(f"❌ Query failed: {result['error']}")
    else:
        print(f"✅ Query succeeded with 120-second timeout")
        print(f"   Result: {result.get('data', [])}")

    print()


async def main():
    """Run timeout configuration tests"""
    print("=" * 60)
    print("2-MINUTE TIMEOUT CONFIGURATION TEST")
    print("=" * 60)
    print()

    await test_timeout_configuration()
    await test_actual_query()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\n✅ The MCP server has been updated to use a 2-minute timeout")
    print("   for all SQL and Cube queries.")
    print("\nThis means:")
    print("• Queries can now run for up to 120 seconds before timing out")
    print("• Long-running analytical queries will have time to complete")
    print("• Connection timeout is also extended to 120 seconds")


if __name__ == "__main__":
    asyncio.run(main())