#!/usr/bin/env python3
"""
Improved httpx usage patterns for MCP
"""

import httpx
import asyncio
from typing import Dict, Any, Optional
import os
import json

# BETTER: Global client instance with connection pooling
# This reuses connections and is more efficient
class APIClient:
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.api_key = os.getenv("DEFINITE_API_KEY")
        self.base_url = os.getenv("DEFINITE_API_BASE_URL", "https://api.definite.app")

    async def _ensure_client(self):
        """Ensure client is initialized with proper configuration"""
        if self.client is None:
            # Better timeout configuration
            timeout = httpx.Timeout(
                timeout=120.0,  # Total timeout
                connect=10.0,   # Connection timeout
                read=120.0,     # Read timeout
                write=10.0,     # Write timeout
                pool=5.0        # Pool timeout
            )

            # Better limits for connection pooling
            limits = httpx.Limits(
                max_keepalive_connections=10,  # Reuse connections
                max_connections=20,             # Total connections
                keepalive_expiry=30.0          # Keep connections alive
            )

            # Create client with retry transport
            transport = httpx.AsyncHTTPTransport(
                retries=3,  # Retry failed requests
                limits=limits
            )

            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=timeout,
                transport=transport,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Connection": "keep-alive"  # Explicit keep-alive
                }
            )

    async def make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request with proper error handling"""
        await self._ensure_client()

        try:
            response = await self.client.post(
                f"/v1/{endpoint}",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as e:
            # More specific timeout handling
            if "connect" in str(e).lower():
                raise Exception("Failed to connect to API server (connection timeout)")
            elif "read" in str(e).lower():
                raise Exception("Query took too long to execute (read timeout)")
            else:
                raise Exception(f"Request timed out: {e}")
        except httpx.ConnectError as e:
            raise Exception(f"Cannot connect to API server: {e}")
        except httpx.HTTPStatusError as e:
            # Re-raise with response details
            raise
        except Exception as e:
            raise Exception(f"API request failed: {e}")

    async def close(self):
        """Clean up client"""
        if self.client:
            await self.client.aclose()
            self.client = None


# ALTERNATIVE: Using connection pooling without global client
async def make_request_with_pooling():
    """Example using explicit connection pooling"""

    # Configure for better connection reuse
    async with httpx.AsyncClient(
        limits=httpx.Limits(
            max_keepalive_connections=10,
            max_connections=20,
        ),
        timeout=httpx.Timeout(120.0),
        http2=True,  # Enable HTTP/2 for better performance
    ) as client:
        # Make multiple requests with the same client
        response = await client.get("https://api.example.com/data")
        return response.json()


# DEBUGGING: How to diagnose connection issues
async def debug_connection_issues():
    """Debug why requests might not get responses"""

    import logging

    # Enable debug logging for httpx
    logging.basicConfig(level=logging.DEBUG)
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.DEBUG)

    async with httpx.AsyncClient() as client:
        try:
            # Test with explicit timeouts
            response = await client.get(
                "https://api.definite.app/health",
                timeout=5.0
            )
            print(f"Connection test: {response.status_code}")
        except httpx.ConnectTimeout:
            print("❌ Connection timeout - server not reachable")
        except httpx.ReadTimeout:
            print("❌ Read timeout - server not responding")
        except httpx.ConnectError as e:
            print(f"❌ Connection error: {e}")
        except Exception as e:
            print(f"❌ Other error: {e}")


# RECOMMENDED PATTERN for MCP
class ImprovedMCPClient:
    """Singleton pattern for MCP httpx client"""
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create the shared client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    timeout=120.0,
                    connect=10.0,
                    read=120.0
                ),
                limits=httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=20
                ),
                headers={
                    "Connection": "keep-alive",
                    "Keep-Alive": "timeout=30"
                }
            )
        return self._client

    async def cleanup(self):
        """Clean up on shutdown"""
        if self._client:
            await self._client.aclose()
            self._client = None


async def main():
    """Test the patterns"""
    print("Testing improved httpx patterns for MCP...")
    print("=" * 60)

    # Test debugging
    print("\n1. Connection debugging:")
    await debug_connection_issues()

    print("\n" + "=" * 60)
    print("Key improvements for MCP:")
    print("✓ Reuse client instances (don't create new for each request)")
    print("✓ Configure proper timeouts (connect vs read vs total)")
    print("✓ Enable connection pooling and keep-alive")
    print("✓ Add retry logic for transient failures")
    print("✓ Better error messages for different failure types")
    print("✓ Consider HTTP/2 for better performance")


if __name__ == "__main__":
    asyncio.run(main())