import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import cities, weather, air_quality
from database import get_db
from models.schemas import HealthResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

ENV = os.getenv("ENV", "production")

app = FastAPI(
    title="Weather & Air Quality API",
    description=(
        "API agregujące dane pogodowe z Open-Meteo "
        "oraz jakość powietrza z GIOŚ dla polskich miast."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(cities.router, prefix="/api/v1")
app.include_router(weather.router, prefix="/api/v1")
app.include_router(air_quality.router, prefix="/api/v1")


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health_check():
    """Sprawdza stan aplikacji i połączenie z bazą danych."""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        db_status = "ok"
    except Exception as e:
        logger.error("DB health check failed: %s", e)
        db_status = "error"
    return HealthResponse(status="ok", database=db_status)


@app.get("/", tags=["system"])
def root():
    return {
        "message": "Weather & Air Quality API",
        "docs": "/docs",
        "version": "1.0.0",
    }
