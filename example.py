"""Example usage of py-air-sviva-api.

Run with: python example.py

This will attempt to connect to the real API, so it requires internet access.
"""

import asyncio
import logging
from datetime import date, timedelta

import aiohttp

from air_sviva_api.client import SvivaAirClient

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        client = SvivaAirClient(session)

        # 1. Login - Generate API token (public, no login required)
        token = await client.generate_token()
        print(f"✅ 1. Auth token generated: {token}")

        # 2. Get Region
        regions = await client.get_regions()
        print(f"\n✅ 2. Found {len(regions)} regions")
        for region in regions:
            station_count = len(region.stations) if region.stations else 0
            print(f"   Region: {region.name} (ID: {region.region_id}) - {station_count} stations")

        # 3. Get (first) Station in city: "תל אביב-יפו"
        tel_aviv_stations = []
        for region in regions:
            if region.stations:
                for station in region.stations:
                    if getattr(station, "city", None) == "תל אביב-יפו":
                        tel_aviv_stations.append(station)

        if not tel_aviv_stations:
            print("\n❌ No stations found in תל אביב-יפו")
            return

        selected_station = tel_aviv_stations[0]
        print(f"\n✅ 3. Selected station: {selected_station.name} (ID: {selected_station.station_id})")
        if selected_station.location:
            print(f"   Location: {selected_station.location.latitude}, {selected_station.location.longitude}")
        print(f"   City: {getattr(selected_station, 'city', 'N/A')}")

        # 4. Get all *current* monitored air quality conditions for this station
        print(f"\n✅ 4. Getting current air quality conditions for station {selected_station.station_id}...")
        try:
            # Get latest index for the specific station
            station_index = await client.get_station_index_fast(selected_station.station_id)
            print("   Station index data retrieved")
            if station_index.get("data"):
                print("   Current pollutants monitored:")
                for entry in station_index["data"]:
                    print(f"     {entry.get('pollutant', 'N/A')}: index={entry.get('index', 'N/A')}, "
                          f"value={entry.get('value', 'N/A')} {entry.get('color', '')} "
                          f"({entry.get('description', 'N/A')})")

            # Also get regions latest data to see current readings
            if selected_station.region_id is not None:
                region_data = await client.get_regions_latest_data(
                    [selected_station.region_id], hours_back=4
                )
            else:
                region_data = []
            for rd in region_data:
                if rd.station_id == selected_station.station_id and rd.region_data and rd.region_data.channels:
                    print(f"   Current readings for {selected_station.name}:")
                    for channel in rd.region_data.channels:
                        print(f"     {channel.name}: {channel.value} {channel.units} "
                              f"(status: {channel.status}, valid: {channel.valid})")
        except Exception as e:
            print(f"   Error getting current conditions: {e}")

        # 5. Get (for one of the monitors) Today's value history (hour-value)
        print(f"\n✅ 5. Getting today's value history for station {selected_station.station_id}...")
        try:
            today = date.today()
            # Get average readings for today (hourly values)
            average = await client.get_station_average(selected_station.station_id)
            if average.data:
                print(f"   Hourly readings for {today}:")
                for data_point in average.data[:24]:  # 24 hours
                    print(f"     {data_point.datetime}:")
                    for channel in data_point.channels or []:  # type: ignore[assignment]
                        print(f"       {channel.name}: {channel.value} {channel.units}")
            else:
                print("   No data available for today")
        except Exception as e:
            print(f"   Error getting history: {e}")

        # 6. Add more useful calls that use a specific Station
        print("\n✅ 6. Additional station-specific calls:")

        # 6a. Get station missing days
        try:
            missing_days = await client.get_station_missing_days(selected_station.station_id, days_back=30)
            print(f"   Missing data days (last 30): {len(missing_days)} days")
        except Exception as e:
            print(f"   Error getting missing days: {e}")

        # 6b. Get station images
        try:
            images = await client.get_station_images(selected_station.station_id)
            if images.images:
                print(f"   Station images: {len(images.images)} images available")
                for img in images.images[:2]:
                    print(f"     {img.name} (ID: {img.id})")
            else:
                print("   No images available")
        except Exception as e:
            print(f"   Error getting images: {e}")

        # 6c. Get fast index for the station (already done above, but showing different time range)
        try:
            await client.get_station_index_fast(
                selected_station.station_id,
                from_date=date.today() - timedelta(days=1),
                to_date=date.today()
            )
            print("   Fast index (last 2 days): retrieved")
        except Exception as e:
            print(f"   Error getting fast index: {e}")

        # 6d. Get station terminology
        try:
            terminology = await client.get_station_terminology()
            print(f"   Station terminology: {len(terminology)} entries")
        except Exception as e:
            print(f"   Error getting terminology: {e}")


if __name__ == "__main__":
    asyncio.run(main())
