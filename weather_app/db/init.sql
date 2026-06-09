CREATE TABLE IF NOT EXISTS cities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
 
CREATE TABLE IF NOT EXISTS weather_readings (
    id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
    recorded_at TIMESTAMP NOT NULL,
    temperature DOUBLE PRECISION,
    apparent_temperature DOUBLE PRECISION,
    humidity INTEGER,
    wind_speed DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    weather_code INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(city_id, recorded_at)
);
 
CREATE TABLE IF NOT EXISTS air_quality_readings (
    id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
    station_id VARCHAR(50),
    station_name VARCHAR(200),
    recorded_at TIMESTAMP NOT NULL,
    pm10 DOUBLE PRECISION,
    pm25 DOUBLE PRECISION,
    no2 DOUBLE PRECISION,
    o3 DOUBLE PRECISION,
    so2 DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(station_id, recorded_at)
);
 
CREATE INDEX IF NOT EXISTS idx_weather_city_time ON weather_readings(city_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_air_city_time ON air_quality_readings(city_id, recorded_at DESC);
 
INSERT INTO cities (name, lat, lon) VALUES
    ('Warszawa', 52.2297, 21.0122),
    ('Kraków', 50.0647, 19.9450),
    ('Gdańsk', 54.3520, 18.6466),
    ('Poznań', 52.4064, 16.9252)
ON CONFLICT (name) DO NOTHING;
