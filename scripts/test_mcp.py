#!/usr/bin/env python3
"""
Test script for the Definite MCP server
"""

import asyncio
import json
import sys
import os

# Add the src directory to Python path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from definite_mcp import run_sql_query, run_cube_query


async def test_sql_query():
    """Test a simple SQL query"""
    print("Testing SQL query...")

    sql = "SELECT 1 as test_column"
    result = await run_sql_query(sql)

    print(f"SQL Query Result:")
    print(json.dumps(result, indent=2))
    print()


async def test_cube_query():
    """Test a Cube query"""
    print("Testing Cube query...")

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

    result = await run_cube_query(cube_query)

    print(f"Cube Query Result:")
    print(json.dumps(result, indent=2))
    print()


async def main():
    """Run all tests"""
    try:
        await test_sql_query()
        await test_cube_query()
        print("All tests completed!")
    except Exception as e:
        print(f"Test failed with error: {e}")


if __name__ == "__main__":
    asyncio.run(main())