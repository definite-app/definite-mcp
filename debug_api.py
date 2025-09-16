#!/usr/bin/env python3
"""
Debug script to test the Definite API directly
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DEFINITE_API_KEY")
print(f"API Key loaded: {API_KEY[:10]}..." if API_KEY else "No API key found")

async def test_api():
    """Test the API directly"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {"sql": "SELECT 1 as test"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.definite.app/v1/query",
                json=payload,
                headers=headers
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_api())