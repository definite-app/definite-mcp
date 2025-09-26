#!/usr/bin/env python3
"""
Debug script to understand what exception causes "Query failed with unknown error"
"""

import asyncio
import json
import sys
import os

# Add the src directory to Python path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


async def test_attio_query_with_debugging():
    """Run the ATTIO query with enhanced error debugging"""
    print("Testing ATTIO query with detailed exception info...")
    print("-" * 60)

    # Patch the run_sql_query to add more debugging
    import definite_mcp
    import httpx

    original_run = definite_mcp.run_sql_query

    async def debug_run_sql_query(sql: str, integration_id=None):
        """Wrapper with detailed exception logging"""
        payload = {"sql": sql}
        if integration_id:
            payload["integration_id"] = integration_id
        else:
            # Check for default integration
            _TABLE_INTEGRATION_ID = os.getenv("_TABLE_INTEGRATION_ID")
            if _TABLE_INTEGRATION_ID:
                payload["integration_id"] = _TABLE_INTEGRATION_ID

        try:
            result = await definite_mcp.make_api_request("query", payload)
            return result
        except httpx.HTTPStatusError as e:
            print(f"\n🔴 HTTPStatusError caught:")
            print(f"   Status Code: {e.response.status_code}")
            print(f"   Response Text: {e.response.text[:200]}")
            raise
        except Exception as e:
            print(f"\n🔴 Generic Exception caught:")
            print(f"   Exception Type: {type(e).__name__}")
            print(f"   Exception Module: {type(e).__module__}")
            print(f"   Exception str(): '{str(e)}'")
            print(f"   Exception repr(): {repr(e)}")
            print(f"   Has args: {e.args if hasattr(e, 'args') else 'No'}")
            if hasattr(e, '__cause__'):
                print(f"   Cause: {e.__cause__}")
            if hasattr(e, '__context__'):
                print(f"   Context: {e.__context__}")

            # Check if it's an empty string
            if str(e) == "":
                print("   ⚠️  This exception has an EMPTY string representation!")
                print("   This is what causes 'Query failed with unknown error'")

            raise

    # Replace temporarily
    definite_mcp.run_sql_query = debug_run_sql_query

    try:
        sql = """SELECT table_catalog, table_schema, table_name
FROM information_schema.tables
WHERE (table_schema ILIKE '%attio%' OR table_name ILIKE '%attio%')
LIMIT 20"""

        print(f"Query: {sql[:80]}...")
        print("\nExecuting query...")

        result = await original_run(sql)

        print(f"\nResult:")
        print(json.dumps(result, indent=2))

        if result.get("error") == "Query failed with unknown error":
            print("\n⚠️  Got the 'unknown error' - check the exception details above!")

    finally:
        # Restore original
        definite_mcp.run_sql_query = original_run


async def test_various_exceptions():
    """Test different exception types to see which produce empty strings"""
    print("\n\nTesting various exception types...")
    print("-" * 60)

    exceptions_to_test = [
        Exception(""),  # Empty message
        Exception(),    # No message
        ValueError(""), # Empty ValueError
        RuntimeError(""),  # Empty RuntimeError
        OSError(""),    # Empty OSError
    ]

    for exc in exceptions_to_test:
        print(f"\n{type(exc).__name__}:")
        print(f"  str(): '{str(exc)}'")
        print(f"  bool(str()): {bool(str(exc))}")
        print(f"  repr(): {repr(exc)}")


async def main():
    """Run debugging tests"""
    print("=" * 60)
    print("DEBUGGING 'Query failed with unknown error'")
    print("=" * 60)
    print()

    await test_attio_query_with_debugging()
    await test_various_exceptions()

    print("\n" + "=" * 60)
    print("DEBUGGING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())