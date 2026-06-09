import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://weatheruser:weatherpass@localhost:5432/weatherdb")


def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def get_cities():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, lat, lon FROM cities ORDER BY name")
            return cur.fetchall()


def upsert_weather(city_id: int, recorded_at: str, data: dict):
    sql = """
        INSERT INTO weather_readings
            (city_id, recorded_at, temperature, apparent_temperature, humidity,
             wind_speed, precipitation, weather_code)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (city_id, recorded_at) DO UPDATE SET
            temperature = EXCLUDED.temperature,
            apparent_temperature = EXCLUDED.apparent_temperature,
            humidity = EXCLUDED.humidity,
            wind_speed = EXCLUDED.wind_speed,
            precipitation = EXCLUDED.precipitation,
            weather_code = EXCLUDED.weather_code
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                city_id,
                recorded_at,
                data.get("temperature"),
                data.get("apparent_temperature"),
                data.get("humidity"),
                data.get("wind_speed"),
                data.get("precipitation"),
                data.get("weather_code"),
            ))
        conn.commit()


def upsert_air_quality(city_id: int, station_id: str, station_name: str, recorded_at: str, data: dict):
    sql = """
        INSERT INTO air_quality_readings
            (city_id, station_id, station_name, recorded_at, pm10, pm25, no2, o3, so2)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (station_id, recorded_at) DO UPDATE SET
            pm10 = EXCLUDED.pm10,
            pm25 = EXCLUDED.pm25,
            no2 = EXCLUDED.no2,
            o3 = EXCLUDED.o3,
            so2 = EXCLUDED.so2
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                city_id,
                station_id,
                station_name,
                recorded_at,
                data.get("pm10"),
                data.get("pm25"),
                data.get("no2"),
                data.get("o3"),
                data.get("so2"),
            ))
        conn.commit()
