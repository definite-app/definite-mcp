#!/usr/bin/env python3
"""
Test script for SQL error handling in the Definite MCP server
"""

import asyncio
import json
import sys
import os

# Add the src directory to Python path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from definite_mcp import run_sql_query


async def test_division_by_zero():
    """Test division by zero error"""
    print("Testing division by zero...")
    print("-" * 50)

    sql = "SELECT 1/0 as impossible"
    result = await run_sql_query(sql)

    print(f"Query: {sql}")
    print(f"Result:")
    print(json.dumps(result, indent=2))
    print()
    return result


async def test_nonexistent_table():
    """Test selecting from a table that doesn't exist"""
    print("Testing non-existent table...")
    print("-" * 50)

    sql = "SELECT * FROM this_table_definitely_does_not_exist"
    result = await run_sql_query(sql)

    print(f"Query: {sql}")
    print(f"Result:")
    print(json.dumps(result, indent=2))
    print()
    return result


async def test_syntax_error():
    """Test SQL syntax error"""
    print("Testing SQL syntax error...")
    print("-" * 50)

    sql = "SELCT * FORM users WHERE"  # Deliberate typos
    result = await run_sql_query(sql)

    print(f"Query: {sql}")
    print(f"Result:")
    print(json.dumps(result, indent=2))
    print()
    return result


async def test_invalid_function():
    """Test using an invalid SQL function"""
    print("Testing invalid SQL function...")
    print("-" * 50)

    sql = "SELECT INVALID_FUNCTION(1) as result"
    result = await run_sql_query(sql)

    print(f"Query: {sql}")
    print(f"Result:")
    print(json.dumps(result, indent=2))
    print()
    return result


async def test_column_ambiguity():
    """Test column name ambiguity error"""
    print("Testing column ambiguity error...")
    print("-" * 50)

    sql = "SELECT id FROM (SELECT 1 as id) a JOIN (SELECT 2 as id) b ON 1=1"
    result = await run_sql_query(sql)

    print(f"Query: {sql}")
    print(f"Result:")
    print(json.dumps(result, indent=2))
    print()
    return result


async def test_type_mismatch():
    """Test type mismatch error"""
    print("Testing type mismatch error...")
    print("-" * 50)

    sql = "SELECT 'hello' + 42 as bad_math"
    result = await run_sql_query(sql)

    print(f"Query: {sql}")
    print(f"Result:")
    print(json.dumps(result, indent=2))
    print()
    return result


async def main():
    """Run all error tests"""
    print("=" * 50)
    print("SQL ERROR HANDLING TESTS")
    print("=" * 50)
    print()

    all_results = []

    try:
        # Run all tests
        all_results.append(("Division by Zero", await test_division_by_zero()))
        all_results.append(("Non-existent Table", await test_nonexistent_table()))
        all_results.append(("Syntax Error", await test_syntax_error()))
        all_results.append(("Invalid Function", await test_invalid_function()))
        all_results.append(("Column Ambiguity", await test_column_ambiguity()))
        all_results.append(("Type Mismatch", await test_type_mismatch()))

        # Summary
        print("=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)

        for test_name, result in all_results:
            if "error" in result:
                print(f"✓ {test_name}: Error captured successfully")
                # Check if error message is meaningful (not empty or generic)
                error_msg = result.get("error", "")
                if error_msg and len(error_msg) > 10:
                    print(f"  → Error message: {error_msg[:100]}...")
                else:
                    print(f"  ⚠ Warning: Error message might be too generic or empty")
            else:
                print(f"✗ {test_name}: No error returned (unexpected)")

        print("\nAll error handling tests completed!")

    except Exception as e:
        print(f"Test suite failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())