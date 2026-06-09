import logging
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.open-meteo.com/v1/forecast"

PARAMS = (
    "temperature_2m,apparent_temperature,relative_humidity_2m,"
    "wind_speed_10m,precipitation,weather_code"
)


def fetch_current_weather(lat: float, lon: float) -> dict | None:
    """Fetch current weather from Open-Meteo API (no API key required)."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": PARAMS,
        "timezone": "Europe/Warsaw",
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current", {})
        return {
            "recorded_at": current.get("time"),
            "temperature": current.get("temperature_2m"),
            "apparent_temperature": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "precipitation": current.get("precipitation"),
            "weather_code": current.get("weather_code"),
        }
    except requests.RequestException as e:
        logger.error("Open-Meteo fetch error for lat=%s lon=%s: %s", lat, lon, e)
        return None


def fetch_hourly_history(lat: float, lon: float, start_date: str, end_date: str) -> list[dict]:
    """Fetch hourly historical weather data."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": PARAMS,
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "Europe/Warsaw",
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        result = []
        for i, t in enumerate(times):
            result.append({
                "recorded_at": t,
                "temperature": hourly.get("temperature_2m", [None])[i],
                "apparent_temperature": hourly.get("apparent_temperature", [None])[i],
                "humidity": hourly.get("relative_humidity_2m", [None])[i],
                "wind_speed": hourly.get("wind_speed_10m", [None])[i],
                "precipitation": hourly.get("precipitation", [None])[i],
                "weather_code": hourly.get("weather_code", [None])[i],
            })
        return result
    except requests.RequestException as e:
        logger.error("Open-Meteo history error: %s", e)
        return []
