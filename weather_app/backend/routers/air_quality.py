import logging
from fastapi import APIRouter, HTTPException, Query
from database import get_db
from models.schemas import AirQualityReading
 
router = APIRouter(prefix="/air-quality", tags=["air-quality"])
logger = logging.getLogger(__name__)
 
 
@router.get("/latest", response_model=list[AirQualityReading], summary="Aktualna jakość powietrza")
def get_latest_air_quality():
    sql = """
        SELECT DISTINCT ON (a.city_id)
            a.id, a.city_id, c.name AS city_name, a.station_id,
            a.station_name, a.recorded_at, a.pm10, a.pm25, a.no2, a.o3, a.so2
        FROM air_quality_readings a
        JOIN cities c ON c.id = a.city_id
        ORDER BY a.city_id, a.recorded_at DESC
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    return [dict(r) for r in rows]
 
 
@router.get("/{city_id}/latest", response_model=AirQualityReading, summary="Aktualna jakość powietrza dla miasta")
def get_city_latest_air_quality(city_id: int):
    sql = """
        SELECT a.id, a.city_id, c.name AS city_name, a.station_id,
               a.station_name, a.recorded_at, a.pm10, a.pm25, a.no2, a.o3, a.so2
        FROM air_quality_readings a
        JOIN cities c ON c.id = a.city_id
        WHERE a.city_id = %s
        ORDER BY a.recorded_at DESC
        LIMIT 1
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (city_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No air quality data for this city")
    return dict(row)
 
 
@router.get("/{city_id}/history", response_model=list[AirQualityReading], summary="Historia jakości powietrza")
def get_city_air_quality_history(
    city_id: int,
    hours: int = Query(default=24, ge=1, le=168, description="Liczba godzin wstecz"),
):
    """
    Zwraca historię jakości powietrza — średnia ze wszystkich stacji w mieście
    agregowana per godzina, posortowana chronologicznie.
    """
    sql = """
        SELECT
            %s AS city_id,
            c.name AS city_name,
            MIN(a.id) AS id,
            'Średnia stacji' AS station_id,
            'Średnia stacji' AS station_name,
            date_trunc('hour', a.recorded_at) AS recorded_at,
            ROUND(AVG(a.pm10)::numeric, 1) AS pm10,
            ROUND(AVG(a.pm25)::numeric, 1) AS pm25,
            ROUND(AVG(a.no2)::numeric, 1) AS no2,
            ROUND(AVG(a.o3)::numeric, 1) AS o3,
            ROUND(AVG(a.so2)::numeric, 1) AS so2
        FROM air_quality_readings a
        JOIN cities c ON c.id = a.city_id
        WHERE a.city_id = %s
          AND a.recorded_at >= NOW() - INTERVAL '%s hours'
        GROUP BY date_trunc('hour', a.recorded_at), c.name
        ORDER BY recorded_at ASC
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (city_id, city_id, hours))
            rows = cur.fetchall()
    return [dict(r) for r in rows]