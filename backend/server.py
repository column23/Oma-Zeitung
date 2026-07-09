"""Flask-Server: liefert das Frontend aus und stellt die JSON-API bereit."""
import logging
from datetime import date

from flask import Flask, jsonify, request, send_from_directory

from backend import db
from backend.config import FRONTEND_DIR, HOST, PORT

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
db.init_db()


# ---------- Frontend (statische Dateien) ----------

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# ---------- JSON-API ----------

@app.route("/api/edition/latest")
def api_edition_latest():
    latest_date = db.get_latest_edition_date()
    if not latest_date:
        return jsonify({"error": "Noch keine Ausgabe vorhanden. Bitte main.py ausführen."}), 404
    edition = db.get_edition_full(latest_date)
    return jsonify(edition)


@app.route("/api/edition/<date_str>")
def api_edition_by_date(date_str):
    edition = db.get_edition_full(date_str)
    if not edition:
        return jsonify({"error": f"Keine Ausgabe für {date_str} gefunden."}), 404
    return jsonify(edition)


@app.route("/api/editions")
def api_editions_list():
    search = request.args.get("search")
    editions = db.list_editions(search=search)
    return jsonify(editions)


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """Manuelles Anstoßen der Ausgaben-Erzeugung (praktisch für lokale Tests statt Cronjob)."""
    from backend.main import build_edition

    try:
        date_str = build_edition(date.today())
        return jsonify({"status": "ok", "date": date_str})
    except Exception as exc:
        logger.exception("Fehler bei manueller Ausgaben-Erzeugung")
        return jsonify({"status": "error", "message": str(exc)}), 500


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=True)
