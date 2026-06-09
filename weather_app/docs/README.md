# Weather & Air Quality — Mini-projekt PW MiNI

Automatyczny system pobierania, przetwarzania i prezentacji danych pogodowych
(Open-Meteo) oraz jakości powietrza (GIOŚ) dla 5 polskich miast.

---

## Architektura

```
Open-Meteo API ──┐
                 ├─► Ingestion (Python) ─► PostgreSQL ─► FastAPI ─► HTML/JS
GIOŚ API ────────┘
```

Architektura warstwowa (Data Pipeline):
- **Źródła danych**: Open-Meteo (REST, brak klucza), GIOŚ (REST, PL)
- **Ingestion**: Python + schedule, co 30 minut
- **Baza danych**: PostgreSQL 15
- **Backend**: FastAPI + Pydantic, REST JSON, Swagger pod `/docs`
- **Frontend**: HTML + Vanilla JS + Chart.js, serwowany przez Nginx
- **Środowisko**: Docker + docker-compose (dev / test / prod)

---

## Uzasadnienie wyboru technologii

| Komponent | Technologia | Uzasadnienie |
|-----------|-------------|--------------|
| Ingestion | Python + requests | Prostota, bogata ekosystem HTTP, schedule bez overhead |
| Backend | FastAPI | Automatyczny Swagger, walidacja Pydantic, async-ready, szybki |
| Baza danych | PostgreSQL | ACID, indeksy, DISTINCT ON do latest readings |
| Frontend | HTML + JS + Chart.js | Zero build toolchain, prosta integracja, Chart.js wystarczy |
| Serwer www | Nginx | Proxy do backendu, serwowanie statycznych plików |
| Konteneryzacja | Docker Compose | Izolacja, 3 środowiska (dev/test/prod) |

---

## Uruchomienie

### Produkcja
```bash
docker-compose up --build
```
- Frontend: http://localhost:80
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

### Development (hot reload)
```bash
docker-compose -f docker-compose.dev.yml up --build
```

### Testy
```bash
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

### Testy wydajnościowe (Locust)
```bash
cd backend
pip install locust
locust -f locustfile.py --host=http://localhost:8000
# Otwórz http://localhost:8089
```

---

## Struktura projektu

```
weather_app/
├── docker-compose.yml          # produkcja
├── docker-compose.dev.yml      # development
├── docker-compose.test.yml     # testy
├── db/
│   └── init.sql                # schemat bazy danych
├── ingestion/
│   ├── Dockerfile
│   ├── scheduler.py            # uruchamia ingestion co 30 min
│   ├── ingestion.py            # główna logika ingestion
│   ├── weather_fetcher.py      # Open-Meteo API client
│   ├── air_quality_fetcher.py  # GIOŚ API client
│   ├── db.py                   # zapis do bazy
│   └── tests/
│       └── test_ingestion.py
├── backend/
│   ├── Dockerfile
│   ├── main.py                 # FastAPI app
│   ├── database.py             # połączenie z DB
│   ├── locustfile.py           # testy wydajnościowe
│   ├── models/
│   │   └── schemas.py          # Pydantic models
│   ├── routers/
│   │   ├── cities.py
│   │   ├── weather.py
│   │   └── air_quality.py
│   └── tests/
│       └── test_api.py
├── frontend/
│   ├── nginx.conf
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── app.js
│       ├── api.js
│       └── utils.js
└── docs/
    └── README.md
```

---

## API — endpoints

| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/api/v1/cities/` | Lista miast |
| GET | `/api/v1/cities/{id}` | Dane miasta |
| GET | `/api/v1/weather/latest` | Aktualna pogoda (wszystkie miasta) |
| GET | `/api/v1/weather/{id}/latest` | Aktualna pogoda (miasto) |
| GET | `/api/v1/weather/{id}/history?hours=24` | Historia pogody |
| GET | `/api/v1/air-quality/latest` | Aktualna jakość powietrza |
| GET | `/api/v1/air-quality/{id}/latest` | Jakość powietrza (miasto) |
| GET | `/api/v1/air-quality/{id}/history?hours=24` | Historia jakości powietrza |
| GET | `/health` | Health check |

Pełna dokumentacja Swagger: http://localhost:8000/docs

---

## Model danych

```sql
cities               (id, name, lat, lon)
weather_readings     (id, city_id, recorded_at, temperature, humidity, wind_speed, ...)
air_quality_readings (id, city_id, station_id, recorded_at, pm10, pm25, no2, o3, so2)
```

---

## Uruchamianie testów lokalnie

```bash
# Backend
cd backend
pip install -r requirements.txt
pytest tests/ -v

# Ingestion
cd ingestion
pip install -r requirements.txt
pytest tests/ -v
```
