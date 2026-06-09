import logging
from db import get_cities, upsert_weather, upsert_air_quality
from weather_fetcher import fetch_current_weather
from air_quality_fetcher import fetch_air_quality_for_city, fetch_air_quality_history_for_city
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
 
 
def run_weather_ingestion():
    cities = get_cities()
    logger.info("Starting weather ingestion for %d cities", len(cities))
    ok, fail = 0, 0
    for city in cities:
        data = fetch_current_weather(city["lat"], city["lon"])
        if data and data.get("recorded_at"):
            try:
                upsert_weather(city["id"], data["recorded_at"], data)
                ok += 1
                logger.info("Weather OK: %s @ %s (%.1f°C)", city["name"], data["recorded_at"], data.get("temperature") or 0)
            except Exception as e:
                logger.error("DB error weather %s: %s", city["name"], e)
                fail += 1
        else:
            logger.warning("No weather data for %s", city["name"])
            fail += 1
    logger.info("Weather ingestion done: %d ok, %d failed", ok, fail)
 
 
def run_air_quality_ingestion():
    cities = get_cities()
    logger.info("Starting air quality ingestion for %d cities", len(cities))
    ok, fail = 0, 0
    for city in cities:
        readings = fetch_air_quality_for_city(city["name"])
        for r in readings:
            try:
                upsert_air_quality(city["id"], r["station_id"], r["station_name"], r["recorded_at"], r)
                ok += 1
                logger.info("Air OK: %s / %s @ %s", city["name"], r["station_name"], r["recorded_at"])
            except Exception as e:
                logger.error("DB error air %s: %s", city["name"], e)
                fail += 1
        if not readings:
            logger.warning("No air quality data for %s", city["name"])
    logger.info("Air quality ingestion done: %d ok, %d failed", ok, fail)
 
 
def run_air_quality_history_backfill():
    """Pobierz pełną historię (~72h) z GIOŚ przy starcie systemu."""
    cities = get_cities()
    logger.info("Backfilling air quality history from GIOS for %d cities", len(cities))
    for city in cities:
        logger.info("Backfilling: %s...", city["name"])
        readings = fetch_air_quality_history_for_city(city["name"])
        ok = 0
        for r in readings:
            try:
                upsert_air_quality(city["id"], r["station_id"], r["station_name"], r["recorded_at"], r)
                ok += 1
            except Exception as e:
                logger.error("DB error air history %s: %s", city["name"], e)
        logger.info("  -> %s: %d rekordów", city["name"], ok)
 
 
if __name__ == "__main__":
    run_weather_ingestion()
    run_air_quality_ingestion()