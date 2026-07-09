"""Exportiert die in der Datenbank gespeicherten Ausgaben als statische JSON-Dateien.

Für das Cloud-/Static-Hosting (GitHub Pages) wird kein laufender Server benötigt: Das
Frontend lädt die Inhalte direkt aus statischen JSON-Dateien unter frontend/data/.

Erzeugte Dateien:
  frontend/data/<YYYY-MM-DD>.json  - komplette Einzelausgabe
  frontend/data/latest.json        - Kopie der neuesten Ausgabe
  frontend/data/index.json         - Liste aller Ausgaben (fürs Archiv)

Die index.json akkumuliert über die bereits vorhandenen Dateien, damit das Archiv auch
dann vollständig bleibt, wenn die SQLite-Datenbank pro Lauf neu aufgebaut wird (z. B. in
einem frischen GitHub-Actions-Checkout).
"""
import json
import logging
from pathlib import Path

from backend import db
from backend.config import FRONTEND_DIR

logger = logging.getLogger(__name__)

DATA_DIR = Path(FRONTEND_DIR) / "data"


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def _count_articles(edition: dict) -> int:
    arts = edition.get("articles", {})
    return len(arts.get("lokal", [])) + len(arts.get("welt", [])) + len(arts.get("sport", []))


def _load_existing_index() -> dict:
    """Liest die bestehende index.json (falls vorhanden) als {date: entry}-Map."""
    index_path = DATA_DIR / "index.json"
    if not index_path.exists():
        return {}
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            entries = json.load(f)
        return {e["date"]: e for e in entries if isinstance(e, dict) and "date" in e}
    except Exception:
        logger.warning("Bestehende index.json konnte nicht gelesen werden - wird neu aufgebaut.")
        return {}


def export_edition(date_str: str) -> None:
    """Exportiert eine einzelne Ausgabe als <date>.json und (falls neueste) latest.json."""
    edition = db.get_edition_full(date_str)
    if not edition:
        logger.warning("Keine Ausgabe für %s in der Datenbank - nichts zu exportieren.", date_str)
        return

    # index.json aktualisieren (bestehende Einträge + diese Ausgabe)
    index = _load_existing_index()
    index[date_str] = {
        "date": edition["date"],
        "created_at": edition.get("created_at"),
        "article_count": _count_articles(edition),
    }

    # Ausgabennummern fortlaufend nach Datum vergeben (Nr. 1 = älteste Ausgabe).
    # Wichtig fürs Cloud-Hosting: die Nummer basiert auf dem akkumulierten Archiv,
    # nicht auf der (pro Lauf evtl. frischen) Datenbank.
    ascending = sorted(index.keys())
    issue_no = {d: i + 1 for i, d in enumerate(ascending)}

    edition["issue_number"] = issue_no[date_str]
    _write_json(DATA_DIR / f"{date_str}.json", edition)

    index_list = sorted(index.values(), key=lambda e: e["date"], reverse=True)
    _write_json(DATA_DIR / "index.json", index_list)

    # latest.json = neueste Ausgabe laut Index
    latest_date = index_list[0]["date"]
    if latest_date == date_str:
        latest_edition = edition
    else:
        latest_edition = db.get_edition_full(latest_date)
        if latest_edition:
            latest_edition["issue_number"] = issue_no[latest_date]
    if latest_edition:
        _write_json(DATA_DIR / "latest.json", latest_edition)

    logger.info("Statische JSON-Dateien exportiert nach %s (Ausgabe Nr. %s vom %s)",
                DATA_DIR, issue_no[date_str], date_str)


def export_all() -> None:
    """Exportiert alle in der Datenbank vorhandenen Ausgaben (praktisch für Erst-Export)."""
    editions = db.list_editions()
    if not editions:
        logger.info("Keine Ausgaben in der Datenbank vorhanden.")
        return
    for ed in editions:
        export_edition(ed["date"])
    logger.info("%d Ausgabe(n) als statische JSON exportiert.", len(editions))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    export_all()
