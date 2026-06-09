from locust import HttpUser, task, between


class WeatherAPIUser(HttpUser):
    """Testy wydajnościowe API.
    Uruchomienie: locust -f locustfile.py --host=http://localhost:8000
    """
    wait_time = between(0.5, 2)

    @task(3)
    def get_latest_weather(self):
        self.client.get("/api/v1/weather/latest")

    @task(3)
    def get_latest_air_quality(self):
        self.client.get("/api/v1/air-quality/latest")

    @task(2)
    def get_cities(self):
        self.client.get("/api/v1/cities/")

    @task(2)
    def get_city_weather(self):
        self.client.get("/api/v1/weather/1/latest")

    @task(1)
    def get_weather_history(self):
        self.client.get("/api/v1/weather/1/history?hours=24")

    @task(1)
    def get_air_quality_history(self):
        self.client.get("/api/v1/air-quality/1/history?hours=24")

    @task(1)
    def health_check(self):
        self.client.get("/health")
