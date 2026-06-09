from weather_fetcher import fetch_hourly_history
from db import get_cities, upsert_weather
from datetime import date, timedelta

cities = get_cities()
start = (date.today() - timedelta(days=7)).isoformat()
end = date.today().isoformat()

print(f"Filling data from {start} to {end}")
for city in cities:
    print(f"Filling {city['name']}")
    data = fetch_hourly_history(city['lat'], city['lon'], start, end)
    for row in data:
        if row.get('recorded_at'):
            upsert_weather(city['id'], row['recorded_at'], row)
    print(f"  -> {len(data)} rekordow wczytano")
print("Gotowe!")