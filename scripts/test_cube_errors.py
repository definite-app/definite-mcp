#!/usr/bin/env python3
"""
Test script for Cube query error handling in the Definite MCP server
"""

import asyncio
import json
import sys
import os

# Add the src directory to Python path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from definite_mcp import run_cube_query


async def test_invalid_measure():
    """Test using a measure that doesn't exist"""
    print("Testing invalid measure...")
    print("-" * 50)

    cube_query = {
        "dimensions": [],
        "filters": [],
        "measures": ["non_existent_cube.fake_measure"],
        "timeDimensions": [],
        "order": [],
        "limit": 10
    }
    result = await run_cube_query(cube_query)

    print(f"Query: {json.dumps(cube_query, indent=2)}")
    print(f"Result:")
    print(json.dumps(result, indent=2))
    print()
    return result


async def test_invalid_dimension():
    """Test using a dimension that doesn't exist"""
    print("Testing invalid dimension...")
    print("-" * 50)

    cube_query = {
        "dimensions": ["fake_cube.non_existent_dimension"],
        "filters": [],
        "measures": [],
        "timeDimensions": [],
        "order": [],
        "limit": 10
    }
    result = await run_cube_query(cube_query)

    print(f"Query: {json.dumps(cube_query, indent=2)}")
    print(f"Result:")
    print(json.dumps(result, indent=2))
    print()
    return result


async def test_invalid_time_dimension():
    """Test using an invalid time dimension"""
    print("Testing invalid time dimension...")
    print("-" * 50)

    cube_query = {
        "dimensions": [],
        "filters": [],
        "measures": ["hubspot_deals.win_rate"],
        "timeDimensions": [{
            "dimension": "fake_cube.non_existent_date",
            "granularity": "month"
        }],
        "order": [],
        "limit": 10
    }
    result = await run_cube_query(cube_query)

    print(f"Query: {json.dumps(cube_query, indent=2)}")
    print(f"Result:")
    print(json.dumps(result, indent=2))
    print()
    return result


async def test_invalid_filter():
    """Test using an invalid filter"""
    print("Testing invalid filter...")
    print("-" * 50)

    cube_query = {
        "dimensions": [],
        "filters": [{
            "member": "fake_cube.non_existent_field",
            "operator": "equals",
            "values": ["test"]
        }],
        "measures": ["hubspot_deals.win_rate"],
        "timeDimensions": [],
        "order": [],
        "limit": 10
    }
    result = await run_cube_query(cube_query)

    print(f"Query: {json.dumps(cube_query, indent=2)}")
    print(f"Result:")
    print(json.dumps(result, indent=2))
    print()
    return result


async def test_malformed_cube_query():
    """Test with a malformed cube query structure"""
    print("Testing malformed cube query...")
    print("-" * 50)

    # Missing required fields or wrong types
    cube_query = {
        "dimensions": "should_be_array",  # Wrong type
        "filters": [],
        "measures": None,  # Should be an array
    }
    result = await run_cube_query(cube_query)

    print(f"Query: {json.dumps(cube_query, indent=2)}")
    print(f"Result:")
    print(json.dumps(result, indent=2))
    print()
    return result


async def test_invalid_granularity():
    """Test using an invalid granularity"""
    print("Testing invalid granularity...")
    print("-" * 50)

    cube_query = {
        "dimensions": [],
        "filters": [],
        "measures": ["hubspot_deals.win_rate"],
        "timeDimensions": [{
            "dimension": "hubspot_deals.close_date",
            "granularity": "invalid_granularity"  # Invalid value
        }],
        "order": [],
        "limit": 10
    }
    result = await run_cube_query(cube_query)

    print(f"Query: {json.dumps(cube_query, indent=2)}")
    print(f"Result:")
    print(json.dumps(result, indent=2))
    print()
    return result


async def main():
    """Run all Cube error tests"""
    print("=" * 50)
    print("CUBE QUERY ERROR HANDLING TESTS")
    print("=" * 50)
    print()

    all_results = []

    try:
        # Run all tests
        all_results.append(("Invalid Measure", await test_invalid_measure()))
        all_results.append(("Invalid Dimension", await test_invalid_dimension()))
        all_results.append(("Invalid Time Dimension", await test_invalid_time_dimension()))
        all_results.append(("Invalid Filter", await test_invalid_filter()))
        all_results.append(("Malformed Query", await test_malformed_cube_query()))
        all_results.append(("Invalid Granularity", await test_invalid_granularity()))

        # Summary
        print("=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)

        for test_name, result in all_results:
            if "error" in result:
                print(f"✓ {test_name}: Error captured successfully")
                # Check if error message is meaningful
                error_msg = result.get("error", "")
                if error_msg and len(error_msg) > 10:
                    # Show first 150 chars of error
                    display_error = error_msg[:150] if len(error_msg) > 150 else error_msg
                    ellipsis = "..." if len(error_msg) > 150 else ""
                    print(f"  → Error message: {display_error}{ellipsis}")
                else:
                    print(f"  ⚠ Warning: Error message might be too generic or empty")
            else:
                print(f"✗ {test_name}: No error returned (unexpected)")
                # Show what was returned instead
                if "data" in result:
                    print(f"  → Got data instead: {len(result.get('data', []))} rows")

        print("\nAll Cube error handling tests completed!")

    except Exception as e:
        print(f"Test suite failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())