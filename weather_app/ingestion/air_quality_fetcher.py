import logging
import requests
 
logger = logging.getLogger(__name__)
 
GIOS_BASE = "https://api.gios.gov.pl/pjp-api/v1/rest"
 
PARAM_MAP = {
    "PM10": "pm10", "PM2.5": "pm25",
    "NO2": "no2", "O3": "o3", "SO2": "so2",
}
 
 
def _get(url, **params):
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        logger.error("GIOŚ error %s: %s", url, e)
        return {}
 
 
def fetch_stations() -> list[dict]:
    data = _get(f"{GIOS_BASE}/station/findAll", size=500)
    return data.get("Lista stacji pomiarowych", [])
 
 
def fetch_sensors(station_id: int) -> list[dict]:
    data = _get(f"{GIOS_BASE}/station/sensors/{station_id}")
    return data.get("Lista stanowisk pomiarowych dla podanej stacji", [])
 
 
def fetch_sensor_data(sensor_id: int) -> list[dict]:
    """Zwraca WSZYSTKIE dostępne pomiary dla sensora (GIOŚ trzyma ~72h)."""
    data = _get(f"{GIOS_BASE}/data/getData/{sensor_id}")
    return data.get("Lista danych pomiarowych", [])
 
 
def fetch_air_quality_for_city(city_name: str) -> list[dict]:
    """Pobierz najnowszy odczyt dla miasta (jeden rekord na stację)."""
    stations = fetch_stations()
    city_stations = [s for s in stations if city_name.lower() in s.get("Nazwa miasta", "").lower()]
 
    results = []
    for station in city_stations[:3]:
        sid = station["Identyfikator stacji"]
        sensors = fetch_sensors(sid)
        reading = {
            "station_id": str(sid),
            "station_name": station.get("Nazwa stacji", ""),
            "recorded_at": None,
            "pm10": None, "pm25": None,
            "no2": None, "o3": None, "so2": None,
        }
        for sensor in sensors:
            field = PARAM_MAP.get(sensor.get("Wskaźnik - kod", ""))
            if not field:
                continue
            sensor_id = sensor.get("Identyfikator stanowiska")
            if not sensor_id:
                continue
            values = fetch_sensor_data(sensor_id)
            for v in values:
                if v.get("Wartość") is not None:
                    reading[field] = v["Wartość"]
                    if reading["recorded_at"] is None:
                        reading["recorded_at"] = v["Data"]
                    break
        if reading["recorded_at"]:
            results.append(reading)
    return results
 
 
def fetch_air_quality_history_for_city(city_name: str) -> list[dict]:
    """
    Pobierz CAŁĄ dostępną historię (~72h) dla miasta z GIOŚ.
    Zwraca listę rekordów (jeden na stację+czas).
    """
    stations = fetch_stations()
    city_stations = [s for s in stations if city_name.lower() in s.get("Nazwa miasta", "").lower()]
 
    # Zbieramy dane per timestamp, uśredniamy po stacjach
    by_time: dict[str, dict] = {}
 
    for station in city_stations[:3]:
        sid = station["Identyfikator stacji"]
        sensors = fetch_sensors(sid)
 
        for sensor in sensors:
            field = PARAM_MAP.get(sensor.get("Wskaźnik - kod", ""))
            if not field:
                continue
            sensor_id = sensor.get("Identyfikator stanowiska")
            if not sensor_id:
                continue
            values = fetch_sensor_data(sensor_id)
            for v in values:
                ts = v.get("Data")
                val = v.get("Wartość")
                if not ts or val is None:
                    continue
                if ts not in by_time:
                    by_time[ts] = {
                        "station_id": str(sid),
                        "station_name": station.get("Nazwa stacji", ""),
                        "recorded_at": ts,
                        "pm10": None, "pm25": None,
                        "no2": None, "o3": None, "so2": None,
                    }
                if by_time[ts][field] is None:
                    by_time[ts][field] = val
 
    return sorted(by_time.values(), key=lambda x: x["recorded_at"])