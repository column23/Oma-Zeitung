"""SQLite-Speicherung für Oma-Zeitung.

Es gibt genau eine "Ausgabe" (edition) pro Kalendertag. Jede Ausgabe hat
Artikel (Lokal/Welt/Sport), einen Wetter-Schnappschuss, einen historischen
Rückblick und die Tages-Rätsel (Sudoku/Kreuzworträtsel).
"""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from backend.config import DATABASE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS editions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    edition_id INTEGER NOT NULL REFERENCES editions(id) ON DELETE CASCADE,
    category TEXT NOT NULL CHECK (category IN ('lokal', 'welt', 'sport')),
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    source_name TEXT,
    source_url TEXT,
    published_at TEXT,
    order_index INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_articles_edition ON articles(edition_id);

CREATE TABLE IF NOT EXISTS weather_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    edition_id INTEGER UNIQUE NOT NULL REFERENCES editions(id) ON DELETE CASCADE,
    location TEXT NOT NULL,
    temp_current REAL,
    temp_min REAL,
    temp_max REAL,
    weather_code INTEGER,
    description TEXT,
    emoji TEXT,
    wind_speed REAL,
    precipitation_prob INTEGER,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS history_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    edition_id INTEGER UNIQUE NOT NULL REFERENCES editions(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    years_ago INTEGER NOT NULL,
    event_text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS puzzles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    edition_id INTEGER UNIQUE NOT NULL REFERENCES editions(id) ON DELETE CASCADE,
    sudoku_json TEXT,
    crossword_json TEXT
);
"""


def _row_to_dict(row):
    return dict(row) if row is not None else None


@contextmanager
def get_connection():
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def get_or_create_edition(date_str: str) -> int:
    """Liefert die edition_id für ein Datum (YYYY-MM-DD), legt sie ggf. an."""
    with get_connection() as conn:
        cur = conn.execute("SELECT id FROM editions WHERE date = ?", (date_str,))
        row = cur.fetchone()
        if row:
            return row["id"]
        cur = conn.execute("INSERT INTO editions (date) VALUES (?)", (date_str,))
        return cur.lastrowid


def clear_edition_content(edition_id: int):
    """Löscht vorhandene Inhalte einer Ausgabe (für erneuten Lauf am selben Tag)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM articles WHERE edition_id = ?", (edition_id,))
        conn.execute("DELETE FROM weather_snapshots WHERE edition_id = ?", (edition_id,))
        conn.execute("DELETE FROM history_facts WHERE edition_id = ?", (edition_id,))
        conn.execute("DELETE FROM puzzles WHERE edition_id = ?", (edition_id,))


def save_articles(edition_id: int, category: str, articles: list):
    with get_connection() as conn:
        for idx, art in enumerate(articles):
            conn.execute(
                """INSERT INTO articles
                   (edition_id, category, title, summary, source_name, source_url, published_at, order_index)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    edition_id,
                    category,
                    art["title"],
                    art["summary"],
                    art.get("source_name"),
                    art.get("source_url"),
                    art.get("published_at"),
                    idx,
                ),
            )


def save_weather(edition_id: int, weather: dict):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO weather_snapshots
               (edition_id, location, temp_current, temp_min, temp_max, weather_code,
                description, emoji, wind_speed, precipitation_prob)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(edition_id) DO UPDATE SET
                 location=excluded.location, temp_current=excluded.temp_current,
                 temp_min=excluded.temp_min, temp_max=excluded.temp_max,
                 weather_code=excluded.weather_code, description=excluded.description,
                 emoji=excluded.emoji,
                 wind_speed=excluded.wind_speed, precipitation_prob=excluded.precipitation_prob""",
            (
                edition_id,
                weather["location"],
                weather.get("temp_current"),
                weather.get("temp_min"),
                weather.get("temp_max"),
                weather.get("weather_code"),
                weather.get("description"),
                weather.get("emoji"),
                weather.get("wind_speed"),
                weather.get("precipitation_prob"),
            ),
        )


def save_history_fact(edition_id: int, fact: dict):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO history_facts (edition_id, year, years_ago, event_text)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(edition_id) DO UPDATE SET
                 year=excluded.year, years_ago=excluded.years_ago, event_text=excluded.event_text""",
            (edition_id, fact["year"], fact["years_ago"], fact["event_text"]),
        )


def save_puzzles(edition_id: int, sudoku: dict = None, crossword: dict = None):
    with get_connection() as conn:
        cur = conn.execute("SELECT id FROM puzzles WHERE edition_id = ?", (edition_id,))
        row = cur.fetchone()
        sudoku_json = json.dumps(sudoku, ensure_ascii=False) if sudoku is not None else None
        crossword_json = json.dumps(crossword, ensure_ascii=False) if crossword is not None else None
        if row:
            if sudoku_json is not None:
                conn.execute("UPDATE puzzles SET sudoku_json = ? WHERE edition_id = ?", (sudoku_json, edition_id))
            if crossword_json is not None:
                conn.execute("UPDATE puzzles SET crossword_json = ? WHERE edition_id = ?", (crossword_json, edition_id))
        else:
            conn.execute(
                "INSERT INTO puzzles (edition_id, sudoku_json, crossword_json) VALUES (?, ?, ?)",
                (edition_id, sudoku_json, crossword_json),
            )


def get_edition_full(date_str: str) -> dict:
    """Liefert eine komplette Ausgabe (inkl. aller Rubriken) für ein Datum, oder None."""
    with get_connection() as conn:
        edition = _row_to_dict(conn.execute("SELECT * FROM editions WHERE date = ?", (date_str,)).fetchone())
        if not edition:
            return None
        edition_id = edition["id"]

        articles = [
            _row_to_dict(r)
            for r in conn.execute(
                "SELECT * FROM articles WHERE edition_id = ? ORDER BY category, order_index", (edition_id,)
            ).fetchall()
        ]
        weather = _row_to_dict(
            conn.execute("SELECT * FROM weather_snapshots WHERE edition_id = ?", (edition_id,)).fetchone()
        )
        history = _row_to_dict(
            conn.execute("SELECT * FROM history_facts WHERE edition_id = ?", (edition_id,)).fetchone()
        )
        puzzles_row = _row_to_dict(
            conn.execute("SELECT * FROM puzzles WHERE edition_id = ?", (edition_id,)).fetchone()
        )

        puzzles = None
        if puzzles_row:
            puzzles = {
                "sudoku": json.loads(puzzles_row["sudoku_json"]) if puzzles_row["sudoku_json"] else None,
                "crossword": json.loads(puzzles_row["crossword_json"]) if puzzles_row["crossword_json"] else None,
            }

        issue_number = conn.execute(
            "SELECT COUNT(*) AS n FROM editions WHERE date <= ?", (date_str,)
        ).fetchone()["n"]

        return {
            "date": edition["date"],
            "created_at": edition["created_at"],
            "issue_number": issue_number,
            "articles": {
                "lokal": [a for a in articles if a["category"] == "lokal"],
                "welt": [a for a in articles if a["category"] == "welt"],
                "sport": [a for a in articles if a["category"] == "sport"],
            },
            "weather": weather,
            "history": history,
            "puzzles": puzzles,
        }


def get_latest_edition_date() -> str:
    with get_connection() as conn:
        row = conn.execute("SELECT date FROM editions ORDER BY date DESC LIMIT 1").fetchone()
        return row["date"] if row else None


def list_editions(search: str = None) -> list:
    """Liste aller Ausgaben (Datum + Anzahl Artikel), optional gefiltert nach Datumsstring."""
    with get_connection() as conn:
        query = """
            SELECT e.date AS date, e.created_at AS created_at, COUNT(a.id) AS article_count
            FROM editions e
            LEFT JOIN articles a ON a.edition_id = e.id
        """
        params = ()
        if search:
            query += " WHERE e.date LIKE ?"
            params = (f"%{search}%",)
        query += " GROUP BY e.id ORDER BY e.date DESC"
        return [_row_to_dict(r) for r in conn.execute(query, params).fetchall()]
