"""Wetter-Modul für Flensburg über die kostenlose Open-Meteo API (kein API-Key nötig)."""
import logging

import requests

from backend.config import WEATHER_LAT, WEATHER_LOCATION_NAME, WEATHER_LON

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# WMO Weather interpretation codes -> deutsche Kurzbeschreibung + Emoji fürs Frontend
WEATHER_CODES = {
    0: ("Klarer Himmel", "☀️"),
    1: ("Überwiegend sonnig", "🌤️"),
    2: ("Teilweise bewölkt", "⛅"),
    3: ("Bedeckt", "☁️"),
    45: ("Nebel", "🌫️"),
    48: ("Reifnebel", "🌫️"),
    51: ("Leichter Nieselregen", "🌦️"),
    53: ("Nieselregen", "🌦️"),
    55: ("Starker Nieselregen", "🌧️"),
    56: ("Gefrierender Nieselregen", "🌧️"),
    57: ("Starker gefrierender Nieselregen", "🌧️"),
    61: ("Leichter Regen", "🌦️"),
    63: ("Regen", "🌧️"),
    65: ("Starker Regen", "🌧️"),
    66: ("Gefrierender Regen", "🌨️"),
    67: ("Starker gefrierender Regen", "🌨️"),
    71: ("Leichter Schneefall", "🌨️"),
    73: ("Schneefall", "❄️"),
    75: ("Starker Schneefall", "❄️"),
    77: ("Schneegriesel", "❄️"),
    80: ("Leichte Regenschauer", "🌦️"),
    81: ("Regenschauer", "🌧️"),
    82: ("Heftige Regenschauer", "⛈️"),
    85: ("Leichte Schneeschauer", "🌨️"),
    86: ("Starke Schneeschauer", "❄️"),
    95: ("Gewitter", "⛈️"),
    96: ("Gewitter mit leichtem Hagel", "⛈️"),
    99: ("Gewitter mit starkem Hagel", "⛈️"),
}


def describe_weather_code(code: int) -> tuple:
    return WEATHER_CODES.get(code, ("Unbekannt", "🌡️"))


def fetch_weather() -> dict:
    """Holt aktuelle Temperatur + Tagesvorhersage für Flensburg."""
    params = {
        "latitude": WEATHER_LAT,
        "longitude": WEATHER_LON,
        "current": "temperature_2m,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
        "timezone": "Europe/Berlin",
    }
    try:
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current", {})
        daily = data.get("daily", {})

        code = current.get("weather_code")
        description, emoji = describe_weather_code(code)

        return {
            "location": WEATHER_LOCATION_NAME,
            "temp_current": current.get("temperature_2m"),
            "temp_min": (daily.get("temperature_2m_min") or [None])[0],
            "temp_max": (daily.get("temperature_2m_max") or [None])[0],
            "weather_code": code,
            "description": description,
            "emoji": emoji,
            "wind_speed": current.get("wind_speed_10m"),
            "precipitation_prob": (daily.get("precipitation_probability_max") or [None])[0],
        }
    except Exception:
        logger.exception("Fehler beim Abrufen der Wetterdaten")
        return {
            "location": WEATHER_LOCATION_NAME,
            "temp_current": None,
            "temp_min": None,
            "temp_max": None,
            "weather_code": None,
            "description": "Wetterdaten nicht verfügbar",
            "emoji": "🌡️",
            "wind_speed": None,
            "precipitation_prob": None,
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(fetch_weather())
