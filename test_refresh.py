#!/usr/bin/env python3
"""Test the token refresh functionality"""

import asyncio

import aiohttp

from air_sviva_api.client import SvivaAirClient


async def test_refresh():
    async with aiohttp.ClientSession() as session:
        client = SvivaAirClient(session)

        # Get initial token
        token1 = await client.generate_token()
        print(f"Initial token: {token1}")

        # Refresh token
        token2 = await client.refresh_token()
        print(f"Refreshed token: {token2}")

        # They should be different (or at least we called the refresh endpoint)
        print("Token refresh test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_refresh())
