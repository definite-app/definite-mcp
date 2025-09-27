#!/usr/bin/env python3
"""
Test script to verify the retry logic works with real API endpoint
"""
import asyncio
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module
import src.definite_mcp as mcp_module

# Make sure API key is set
if not os.environ.get("DEFINITE_API_KEY"):
    print("Please set DEFINITE_API_KEY environment variable")
    sys.exit(1)

async def test_real_api():
    print("Testing with real Definite API endpoint...")
    print(f"API URL: {mcp_module.API_BASE_URL}")
    print("=" * 60)

    # Test 1: Simple query
    print("\nTest 1: Simple SELECT query")
    print("-" * 30)
    start_time = time.time()
    try:
        result = await mcp_module.make_api_request("query", {"sql": "SELECT 1 as test"})
        elapsed = time.time() - start_time
        print(f"✅ Success in {elapsed:.2f}s")
        print(f"   Result: {result.get('data', [])}")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Failed in {elapsed:.2f}s: {type(e).__name__}: {str(e)[:100]}")

    # Test 2: Multiple quick queries
    print("\nTest 2: Multiple quick queries (testing connection reuse)")
    print("-" * 30)
    for i in range(3):
        start_time = time.time()
        try:
            result = await mcp_module.make_api_request("query", {"sql": f"SELECT {i+1} as num"})
            elapsed = time.time() - start_time
            print(f"  Query {i+1}: ✅ Success in {elapsed:.2f}s - Result: {result.get('data', [])}")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  Query {i+1}: ❌ Failed in {elapsed:.2f}s: {str(e)[:50]}")

    # Test 3: Query with integration_id if available
    print("\nTest 3: Query with integration_id")
    print("-" * 30)
    integration_id = os.environ.get("_TABLE_INTEGRATION_ID")
    if integration_id:
        print(f"   Using integration_id: {integration_id}")
        start_time = time.time()
        try:
            payload = {
                "sql": "SELECT 'with_integration' as test",
                "integration_id": integration_id
            }
            result = await mcp_module.make_api_request("query", payload)
            elapsed = time.time() - start_time
            print(f"✅ Success in {elapsed:.2f}s")
            print(f"   Result: {result.get('data', [])}")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Failed in {elapsed:.2f}s: {type(e).__name__}: {str(e)[:100]}")
    else:
        print("   No integration_id in environment, skipping")

    print("\n" + "=" * 60)
    print("Testing complete!")
    print("\nNOTE: With the retry logic:")
    print("  • Connection attempts timeout after 1s (first 2 attempts)")
    print("  • Exponential backoff between retries (1s, 2s)")
    print("  • Final attempt uses 30s timeout")
    print("  • Real API calls should succeed immediately on first attempt")

if __name__ == "__main__":
    asyncio.run(test_real_api())