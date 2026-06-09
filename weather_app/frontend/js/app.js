import { api } from "./api.js";
import { weatherDescription, aqiClass, aqiLabel, formatDateTime, formatValue } from "./utils.js";
 
let cities = [];
let selectedCityId = null;
let weatherChart = null;
let airChart = null;
let currentHoursWeather = 24;
let currentHoursAir = 24;
 
async function init() {
  try {
    cities = await api.getCities();
    renderCityButtons();
    if (cities.length > 0) selectCity(cities[0].id);
  } catch (e) {
    showError("Nie można połączyć się z API. Sprawdź czy backend działa.");
    console.error(e);
  }
}
 
function renderCityButtons() {
  const container = document.getElementById("city-selector");
  container.innerHTML = "";
  cities.forEach(city => {
    const btn = document.createElement("button");
    btn.className = "city-btn";
    btn.textContent = city.name;
    btn.onclick = () => selectCity(city.id);
    btn.dataset.cityId = city.id;
    container.appendChild(btn);
  });
}
 
function selectCity(cityId) {
  selectedCityId = cityId;
  document.querySelectorAll(".city-btn").forEach(btn => {
    btn.classList.toggle("active", Number(btn.dataset.cityId) === cityId);
  });
  loadCityData(cityId);
}
 
async function loadCityData(cityId) {
  showLoading(true);
  clearError();
  try {
    const [weather, air] = await Promise.allSettled([
      api.getCityLatestWeather(cityId),
      api.getCityLatestAirQuality(cityId),
    ]);
    renderWeatherCard(weather.status === "fulfilled" ? weather.value : null);
    renderAirQualityCard(air.status === "fulfilled" ? air.value : null);
    await loadCharts(cityId, currentHoursWeather, currentHoursAir);
  } catch (e) {
    showError("Błąd ładowania danych: " + e.message);
  } finally {
    showLoading(false);
  }
}
 
function renderWeatherCard(w) {
  const el = document.getElementById("weather-card");
  if (!w) {
    el.innerHTML = `<div class="card-title">Pogoda</div><p class="sub-value">Brak danych pogodowych</p>`;
    return;
  }
  el.innerHTML = `
    <div class="card-title">Pogoda — ${w.city_name}</div>
    <div class="big-value">${formatValue(w.temperature, "°C")}</div>
    <div class="sub-value">Odczuwalna: ${formatValue(w.apparent_temperature, "°C")}</div>
    <div class="sub-value">${weatherDescription(w.weather_code)}</div>
    <div class="metrics-grid">
      <div class="metric">
        <div class="metric-label">Wilgotność</div>
        <div class="metric-value">${formatValue(w.humidity, "%", 0)}</div>
      </div>
      <div class="metric">
        <div class="metric-label">Wiatr</div>
        <div class="metric-value">${formatValue(w.wind_speed, " km/h")}</div>
      </div>
      <div class="metric">
        <div class="metric-label">Opady</div>
        <div class="metric-value">${formatValue(w.precipitation, " mm")}</div>
      </div>
    </div>
    <div class="updated-at">Aktualizacja: ${formatDateTime(w.recorded_at)}</div>
  `;
}
 
function renderAirQualityCard(a) {
  const el = document.getElementById("air-card");
  if (!a) {
    el.innerHTML = `<div class="card-title">Jakość powietrza</div><p class="sub-value">Brak danych</p>`;
    return;
  }
  const cls = aqiClass(a.pm10);
  const label = aqiLabel(a.pm10);
  el.innerHTML = `
    <div class="card-title">Jakość powietrza — ${a.city_name}</div>
    <div style="margin-bottom:10px">
      <span class="aqi-badge ${cls}">${label}</span>
    </div>
    <div class="metrics-grid">
      <div class="metric">
        <div class="metric-label">PM10</div>
        <div class="metric-value">${formatValue(a.pm10, " µg/m³")}</div>
      </div>
      <div class="metric">
        <div class="metric-label">PM2.5</div>
        <div class="metric-value">${formatValue(a.pm25, " µg/m³")}</div>
      </div>
      <div class="metric">
        <div class="metric-label">NO₂</div>
        <div class="metric-value">${formatValue(a.no2, " µg/m³")}</div>
      </div>
    </div>
    <div class="station-info">Stacja: ${a.station_name}</div>
    <div class="updated-at">Aktualizacja: ${formatDateTime(a.recorded_at)}</div>
  `;
}
 
async function loadCharts(cityId, hoursWeather, hoursAir) {
  const [wHistory, aHistory] = await Promise.allSettled([
    api.getWeatherHistory(cityId, hoursWeather),
    api.getAirQualityHistory(cityId, hoursAir),
  ]);
 
  if (wHistory.status === "fulfilled") renderWeatherChart(wHistory.value);
  if (aHistory.status === "fulfilled") renderAirChart(aHistory.value);
}
 
// Pogoda: czas w formacie ISO z T, traktuj jako lokalny czas warszawski
function parseWeatherDate(isoStr) {
  // Format: "2026-05-24T14:15" - czas lokalny PL, bez strefy
  return new Date(isoStr);
}
 
// Jakość powietrza: format "2026-05-24 14:00:00" - czas lokalny PL
function parseAirDate(str) {
  // Zamień spację na T żeby JS poprawnie parsował jako lokalny czas
  return new Date(str.replace(" ", "T"));
}
 
function chartLabel(dt, showDate) {
  const time = dt.toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit" });
  if (showDate) {
    const date = dt.toLocaleDateString("pl-PL", { day: "2-digit", month: "2-digit" });
    return date + " " + time;
  }
  return time;
}
 
function renderWeatherChart(rawData) {
  const now = new Date();
  const data = rawData.filter(d => parseWeatherDate(d.recorded_at) <= now);
 
  const ctx = document.getElementById("weather-chart").getContext("2d");
 
  if (data.length === 0) {
    ctx.canvas.parentElement.innerHTML += '<p style="text-align:center;color:#718096;padding:20px">Brak danych historycznych</p>';
    return;
  }
 
  let prevDay = null;
  const labels = data.map(d => {
    const dt = parseWeatherDate(d.recorded_at);
    const day = dt.toLocaleDateString("pl-PL", { day: "2-digit", month: "2-digit" });
    const isNewDay = day !== prevDay && prevDay !== null;
    prevDay = day;
    return chartLabel(dt, isNewDay);
  });
 
  if (weatherChart) weatherChart.destroy();
  weatherChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Temperatura (°C)",
        data: data.map(d => d.temperature),
        borderColor: "#3182ce",
        backgroundColor: "rgba(49,130,206,0.1)",
        fill: true,
        tension: 0.3,
        pointRadius: data.length > 48 ? 0 : 3,
      }, {
        label: "Wilgotność (%)",
        data: data.map(d => d.humidity),
        borderColor: "#38a169",
        backgroundColor: "rgba(56,161,105,0.05)",
        fill: false,
        tension: 0.3,
        pointRadius: data.length > 48 ? 0 : 3,
        yAxisID: "y2",
      }]
    },
    options: {
      responsive: true,
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "top" } },
      scales: {
        y: { title: { display: true, text: "°C" } },
        y2: { position: "right", title: { display: true, text: "%" }, grid: { drawOnChartArea: false } },
      }
    }
  });
}
 
function renderAirChart(rawData) {
  const now = new Date();
  const data = rawData.filter(d => parseAirDate(d.recorded_at) <= now);
 
  const ctx = document.getElementById("air-chart").getContext("2d");
 
  if (data.length === 0) {
    const parent = ctx.canvas.parentElement;
    const existing = parent.querySelector(".no-data-msg");
    if (!existing) {
      const msg = document.createElement("p");
      msg.className = "no-data-msg";
      msg.style = "text-align:center;color:#718096;padding:20px";
      msg.textContent = "Brak danych historycznych — dane będą się pojawiać co godzinę";
      parent.appendChild(msg);
    }
    return;
  }
 
  // Usuń ewentualny komunikat o braku danych
  const existing = ctx.canvas.parentElement.querySelector(".no-data-msg");
  if (existing) existing.remove();
 
  const labels = data.map(d => {
    const dt = parseAirDate(d.recorded_at);
    const dateStr = dt.toLocaleDateString("pl-PL", { day: "2-digit", month: "2-digit" });
    const timeStr = dt.toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit" });
    return dateStr + ', ' + timeStr;
  });
 
  if (airChart) airChart.destroy();
  airChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "PM10 (µg/m³)",
        data: data.map(d => d.pm10),
        backgroundColor: "rgba(229,62,62,0.7)",
      }, {
        label: "PM2.5 (µg/m³)",
        data: data.map(d => d.pm25),
        backgroundColor: "rgba(214,158,46,0.7)",
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: "top" } },
      scales: {
        y: { title: { display: true, text: "µg/m³" } }
      }
    }
  });
}
 
function showLoading(show) {
  const el = document.getElementById("loading");
  if (el) el.style.display = show ? "block" : "none";
}
 
function showError(msg) {
  const el = document.getElementById("error-msg");
  if (el) { el.textContent = msg; el.style.display = "block"; }
}
 
function clearError() {
  const el = document.getElementById("error-msg");
  if (el) el.style.display = "none";
}
 
document.querySelectorAll(".range-btn[data-chart='weather']").forEach(btn => {
  btn.onclick = async () => {
    document.querySelectorAll(".range-btn[data-chart='weather']").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentHoursWeather = Number(btn.dataset.hours);
    if (selectedCityId) {
      const data = await api.getWeatherHistory(selectedCityId, currentHoursWeather);
      renderWeatherChart(data);
    }
  };
});
 
document.querySelectorAll(".range-btn[data-chart='air']").forEach(btn => {
  btn.onclick = async () => {
    document.querySelectorAll(".range-btn[data-chart='air']").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentHoursAir = Number(btn.dataset.hours);
    if (selectedCityId) {
      const data = await api.getAirQualityHistory(selectedCityId, currentHoursAir);
      renderAirChart(data);
    }
  };
});
 
init();