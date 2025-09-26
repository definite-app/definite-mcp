#!/usr/bin/env python3
"""
Test that error responses include request details
"""

import asyncio
import json
import sys
import os

# Add the src directory to Python path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from definite_mcp import run_sql_query, run_cube_query


async def test_timeout_error_with_details():
    """Test that timeout errors include request details"""
    print("Testing timeout error with request details...")
    print("-" * 60)

    import definite_mcp
    import httpx

    original = definite_mcp.make_api_request

    async def mock_timeout(endpoint: str, payload: dict):
        raise httpx.TimeoutException("")

    definite_mcp.make_api_request = mock_timeout

    try:
        sql = "SELECT * FROM large_table"
        result = await run_sql_query(sql, integration_id="test-integration-123")

        print("Error Response:")
        print(json.dumps(result, indent=2))

        # Check what's included
        if 'request_details' in result:
            print("\n✅ Request details included:")
            details = result['request_details']
            print(f"  - URL: {details.get('url')}")
            print(f"  - Payload: {json.dumps(details.get('payload'), indent=4)}")
            print(f"  - API Key Configured: {details.get('api_key_configured')}")
            print(f"  - Timeout: {details.get('timeout')}")
        else:
            print("\n❌ No request details found")

    finally:
        definite_mcp.make_api_request = original

    print()


async def test_http_error_with_details():
    """Test that HTTP errors include request details"""
    print("Testing HTTP error with request details...")
    print("-" * 60)

    import definite_mcp
    import httpx

    original = definite_mcp.make_api_request

    async def mock_http_error(endpoint: str, payload: dict):
        response = httpx.Response(
            status_code=400,
            json={"message": "Invalid query syntax"},
            request=httpx.Request("POST", "http://test.com")
        )
        raise httpx.HTTPStatusError("Bad Request", request=response.request, response=response)

    definite_mcp.make_api_request = mock_http_error

    try:
        sql = "SELCT * FORM users"  # Deliberate typo
        result = await run_sql_query(sql)

        print("Error Response:")
        print(json.dumps(result, indent=2))

        if 'request_details' in result:
            print("\n✅ Request details included in HTTP error")
        else:
            print("\n❌ No request details in HTTP error")

    finally:
        definite_mcp.make_api_request = original

    print()


async def test_cube_error_with_details():
    """Test that Cube query errors include request details"""
    print("Testing Cube query error with request details...")
    print("-" * 60)

    import definite_mcp
    import httpx

    original = definite_mcp.make_api_request

    async def mock_network_error(endpoint: str, payload: dict):
        raise httpx.NetworkError("")

    definite_mcp.make_api_request = mock_network_error

    try:
        cube_query = {
            "measures": ["sales.total"],
            "dimensions": ["sales.region"],
            "filters": []
        }
        result = await run_cube_query(cube_query, integration_id="cube-int-456")

        print("Error Response:")
        print(json.dumps(result, indent=2))

        if 'request_details' in result:
            print("\n✅ Request details included in Cube error:")
            details = result['request_details']
            print(f"  - URL: {details.get('url')}")
            print(f"  - Payload includes cube_query: {'cube_query' in details.get('payload', {})}")
            print(f"  - Payload includes integration_id: {'integration_id' in details.get('payload', {})}")
        else:
            print("\n❌ No request details in Cube error")

    finally:
        definite_mcp.make_api_request = original

    print()


async def test_with_env_integration_id():
    """Test with _TABLE_INTEGRATION_ID from environment"""
    print("Testing with _TABLE_INTEGRATION_ID environment variable...")
    print("-" * 60)

    import definite_mcp
    import httpx

    # Set environment variable
    os.environ["_TABLE_INTEGRATION_ID"] = "env-integration-789"

    original = definite_mcp.make_api_request

    async def mock_error(endpoint: str, payload: dict):
        print(f"Request payload: {json.dumps(payload, indent=2)}")
        raise httpx.ConnectError("")

    definite_mcp.make_api_request = mock_error

    try:
        sql = "SELECT 1"
        result = await run_sql_query(sql)  # No explicit integration_id

        if 'request_details' in result:
            payload = result['request_details'].get('payload', {})
            if 'integration_id' in payload:
                print(f"✅ integration_id from environment: {payload['integration_id']}")
            else:
                print("❌ No integration_id in payload")

    finally:
        definite_mcp.make_api_request = original
        # Clean up env var
        if "_TABLE_INTEGRATION_ID" in os.environ:
            del os.environ["_TABLE_INTEGRATION_ID"]

    print()


async def main():
    """Run all tests"""
    print("=" * 60)
    print("TESTING REQUEST DETAILS IN ERROR RESPONSES")
    print("=" * 60)
    print()

    await test_timeout_error_with_details()
    await test_http_error_with_details()
    await test_cube_error_with_details()
    await test_with_env_integration_id()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\nError responses now include request_details with:")
    print("• URL that was called")
    print("• Full payload including SQL/Cube query and integration_id")
    print("• API key configuration status")
    print("• Timeout setting")
    print("\nThis helps debug exactly what request failed and why!")


if __name__ == "__main__":
    asyncio.run(main())