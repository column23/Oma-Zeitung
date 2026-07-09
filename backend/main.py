"""Orchestrator: erzeugt die komplette Tagesausgabe der Oma-Zeitung.

Wird typischerweise einmal morgens per Cronjob aufgerufen (siehe README.md).
"""
import logging
from datetime import date

from backend import db
from backend.export_static import export_edition
from backend.fetch_history import fetch_history_fact
from backend.fetch_news import fetch_and_summarize_all
from backend.fetch_sport import fetch_and_summarize_sport
from backend.fetch_weather import fetch_weather
from backend.games.crossword import generate_crossword
from backend.games.sudoku import generate_sudoku

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def build_edition(target_date: date = None):
    target_date = target_date or date.today()
    date_str = target_date.isoformat()

    logger.info("=== Erzeuge Oma-Zeitung Ausgabe vom %s ===", date_str)

    db.init_db()
    edition_id = db.get_or_create_edition(date_str)
    db.clear_edition_content(edition_id)

    logger.info("Schritt 1/5: Nachrichten (Lokal/Welt) ...")
    news = fetch_and_summarize_all()
    db.save_articles(edition_id, "lokal", news.get("lokal", []))
    db.save_articles(edition_id, "welt", news.get("welt", []))

    logger.info("Schritt 2/5: Sport (Tennis) ...")
    sport = fetch_and_summarize_sport()
    db.save_articles(edition_id, "sport", sport)

    logger.info("Schritt 3/5: Wetter Flensburg ...")
    weather = fetch_weather()
    db.save_weather(edition_id, weather)

    logger.info("Schritt 4/5: Historischer Rückblick ...")
    history = fetch_history_fact(target_date)
    db.save_history_fact(edition_id, history)

    logger.info("Schritt 5/5: Rätsel (Sudoku + Kreuzworträtsel) ...")
    sudoku = generate_sudoku(difficulty="medium")
    all_news_for_crossword = news.get("lokal", []) + news.get("welt", [])
    crossword = generate_crossword(all_news_for_crossword, num_words=10)
    db.save_puzzles(edition_id, sudoku=sudoku, crossword=crossword)

    logger.info("Exportiere statische JSON-Dateien fürs Frontend ...")
    export_edition(date_str)

    logger.info("=== Ausgabe vom %s fertig gespeichert ===", date_str)
    return date_str


if __name__ == "__main__":
    build_edition()
