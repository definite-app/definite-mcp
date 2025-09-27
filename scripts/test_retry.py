#!/usr/bin/env python3
"""
Test script to verify the retry logic for connection timeouts
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module
import src.definite_mcp as mcp_module

# Make sure API key is set
if not os.environ.get("DEFINITE_API_KEY"):
    print("Please set DEFINITE_API_KEY environment variable")
    sys.exit(1)

async def test_retry():
    print("Testing retry logic with non-routable IP address...")
    print("This should trigger 3 connection attempts with 1s timeout each, then final 30s timeout")
    print("Expected: 3 quick failures (1s each) with exponential backoff, then a longer wait")
    print("---")

    # Save original URL
    original_url = mcp_module.API_BASE_URL

    # Set non-routable IP to force connection timeout
    mcp_module.API_BASE_URL = "http://192.0.2.1"  # Non-routable IP per RFC 5737

    try:
        result = await mcp_module.make_api_request("query", {"sql": "SELECT 1 as test"})
        print(f"Unexpected success: {result}")
    except Exception as e:
        print(f"\nFinal error (as expected): {type(e).__name__}: {str(e)[:100]}...")

    # Restore original URL
    mcp_module.API_BASE_URL = original_url
    print("\n---")
    print("Test completed. The retry logic should have shown 3 connection timeout messages.")

    # Now test with a working connection
    print("\n---")
    print("Testing with working connection...")
    try:
        result = await mcp_module.make_api_request("query", {"sql": "SELECT 1 as test"})
        print(f"Success (as expected): Got {len(result.get('data', []))} row(s)")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_retry())