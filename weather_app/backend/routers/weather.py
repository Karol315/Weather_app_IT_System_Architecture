import logging
from fastapi import APIRouter, HTTPException, Query
from database import get_db
from models.schemas import WeatherReading

router = APIRouter(prefix="/weather", tags=["weather"])
logger = logging.getLogger(__name__)


@router.get("/latest", response_model=list[WeatherReading], summary="Aktualna pogoda dla wszystkich miast")
def get_latest_weather():
    """Zwraca najnowszy odczyt pogody dla każdego miasta."""
    sql = """
        SELECT DISTINCT ON (w.city_id)
            w.id, w.city_id, c.name AS city_name, w.recorded_at,
            w.temperature, w.apparent_temperature, w.humidity,
            w.wind_speed, w.precipitation, w.weather_code
        FROM weather_readings w
        JOIN cities c ON c.id = w.city_id
        ORDER BY w.city_id, w.recorded_at DESC
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    return [dict(r) for r in rows]


@router.get("/{city_id}/latest", response_model=WeatherReading, summary="Aktualna pogoda dla miasta")
def get_city_latest_weather(city_id: int):
    """Zwraca najnowszy odczyt pogody dla wybranego miasta."""
    sql = """
        SELECT w.id, w.city_id, c.name AS city_name, w.recorded_at,
               w.temperature, w.apparent_temperature, w.humidity,
               w.wind_speed, w.precipitation, w.weather_code
        FROM weather_readings w
        JOIN cities c ON c.id = w.city_id
        WHERE w.city_id = %s
        ORDER BY w.recorded_at DESC
        LIMIT 1
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (city_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No weather data for this city")
    return dict(row)


@router.get("/{city_id}/history", response_model=list[WeatherReading], summary="Historia pogody")
def get_city_weather_history(
    city_id: int,
    hours: int = Query(default=24, ge=1, le=168, description="Liczba godzin wstecz"),
):
    """Zwraca historię pogody dla wybranego miasta (domyślnie 24h, max 168h = 7 dni)."""
    sql = """
        SELECT w.id, w.city_id, c.name AS city_name, w.recorded_at,
               w.temperature, w.apparent_temperature, w.humidity,
               w.wind_speed, w.precipitation, w.weather_code
        FROM weather_readings w
        JOIN cities c ON c.id = w.city_id
        WHERE w.city_id = %s
          AND w.recorded_at >= NOW() - INTERVAL '%s hours'
        ORDER BY w.recorded_at ASC
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (city_id, hours))
            rows = cur.fetchall()
    return [dict(r) for r in rows]
