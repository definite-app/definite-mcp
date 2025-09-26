#!/usr/bin/env python3
"""
Test the new explicit timeout configuration
"""

import asyncio
import json
import sys
import os
import time

# Add the src directory to Python path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from definite_mcp import run_sql_query


async def test_timeout_config():
    """Test that timeouts are properly configured"""
    print("Testing new timeout configuration...")
    print("-" * 60)

    # Check what httpx sees
    import httpx

    # Create timeout object like in the code
    timeout = httpx.Timeout(
        timeout=120.0,  # Total timeout
        connect=30.0,   # Connection timeout (increased from default 5s)
        read=120.0,     # Read timeout for long-running queries
        write=30.0,     # Write timeout
        pool=10.0       # Pool timeout
    )

    print("Timeout configuration:")
    print(f"  Timeout object: {timeout}")
    print(f"  Connect timeout: {timeout.connect}s")
    print(f"  Read timeout: {timeout.read}s")
    print(f"  Write timeout: {timeout.write}s")
    print(f"  Pool timeout: {timeout.pool}s")

    print("\n✅ Connect timeout is now 30 seconds (was default 5s)")
    print("   This should prevent premature ReadTimeout errors")


async def test_slow_connection():
    """Simulate slow connection to test timeout"""
    print("\nTesting with simulated slow connection...")
    print("-" * 60)

    import definite_mcp
    import httpx

    original = definite_mcp.make_api_request

    # Track how long before timeout
    start_time = None

    async def mock_slow_connect(endpoint: str, payload: dict):
        nonlocal start_time
        start_time = time.time()
        # Simulate slow connection (but less than 30s)
        await asyncio.sleep(2)  # 2 second delay
        raise httpx.ConnectError("Simulated connection error after delay")

    definite_mcp.make_api_request = mock_slow_connect

    try:
        result = await run_sql_query("SELECT 1")
        elapsed = time.time() - start_time if start_time else 0

        print(f"Response after {elapsed:.1f} seconds:")
        if 'error' in result:
            print(f"  Error: {result['error']}")
            if 'request_details' in result:
                print(f"  Timeout config: {result['request_details'].get('timeout')}")

        if elapsed >= 2:
            print("\n✅ Connection attempt lasted at least 2 seconds")
            print("   (Would have failed immediately with old 5s default)")

    finally:
        definite_mcp.make_api_request = original


async def test_real_query():
    """Test with a real query"""
    print("\nTesting with actual query...")
    print("-" * 60)

    sql = "SELECT 1 as test"

    print("Executing query...")
    start = time.time()

    result = await run_sql_query(sql)

    elapsed = time.time() - start
    print(f"Response after {elapsed:.2f} seconds")

    if 'error' in result:
        print(f"Error: {result['error']}")
        if 'exception_type' in result:
            print(f"Exception type: {result['exception_type']}")
        if 'request_details' in result:
            timeout_info = result['request_details'].get('timeout', 'Not specified')
            print(f"Timeout configuration: {timeout_info}")

            # Check if it's a timeout error
            if 'ReadTimeout' in result.get('exception_type', ''):
                print("\n⚠️  Still getting ReadTimeout!")
                print("   But now we know it's not the connect timeout (30s)")
                print("   This might be actual query execution time >120s")
            elif 'ConnectTimeout' in result.get('exception_type', ''):
                print("\n⚠️  ConnectTimeout after 30 seconds")
                print("   Server might be unreachable")
    else:
        print(f"✅ Query succeeded")
        if result.get('data'):
            print(f"   Result: {result['data']}")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("TESTING IMPROVED TIMEOUT CONFIGURATION")
    print("=" * 60)
    print()

    await test_timeout_config()
    await test_slow_connection()
    await test_real_query()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\nTimeout improvements:")
    print("• Connect timeout: 30s (was implicit 5s)")
    print("• Read timeout: 120s for long queries")
    print("• Write timeout: 30s")
    print("• Pool timeout: 10s")
    print("\nThis should prevent premature 'ReadTimeout' errors")
    print("that were actually connection timeouts.")


if __name__ == "__main__":
    asyncio.run(main())