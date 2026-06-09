import schedule
import time
import logging
from ingestion import run_weather_ingestion, run_air_quality_ingestion, run_air_quality_history_backfill
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
 
 
def run_all():
    logger.info("=== Scheduled ingestion run ===")
    run_weather_ingestion()
    run_air_quality_ingestion()
 
 
schedule.every(30).minutes.do(run_all)
 
if __name__ == "__main__":
    logger.info("Scheduler starting — backfilling air quality history from GIOS...")
    run_air_quality_history_backfill()
    logger.info("First weather + air run now")
    run_all()
    while True:
        schedule.run_pending()
        time.sleep(60)
 
