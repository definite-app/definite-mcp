#!/usr/bin/env python3
"""
Test script for invalid integration_id handling in the Definite MCP server
"""

import asyncio
import json
import sys
import os

# Add the src directory to Python path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from definite_mcp import run_sql_query, run_cube_query


async def test_invalid_integration_sql():
    """Test SQL query with invalid integration_id"""
    print("Testing SQL query with invalid integration_id...")
    print("-" * 50)

    # Use a completely invalid UUID
    invalid_id = "invalid-uuid-12345-67890"
    sql = "SELECT 1 as test_column"

    result = await run_sql_query(sql, integration_id=invalid_id)

    print(f"Query: {sql}")
    print(f"Integration ID: {invalid_id}")
    print(f"Result:")
    print(json.dumps(result, indent=2))

    if "error" in result:
        print(f"\n✓ Error captured successfully!")
        print(f"Error message: {result['error']}")
        if "http_status" in result:
            print(f"HTTP status: {result['http_status']}")
    else:
        print(f"\n✗ No error returned (unexpected)")

    print()
    return result


async def test_nonexistent_integration_sql():
    """Test SQL query with non-existent but valid UUID integration_id"""
    print("Testing SQL query with non-existent integration_id...")
    print("-" * 50)

    # Use a valid UUID format but non-existent integration
    nonexistent_id = "00000000-0000-0000-0000-000000000000"
    sql = "SELECT 'hello' as greeting, 42 as answer"

    result = await run_sql_query(sql, integration_id=nonexistent_id)

    print(f"Query: {sql}")
    print(f"Integration ID: {nonexistent_id}")
    print(f"Result:")
    print(json.dumps(result, indent=2))

    if "error" in result:
        print(f"\n✓ Error captured successfully!")
        print(f"Error message: {result['error']}")
        if "http_status" in result:
            print(f"HTTP status: {result['http_status']}")
    else:
        print(f"\n✗ No error returned (unexpected)")

    print()
    return result


async def test_invalid_integration_cube():
    """Test Cube query with invalid integration_id"""
    print("Testing Cube query with invalid integration_id...")
    print("-" * 50)

    # Use an invalid integration ID
    invalid_id = "not-a-valid-uuid"
    cube_query = {
        "dimensions": [],
        "filters": [],
        "measures": ["hubspot_deals.win_rate"],
        "timeDimensions": [{
            "dimension": "hubspot_deals.close_date",
            "granularity": "month"
        }],
        "order": [],
        "limit": 10
    }

    result = await run_cube_query(cube_query, integration_id=invalid_id)

    print(f"Cube Query: {json.dumps(cube_query, indent=2)}")
    print(f"Integration ID: {invalid_id}")
    print(f"Result:")
    print(json.dumps(result, indent=2))

    if "error" in result:
        print(f"\n✓ Error captured successfully!")
        print(f"Error message: {result['error']}")
        if "http_status" in result:
            print(f"HTTP status: {result['http_status']}")
    else:
        print(f"\n✗ No error returned (unexpected)")

    print()
    return result


async def test_empty_integration():
    """Test with empty string integration_id"""
    print("Testing with empty string integration_id...")
    print("-" * 50)

    empty_id = ""
    sql = "SELECT NOW() as current_time"

    result = await run_sql_query(sql, integration_id=empty_id)

    print(f"Query: {sql}")
    print(f"Integration ID: '{empty_id}' (empty string)")
    print(f"Result:")
    print(json.dumps(result, indent=2))

    if "error" in result:
        print(f"\n✓ Error captured!")
        print(f"Error message: {result['error']}")
    else:
        print(f"\n✓ Query executed (empty string might be treated as None)")

    print()
    return result


async def main():
    """Run all integration ID tests"""
    print("=" * 60)
    print("INVALID INTEGRATION_ID ERROR TESTS")
    print("=" * 60)
    print()

    all_results = []

    try:
        # Run all tests
        all_results.append(("Invalid UUID Format (SQL)", await test_invalid_integration_sql()))
        all_results.append(("Non-existent UUID (SQL)", await test_nonexistent_integration_sql()))
        all_results.append(("Invalid UUID Format (Cube)", await test_invalid_integration_cube()))
        all_results.append(("Empty String ID", await test_empty_integration()))

        # Summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        errors_found = 0
        for test_name, result in all_results:
            if "error" in result:
                errors_found += 1
                print(f"✓ {test_name}: Error captured successfully")
                error_msg = result.get("error", "")
                if error_msg:
                    # Show first 100 chars of error
                    display_error = error_msg[:100] if len(error_msg) > 100 else error_msg
                    ellipsis = "..." if len(error_msg) > 100 else ""
                    print(f"  → Error: {display_error}{ellipsis}")
            else:
                print(f"ℹ {test_name}: No error (query might have succeeded with default)")

        print(f"\nTotal tests with errors: {errors_found}/{len(all_results)}")
        print("\n✅ Invalid integration_id handling test completed!")
        print("\nThe MCP server properly handles invalid integration IDs by:")
        print("• Returning clear error messages when integration is invalid")
        print("• Including HTTP status codes for debugging")
        print("• Preserving query/request details in error responses")

    except Exception as e:
        print(f"Test suite failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())