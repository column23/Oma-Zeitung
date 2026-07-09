"""Sport-Rubrik mit Tennis-Fokus: RSS-Fetching + Zusammenfassung."""
import logging

from backend.claude_client import ask_claude_json
from backend.config import MAX_ARTICLES_SPORT, SPORT_FEEDS
from backend.fetch_news import fetch_raw_entries

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Du bist Sportredakteur einer täglichen Zeitung. Du schreibst die Rubrik 'Sport' mit "
    "Schwerpunkt Tennis: große Turniere (Grand Slams, ATP/WTA-Touren) und bekannte "
    "Spielerinnen/Spieler.\n\n"
    "Länge und Tiefe:\n"
    "- Schreibe ausführliche Artikel statt Kurzmeldungen: ein Lead-Absatz mit dem Ergebnis bzw. "
    "der wichtigsten Neuigkeit, danach ein bis zwei weitere Absätze mit Einordnung, Turnierkontext "
    "oder Bedeutung für die Spielerin/den Spieler - soweit die Rohquelle das hergibt.\n"
    "- ERFINDE NIEMALS Ergebnisse, Zahlen oder Zitate, die nicht in der Rohquelle stehen. Ist die "
    "Quelle dünn, bleib entsprechend kürzer statt mit Füllsätzen zu strecken.\n"
    "- Keine Wiederholungen: Jeder Absatz muss neue Information bringen, nichts zweimal mit "
    "anderen Worten sagen.\n\n"
    "Schreibstil:\n"
    "- Lead-Prinzip: Ergebnis oder wichtigste Neuigkeit zuerst, dann Einordnung/Kontext.\n"
    "- Lebendiger, aber seriöser Sportjournalismus - wie ein erfahrener Redakteur, nicht wie "
    "eine nüchterne Ergebnisliste. Ruhig auch mal Spannung oder Bedeutung eines Spiels einordnen.\n"
    "- Vollständige, natürlich fließende Sätze mit variabler Länge, keine Floskeln wie "
    "'Zusammenfassend' oder 'Dieser Artikel'.\n"
    "- Verschiedene Meldungen unterschiedlich formulieren, nicht immer nach demselben Muster "
    "aufbauen.\n"
    "- Trenne Absätze im 'summary'-Feld durch eine Leerzeile (zwei Zeilenumbrüche).\n\n"
    "WICHTIG: Formuliere IMMER in eigenen Worten - übernimm niemals wörtliche Sätze oder "
    "Zitate aus den Originalartikeln. Ignoriere Artikel, die nicht wirklich Tennis-Inhalte sind."
)


def fetch_and_summarize_sport() -> list:
    logger.info("Lade Sport/Tennis-Feeds ...")
    raw = fetch_raw_entries(SPORT_FEEDS, limit_per_feed=20)
    logger.info("%d Roh-Sportartikel gefunden", len(raw))
    if not raw:
        return []

    articles_block = "\n\n".join(
        f"[{i}] Titel: {e['title']}\nQuelle: {e['source_name']}\nLink: {e['link']}\n"
        f"Datum: {e['published']}\nBeschreibung: {e['description']}"
        for i, e in enumerate(raw)
    )

    user_prompt = f"""Hier sind Rohartikel für die Sport-Rubrik (Fokus Tennis):

{articles_block}

Wähle die {MAX_ARTICLES_SPORT} wichtigsten, thematisch unterschiedlichen Tennis-Meldungen aus
(große Turniere, bekannte Spieler, Ergebnisse). Falls weniger als {MAX_ARTICLES_SPORT} echte
Tennis-Artikel vorhanden sind, gib nur so viele zurück wie tatsächlich relevant sind.
Antworte NUR mit einem JSON-Array (keine Erklärungen, kein Markdown) in diesem Format:

[
  {{
    "title": "Prägnante, eigene Überschrift im Zeitungsstil (max. 12 Wörter)",
    "summary": "Mehrere Absätze Fließtext (durch Leerzeile getrennt), Lead-Prinzip, journalistischer Ton, eigene Worte, keine wörtlichen Zitate, keine Wiederholungen, keine erfundenen Fakten",
    "source_name": "Name der Quelle",
    "source_url": "Link zum Originalartikel",
    "published_at": "Datum/Zeit falls vorhanden, sonst leerer String"
  }}
]"""

    try:
        result = ask_claude_json(SYSTEM_PROMPT, user_prompt, max_tokens=5000)
        if isinstance(result, list):
            return result[:MAX_ARTICLES_SPORT]
        return []
    except Exception:
        logger.exception("Fehler bei der Zusammenfassung der Sport-Rubrik")
        return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for a in fetch_and_summarize_sport():
        print(f"- {a['title']}\n  {a['summary']}\n  Quelle: {a.get('source_name')} ({a.get('source_url')})")
