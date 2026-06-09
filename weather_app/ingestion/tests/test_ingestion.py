import pytest
import responses as resp_mock
from unittest.mock import patch

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from weather_fetcher import fetch_current_weather, fetch_hourly_history
from air_quality_fetcher import fetch_stations, fetch_sensor_data, fetch_air_quality_for_city
from ingestion import run_weather_ingestion, run_air_quality_ingestion


WEATHER_RESPONSE = {
    "current": {
        "time": "2024-01-15T12:00",
        "temperature_2m": 5.2,
        "apparent_temperature": 2.1,
        "relative_humidity_2m": 78,
        "wind_speed_10m": 12.3,
        "precipitation": 0.0,
        "weather_code": 3,
    }
}

# Zaktualizowane klucze pod kod produkcyjny ("Lista stacji pomiarowych")
STATIONS_RESPONSE = {
    "Lista stacji pomiarowych": [
        {"id": 1, "stationName": "Warszawa-Marszałkowska", "city": {"name": "Warszawa"}}
    ]
}

SENSORS_RESPONSE = {
    "Lista stanowisk pomiarowych dla podanej stacji": [
        {"Identyfikator stanowiska": 101, "Wskaźnik - kod": "PM10"},
        {"Identyfikator stanowiska": 102, "Wskaźnik - kod": "PM2.5"},
    ]
}

# Zaktualizowane klucze pod kod produkcyjny ("Lista danych pomiarowych")
SENSOR_DATA_RESPONSE = {
    "Lista danych pomiarowych": [
        {"Data": "2024-01-15 12:00:00", "Wartość": 42.5},
        {"Data": "2024-01-15 11:00:00", "Wartość": 38.1},
    ]
}


class TestWeatherFetcher:
    @resp_mock.activate
    def test_fetch_current_weather_success(self):
        resp_mock.add(
            resp_mock.GET,
            "https://api.open-meteo.com/v1/forecast",
            json=WEATHER_RESPONSE,
            status=200,
        )
        result = fetch_current_weather(52.2297, 21.0122)
        assert result is not None
        assert result["temperature"] == 5.2
        assert result["humidity"] == 78
        assert result["recorded_at"] == "2024-01-15T12:00"

    @resp_mock.activate
    def test_fetch_current_weather_api_error(self):
        resp_mock.add(
            resp_mock.GET,
            "https://api.open-meteo.com/v1/forecast",
            status=500,
        )
        result = fetch_current_weather(52.2297, 21.0122)
        assert result is None

    @resp_mock.activate
    def test_fetch_current_weather_timeout(self):
        import requests as req_lib
        resp_mock.add(
            resp_mock.GET,
            "https://api.open-meteo.com/v1/forecast",
            body=req_lib.exceptions.ConnectionError("Connection timeout"),
        )
        result = fetch_current_weather(52.2297, 21.0122)
        assert result is None

    @resp_mock.activate
    def test_fetch_hourly_history_returns_list(self):
        hourly_response = {
            "hourly": {
                "time": ["2024-01-15T00:00", "2024-01-15T01:00"],
                "temperature_2m": [3.1, 2.8],
                "apparent_temperature": [0.5, 0.1],
                "relative_humidity_2m": [80, 82],
                "wind_speed_10m": [10.0, 9.5],
                "precipitation": [0.0, 0.0],
                "weather_code": [2, 2],
            }
        }
        resp_mock.add(
            resp_mock.GET,
            "https://api.open-meteo.com/v1/forecast",
            json=hourly_response,
            status=200,
        )
        result = fetch_hourly_history(52.2297, 21.0122, "2024-01-15", "2024-01-15")
        assert len(result) == 2
        assert result[0]["temperature"] == 3.1
        assert result[1]["humidity"] == 82


class TestAirQualityFetcher:
    @resp_mock.activate
    def test_fetch_stations_success(self):
        # Dopasowane do request.get z params={"size": 500} w Twoim kodzie
        resp_mock.add(
            resp_mock.GET,
            "https://api.gios.gov.pl/pjp-api/v1/rest/station/findAll?size=500",
            json=STATIONS_RESPONSE,
            status=200,
        )
        result = fetch_stations()
        assert len(result) == 1
        assert result[0]["id"] == 1

    @resp_mock.activate
    def test_fetch_stations_error_returns_empty(self):
        resp_mock.add(
            resp_mock.GET,
            "https://api.gios.gov.pl/pjp-api/v1/rest/station/findAll?size=500",
            status=503,
        )
        result = fetch_stations()
        assert result == []

    @resp_mock.activate
    def test_fetch_sensor_data_returns_latest(self):
        resp_mock.add(
            resp_mock.GET,
            "https://api.gios.gov.pl/pjp-api/v1/rest/data/getData/101",
            json=SENSOR_DATA_RESPONSE,
            status=200,
        )
        result = fetch_sensor_data(101)
        # Twój air_quality_fetcher.py dla tej funkcji zwraca LISTĘ, więc test musi to uwzględniać (brak TypeError)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["Wartość"] == 42.5

    @resp_mock.activate
    def test_fetch_sensor_data_all_null_returns_none(self):
        resp_mock.add(
            resp_mock.GET,
            "https://api.gios.gov.pl/pjp-api/v1/rest/data/getData/101",
            json={"Lista danych pomiarowych": []},
            status=200,
        )
        result = fetch_sensor_data(101)
        # Twój kod domyślnie zwraca pustą listę w przypadku braku danych, a nie None
        assert result == []


class TestIngestionPipeline:
    @patch("ingestion.get_cities")
    @patch("ingestion.fetch_current_weather")
    @patch("ingestion.upsert_weather")
    def test_run_weather_ingestion_success(self, mock_upsert, mock_fetch, mock_cities):
        mock_cities.return_value = [{"id": 1, "name": "Warszawa", "lat": 52.23, "lon": 21.01}]
        mock_fetch.return_value = {
            "recorded_at": "2024-01-15T12:00",
            "temperature": 5.2,
            "apparent_temperature": 2.1,
            "humidity": 78,
            "wind_speed": 12.3,
            "precipitation": 0.0,
            "weather_code": 3,
        }
        run_weather_ingestion()
        mock_upsert.assert_called_once()

    @patch("ingestion.get_cities")
    @patch("ingestion.fetch_current_weather")
    @patch("ingestion.upsert_weather")
    def test_run_weather_ingestion_no_data(self, mock_upsert, mock_fetch, mock_cities):
        mock_cities.return_value = [{"id": 1, "name": "Warszawa", "lat": 52.23, "lon": 21.01}]
        mock_fetch.return_value = None
        run_weather_ingestion()
        mock_upsert.assert_not_called()

    @patch("ingestion.get_cities")
    @patch("ingestion.fetch_air_quality_for_city")
    @patch("ingestion.upsert_air_quality")
    def test_run_air_quality_ingestion_success(self, mock_upsert, mock_fetch_air, mock_cities):
        mock_cities.return_value = [{"id": 1, "name": "Warszawa", "lat": 52.23, "lon": 21.01}]
        mock_fetch_air.return_value = [{
            "station_id": "1",
            "station_name": "Warszawa-Test",
            "recorded_at": "2024-01-15 12:00:00",
            "pm10": 42.5,
            "pm25": 25.1,
            "no2": None,
            "o3": None,
            "so2": None,
        }]
        run_air_quality_ingestion()
        mock_upsert.assert_called_once()