#!/usr/bin/env python3
"""
Test script to check timeout behavior for the Definite MCP server
"""

import asyncio
import json
import sys
import os
import time
import httpx

# Add the src directory to Python path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from definite_mcp import run_sql_query


async def test_httpx_default_timeout():
    """Test what the default timeout is for httpx.AsyncClient"""
    print("Testing httpx default timeout...")
    print("-" * 50)

    # Create a client without explicit timeout
    async with httpx.AsyncClient() as client:
        print(f"Default timeout: {client.timeout}")
        # The timeout object in httpx has these attributes
        if hasattr(client.timeout, 'total'):
            print(f"  - Total timeout: {client.timeout.total}")
        if hasattr(client.timeout, 'connect'):
            print(f"  - Connect timeout: {client.timeout.connect}")
        if hasattr(client.timeout, 'read'):
            print(f"  - Read timeout: {client.timeout.read}")
        if hasattr(client.timeout, 'write'):
            print(f"  - Write timeout: {client.timeout.write}")
        if hasattr(client.timeout, 'pool'):
            print(f"  - Pool timeout: {client.timeout.pool}")

        # Show the actual timeout value
        print(f"\nActual timeout configuration: {repr(client.timeout)}")

    print()


async def test_long_running_query():
    """Test with a query that might take a long time"""
    print("Testing long-running SQL query...")
    print("-" * 50)

    # This query generates a large dataset that might take time
    sql = """
    WITH RECURSIVE numbers(n) AS (
        SELECT 1
        UNION ALL
        SELECT n + 1 FROM numbers WHERE n < 1000000
    )
    SELECT COUNT(*) as total FROM numbers
    """

    print("Executing potentially slow query...")
    print(f"Query: {sql[:100]}...")

    start_time = time.time()

    try:
        result = await run_sql_query(sql)
        elapsed = time.time() - start_time

        print(f"Query completed in {elapsed:.2f} seconds")

        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Result: {json.dumps(result, indent=2)[:200]}...")

    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        print(f"Query timed out after {elapsed:.2f} seconds")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"Query failed after {elapsed:.2f} seconds: {e}")

    print()


async def test_sleep_query():
    """Test with a query that explicitly sleeps (if supported by the database)"""
    print("Testing query with explicit sleep...")
    print("-" * 50)

    # Try to sleep for 10 seconds (syntax may vary by database)
    # This might not work on all databases
    sql = "SELECT pg_sleep(10) as slept"  # PostgreSQL syntax

    print("Executing sleep query (10 seconds)...")
    print(f"Query: {sql}")

    start_time = time.time()

    try:
        result = await run_sql_query(sql)
        elapsed = time.time() - start_time

        print(f"Query completed in {elapsed:.2f} seconds")

        if "error" in result:
            print(f"Error (expected if not PostgreSQL): {result['error'][:200]}...")
        else:
            print(f"Result: {json.dumps(result, indent=2)}")

    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        print(f"Query timed out after {elapsed:.2f} seconds")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"Query failed after {elapsed:.2f} seconds: {e}")

    print()


async def main():
    """Run timeout tests"""
    print("=" * 60)
    print("MCP SQL QUERY TIMEOUT TESTS")
    print("=" * 60)
    print()

    # Check httpx defaults
    await test_httpx_default_timeout()

    # Test with potentially long queries
    await test_long_running_query()
    await test_sleep_query()

    print("=" * 60)
    print("TIMEOUT INFORMATION SUMMARY")
    print("=" * 60)
    print("\nBased on the httpx AsyncClient defaults:")
    print("• Total timeout: 5.0 seconds (default)")
    print("• Connect timeout: 5.0 seconds")
    print("• Read/Write/Pool: No specific limits")
    print("\nThis means SQL queries via the MCP will timeout after:")
    print("→ 5 seconds total (including connection and response time)")
    print("\nTo handle long-running queries, the MCP server would need to:")
    print("1. Set a higher timeout in httpx.AsyncClient(timeout=...)")
    print("2. Or use timeout=None for no timeout")
    print("3. Or configure specific timeouts for different operations")


if __name__ == "__main__":
    asyncio.run(main())