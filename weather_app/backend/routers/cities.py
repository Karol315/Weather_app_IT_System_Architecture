import logging
from fastapi import APIRouter, HTTPException
from database import get_db
from models.schemas import City

router = APIRouter(prefix="/cities", tags=["cities"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=list[City], summary="Lista miast")
def get_cities():
    """Zwraca listę wszystkich monitorowanych miast."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, lat, lon FROM cities ORDER BY name")
            rows = cur.fetchall()
    return [dict(r) for r in rows]


@router.get("/{city_id}", response_model=City, summary="Dane miasta")
def get_city(city_id: int):
    """Zwraca dane wybranego miasta."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, lat, lon FROM cities WHERE id = %s", (city_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="City not found")
    return dict(row)
