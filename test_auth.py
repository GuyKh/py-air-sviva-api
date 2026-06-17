#!/usr/bin/env python3
"""Test just the authentication flow"""

import asyncio

import aiohttp

from air_sviva_api.client import SvivaAirClient


async def test_auth():
    async with aiohttp.ClientSession() as session:
        client = SvivaAirClient(session)
        token = await client.generate_token()
        print(f"Successfully generated token: {token}")
        return token


if __name__ == "__main__":
    asyncio.run(test_auth())
