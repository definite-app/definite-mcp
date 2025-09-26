#!/usr/bin/env python3
"""
Test what actually causes empty error strings in the Exception handler
"""

import asyncio
import json
import sys
import os

# Add the src directory to Python path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


async def test_json_decode_error():
    """Test when response.json() fails"""
    print("1. Testing JSON decode error...")
    print("-" * 50)

    import definite_mcp
    import httpx

    original = definite_mcp.make_api_request

    async def mock_bad_json(endpoint: str, payload: dict):
        # Simulate a response that isn't JSON
        class MockResponse:
            status_code = 200

            def raise_for_status(self):
                pass  # 200 is OK

            def json(self):
                # This raises json.JSONDecodeError
                return json.loads("not valid json")

        # Create and return mock response
        response = MockResponse()
        response.raise_for_status()
        return response.json()

    definite_mcp.make_api_request = mock_bad_json

    try:
        from definite_mcp import run_sql_query
        result = await run_sql_query("SELECT 1")
        print(f"Result: {json.dumps(result, indent=2)}")
        print(f"Error message: '{result.get('error', '')}'")
        print(f"Is error empty? {result.get('error', '') == ''}")
    except Exception as e:
        print(f"Unexpected exception: {e}")
    finally:
        definite_mcp.make_api_request = original

    print()


async def test_actual_json_error():
    """Test actual JSONDecodeError to see its string representation"""
    print("2. Testing actual JSONDecodeError string...")
    print("-" * 50)

    try:
        json.loads("not valid json")
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError str(): '{str(e)}'")
        print(f"Is empty? {str(e) == ''}")
        print(f"Length: {len(str(e))}")

    print()


async def test_response_attribute_error():
    """Test when response doesn't have expected attributes"""
    print("3. Testing response attribute errors...")
    print("-" * 50)

    import definite_mcp
    import httpx

    original = definite_mcp.make_api_request

    async def mock_attribute_error(endpoint: str, payload: dict):
        # Return None which will cause AttributeError on .json()
        return None

    definite_mcp.make_api_request = mock_attribute_error

    try:
        from definite_mcp import run_sql_query
        result = await run_sql_query("SELECT 1")
        print(f"Result: {json.dumps(result, indent=2)}")
        print(f"Error message: '{result.get('error', '')}'")
    except Exception as e:
        print(f"Caught exception: {type(e).__name__}: {e}")
    finally:
        definite_mcp.make_api_request = original

    print()


async def test_network_errors():
    """Test various network errors"""
    print("4. Testing network errors that bypass HTTPStatusError...")
    print("-" * 50)

    import definite_mcp
    import httpx

    original = definite_mcp.make_api_request

    # Test various network errors
    network_errors = [
        httpx.ConnectError(""),
        httpx.TimeoutException(""),
        httpx.NetworkError(""),
        httpx.ProtocolError(""),
    ]

    for error in network_errors:
        async def mock_network_error(endpoint: str, payload: dict):
            raise error

        definite_mcp.make_api_request = mock_network_error

        try:
            from definite_mcp import run_sql_query
            result = await run_sql_query("SELECT 1")
            print(f"\n{type(error).__name__}:")
            print(f"  Result error: '{result.get('error', '')}'")
            print(f"  Is 'unknown error'? {result.get('error') == 'Query failed with unknown error'}")
        finally:
            definite_mcp.make_api_request = original


async def main():
    """Run all tests"""
    print("=" * 60)
    print("TESTING ACTUAL ERROR PATHS")
    print("=" * 60)
    print()

    await test_json_decode_error()
    await test_actual_json_error()
    await test_response_attribute_error()
    await test_network_errors()

    print("\n" + "=" * 60)
    print("CONCLUSION")
    print("=" * 60)
    print("\nThe generic Exception handler catches:")
    print("1. JSON decode errors (when response isn't valid JSON)")
    print("2. Network errors that aren't HTTPStatusError")
    print("3. Any other non-HTTP exception from make_api_request")
    print("\nMany of these CAN have empty string representations!")


if __name__ == "__main__":
    asyncio.run(main())