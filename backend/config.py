"""Zentrale Konfiguration für Oma-Zeitung."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))

DATABASE_PATH = str(BASE_DIR / os.getenv("DATABASE_PATH", "data/omazeitung.db"))

FRONTEND_DIR = str(BASE_DIR / "frontend")

# --- RSS-Feeds für die Nachrichten-Rubriken ---
# Hinweis: RSS-URLs ändern sich gelegentlich. Bitte bei Problemen auf den
# jeweiligen Webseiten nach "RSS" suchen und hier aktualisieren.
NEWS_FEEDS = {
    "lokal": [
        # NDR Schleswig-Holstein
        "https://www.ndr.de/nachrichten/schleswig-holstein/index-rss.xml",
        # shz.de (Flensburg/Schleswig-Holstein)
        "https://www.shz.de/lokales/flensburg/rss",
    ],
    "welt": [
        # tagesschau.de - Startseite / Übersicht
        "https://www.tagesschau.de/xml/rss2/",
    ],
}

# Google-News-RSS-Suche für Tennis (kein API-Key nötig)
SPORT_FEEDS = [
    "https://news.google.com/rss/search?q=Tennis+ATP+OR+WTA+when:2d&hl=de&gl=DE&ceid=DE:de",
]

MAX_ARTICLES_PER_CATEGORY = 6
MAX_ARTICLES_SPORT = 5

# --- Wetter (Open-Meteo, kein API-Key nötig) ---
WEATHER_LOCATION_NAME = "Flensburg"
WEATHER_LAT = 54.7937
WEATHER_LON = 9.4464

# --- Historischer Rückblick ---
HISTORY_YEARS_AGO_MIN = 10
HISTORY_YEARS_AGO_MAX = 200
