export const WMO_CODES = {
  0: "Bezchmurnie", 1: "Przeważnie pogodnie", 2: "Częściowe zachmurzenie",
  3: "Pochmurno", 45: "Mgła", 48: "Mgła szronowa",
  51: "Mżawka lekka", 53: "Mżawka umiarkowana", 55: "Mżawka gęsta",
  61: "Deszcz lekki", 63: "Deszcz umiarkowany", 65: "Deszcz silny",
  71: "Śnieg lekki", 73: "Śnieg umiarkowany", 75: "Śnieg silny",
  80: "Przelotny deszcz", 81: "Przelotny deszcz umiarkowany", 82: "Przelotny deszcz silny",
  95: "Burza", 96: "Burza z gradem", 99: "Silna burza z gradem",
};

export function weatherDescription(code) {
  return WMO_CODES[code] ?? "Nieznane";
}

export function aqiClass(pm10) {
  if (pm10 === null || pm10 === undefined) return "aqi-unknown";
  if (pm10 <= 20)  return "aqi-good";
  if (pm10 <= 50)  return "aqi-medium";
  return "aqi-bad";
}

export function aqiLabel(pm10) {
  if (pm10 === null || pm10 === undefined) return "Brak danych";
  if (pm10 <= 20)  return "Dobra";
  if (pm10 <= 50)  return "Umiarkowana";
  return "Zła";
}

export function formatDateTime(isoString) {
  if (!isoString) return "—";
  const d = new Date(isoString);
  return d.toLocaleString("pl-PL", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

export function formatValue(val, unit = "", decimals = 1) {
  if (val === null || val === undefined) return "—";
  return `${Number(val).toFixed(decimals)}${unit}`;
}
