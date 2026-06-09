from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class City(BaseModel):
    id: int
    name: str
    lat: float
    lon: float


class WeatherReading(BaseModel):
    id: int
    city_id: int
    city_name: Optional[str] = None
    recorded_at: datetime
    temperature: Optional[float]
    apparent_temperature: Optional[float]
    humidity: Optional[int]
    wind_speed: Optional[float]
    precipitation: Optional[float]
    weather_code: Optional[int]


class AirQualityReading(BaseModel):
    id: int
    city_id: int
    city_name: Optional[str] = None
    station_id: str
    station_name: str
    recorded_at: datetime
    pm10: Optional[float]
    pm25: Optional[float]
    no2: Optional[float]
    o3: Optional[float]
    so2: Optional[float]


class WeatherSummary(BaseModel):
    city: City
    latest: Optional[WeatherReading]
    air_quality: Optional[AirQualityReading]


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str = "1.0.0"
