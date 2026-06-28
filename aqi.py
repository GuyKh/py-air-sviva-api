import asyncio

import aiohttp

from air_sviva_api.client import SvivaAirClient


async def main():
    async with aiohttp.ClientSession() as session:
        client = SvivaAirClient(session)
        await client.generate_token()
        # API-computed AQI for the station (matches web dashboard)
        aqi = await client.get_station_aqi(82)
        print(f"Station {aqi.station_id} at {aqi.datetime}")
        print(f"Overall AQI index: {aqi.index} ({aqi.description})")
        if aqi.indexes:
            print("\nPer-pollutant breakdown:")
            for idx in aqi.indexes:
                print(f"  {idx.pollutant:>6s}: index={idx.index:>7.1f}  value={idx.value:>7.1f}  {idx.description}")
asyncio.run(main())
