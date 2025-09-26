#!/usr/bin/env python3
"""
Run all tests for the Definite MCP server
"""

import asyncio
import sys
import os

# Add the src directory to Python path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from test_mcp import main as test_basic
from test_sql_errors import main as test_sql_errors
from test_cube_errors import main as test_cube_errors


async def main():
    """Run all test suites"""
    print("=" * 60)
    print("DEFINITE MCP SERVER - COMPLETE TEST SUITE")
    print("=" * 60)
    print()

    all_passed = True

    # Test basic functionality
    print("\n[1/3] Running basic functionality tests...")
    print("-" * 60)
    try:
        await test_basic()
        print("✓ Basic functionality tests passed")
    except Exception as e:
        print(f"✗ Basic functionality tests failed: {e}")
        all_passed = False

    # Test SQL error handling
    print("\n[2/3] Running SQL error handling tests...")
    print("-" * 60)
    try:
        await test_sql_errors()
        print("✓ SQL error handling tests passed")
    except Exception as e:
        print(f"✗ SQL error handling tests failed: {e}")
        all_passed = False

    # Test Cube error handling
    print("\n[3/3] Running Cube error handling tests...")
    print("-" * 60)
    try:
        await test_cube_errors()
        print("✓ Cube error handling tests passed")
    except Exception as e:
        print(f"✗ Cube error handling tests failed: {e}")
        all_passed = False

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)

    if all_passed:
        print("✅ All test suites completed successfully!")
        print("\nThe MCP server is working correctly and returns:")
        print("• Clean, meaningful error messages for SQL errors")
        print("• Clear error messages for Cube query errors")
        print("• Successful results for valid queries")
        sys.exit(0)
    else:
        print("❌ Some test suites failed. Please review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())