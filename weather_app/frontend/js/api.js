const API_BASE = "/api/v1";

async function apiFetch(path) {
  const resp = await fetch(API_BASE + path);
  if (!resp.ok) throw new Error(`API error ${resp.status}: ${path}`);
  return resp.json();
}

export const api = {
  getCities:              () => apiFetch("/cities/"),
  getLatestWeather:       () => apiFetch("/weather/latest"),
  getCityLatestWeather:   (id) => apiFetch(`/weather/${id}/latest`),
  getWeatherHistory:      (id, hours) => apiFetch(`/weather/${id}/history?hours=${hours}`),
  getLatestAirQuality:    () => apiFetch("/air-quality/latest"),
  getCityLatestAirQuality:(id) => apiFetch(`/air-quality/${id}/latest`),
  getAirQualityHistory:   (id, hours) => apiFetch(`/air-quality/${id}/history?hours=${hours}`),
};
