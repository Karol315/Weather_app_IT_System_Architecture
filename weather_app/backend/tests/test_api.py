import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app

client = TestClient(app)

MOCK_CITIES = [
    {"id": 1, "name": "Warszawa", "lat": 52.2297, "lon": 21.0122},
    {"id": 2, "name": "Kraków", "lat": 50.0647, "lon": 19.9450},
]

MOCK_WEATHER = {
    "id": 1,
    "city_id": 1,
    "city_name": "Warszawa",
    "recorded_at": datetime(2024, 1, 15, 12, 0),
    "temperature": 5.2,
    "apparent_temperature": 2.1,
    "humidity": 78,
    "wind_speed": 12.3,
    "precipitation": 0.0,
    "weather_code": 3,
}

MOCK_AIR = {
    "id": 1,
    "city_id": 1,
    "city_name": "Warszawa",
    "station_id": "1",
    "station_name": "Warszawa-Test",
    "recorded_at": datetime(2024, 1, 15, 12, 0),
    "pm10": 42.5,
    "pm25": 25.1,
    "no2": 30.0,
    "o3": 60.0,
    "so2": 5.0,
}


def make_mock_cursor(rows):
    cur = MagicMock()
    cur.fetchall.return_value = rows
    cur.fetchone.return_value = rows[0] if rows else None
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    return cur


def make_mock_conn(rows):
    cur = make_mock_cursor(rows)
    conn = MagicMock()
    conn.cursor.return_value = cur
    conn.__enter__ = lambda s: s
    conn.__exit__ = MagicMock(return_value=False)
    return conn


class TestHealthEndpoint:
    def test_health_ok(self):
        with patch("main.get_db") as mock_db:
            mock_db.return_value.__enter__ = lambda s: make_mock_conn([])
            mock_db.return_value.__exit__ = MagicMock(return_value=False)
            resp = client.get("/health")
        assert resp.status_code == 200

    def test_root_endpoint(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "docs" in resp.json()


class TestCitiesEndpoints:
    def test_get_cities(self):
        with patch("routers.cities.get_db") as mock_db:
            conn = make_mock_conn(MOCK_CITIES)
            mock_db.return_value.__enter__ = lambda s: conn
            mock_db.return_value.__exit__ = MagicMock(return_value=False)
            resp = client.get("/api/v1/cities/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["name"] == "Warszawa"

    def test_get_city_not_found(self):
        with patch("routers.cities.get_db") as mock_db:
            conn = make_mock_conn([])
            mock_db.return_value.__enter__ = lambda s: conn
            mock_db.return_value.__exit__ = MagicMock(return_value=False)
            resp = client.get("/api/v1/cities/999")
        assert resp.status_code == 404


class TestWeatherEndpoints:
    def test_get_latest_weather(self):
        with patch("routers.weather.get_db") as mock_db:
            conn = make_mock_conn([MOCK_WEATHER])
            mock_db.return_value.__enter__ = lambda s: conn
            mock_db.return_value.__exit__ = MagicMock(return_value=False)
            resp = client.get("/api/v1/weather/latest")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["temperature"] == 5.2

    def test_get_city_latest_weather_not_found(self):
        with patch("routers.weather.get_db") as mock_db:
            conn = make_mock_conn([])
            mock_db.return_value.__enter__ = lambda s: conn
            mock_db.return_value.__exit__ = MagicMock(return_value=False)
            resp = client.get("/api/v1/weather/999/latest")
        assert resp.status_code == 404

    def test_get_weather_history_invalid_hours(self):
        resp = client.get("/api/v1/weather/1/history?hours=999")
        assert resp.status_code == 422

    def test_get_weather_history_valid(self):
        with patch("routers.weather.get_db") as mock_db:
            conn = make_mock_conn([MOCK_WEATHER])
            mock_db.return_value.__enter__ = lambda s: conn
            mock_db.return_value.__exit__ = MagicMock(return_value=False)
            resp = client.get("/api/v1/weather/1/history?hours=24")
        assert resp.status_code == 200


class TestAirQualityEndpoints:
    def test_get_latest_air_quality(self):
        with patch("routers.air_quality.get_db") as mock_db:
            conn = make_mock_conn([MOCK_AIR])
            mock_db.return_value.__enter__ = lambda s: conn
            mock_db.return_value.__exit__ = MagicMock(return_value=False)
            resp = client.get("/api/v1/air-quality/latest")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["pm10"] == 42.5

    def test_get_city_air_quality_not_found(self):
        with patch("routers.air_quality.get_db") as mock_db:
            conn = make_mock_conn([])
            mock_db.return_value.__enter__ = lambda s: conn
            mock_db.return_value.__exit__ = MagicMock(return_value=False)
            resp = client.get("/api/v1/air-quality/999/latest")
        assert resp.status_code == 404
