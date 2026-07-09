"""RSS-Fetching + Zusammenfassung der Nachrichten-Rubriken 'Lokal' und 'Welt'."""
import logging
from html import unescape
from html.parser import HTMLParser

import feedparser

from backend.claude_client import ask_claude_json
from backend.config import MAX_ARTICLES_PER_CATEGORY, NEWS_FEEDS

logger = logging.getLogger(__name__)


class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return "".join(self.parts)


def strip_html(html: str) -> str:
    if not html:
        return ""
    stripper = _HTMLStripper()
    stripper.feed(html)
    return unescape(stripper.get_text()).strip()


def fetch_raw_entries(feed_urls: list, limit_per_feed: int = 12) -> list:
    """Lädt Rohartikel (Titel, Beschreibung, Link, Datum, Quelle) aus einer Liste von RSS-Feeds."""
    entries = []
    for url in feed_urls:
        try:
            parsed = feedparser.parse(url)
            if parsed.bozo and not parsed.entries:
                logger.warning("Feed konnte nicht gelesen werden: %s (%s)", url, parsed.bozo_exception)
                continue
            source_name = parsed.feed.get("title", url)
            for entry in parsed.entries[:limit_per_feed]:
                raw_desc = entry.get("summary", "") or entry.get("description", "")
                entries.append(
                    {
                        "title": strip_html(entry.get("title", "")),
                        "description": strip_html(raw_desc)[:1500],
                        "link": entry.get("link", ""),
                        "published": entry.get("published", "") or entry.get("updated", ""),
                        "source_name": source_name,
                    }
                )
        except Exception:
            logger.exception("Fehler beim Abrufen des Feeds: %s", url)
    return entries


SYSTEM_PROMPT = (
    "Du bist Redakteur einer täglichen Zeitung für ältere Leserinnen und Leser (Oma-Zeitung). "
    "Deine Aufgabe: Rohartikel aus RSS-Feeds zu einer kleinen Auswahl der wichtigsten, "
    "eigenständigen Nachrichten ausarbeiten - im Stil eines erfahrenen Zeitungsredakteurs, "
    "nicht wie eine KI-generierte Stichpunktliste.\n\n"
    "Länge und Tiefe:\n"
    "- Schreibe ausführliche, richtige Zeitungsartikel, keine Kurzmeldungen: mehrere Absätze "
    "(Lead-Absatz + ein bis drei weitere Absätze mit Hintergrund, Kontext und Einordnung), wenn "
    "die Rohquelle das hergibt.\n"
    "- Nutze dafür alles, was in Titel und Beschreibung der Rohquelle an Substanz steckt - "
    "Zusammenhänge erklären, Bedeutung einordnen, ggf. naheliegenden Kontext ergänzen (allgemein "
    "bekanntes Hintergrundwissen, keine erfundenen Fakten).\n"
    "- ERFINDE NIEMALS zusätzliche Fakten, Zahlen, Namen oder Zitate, die nicht aus der Rohquelle "
    "hervorgehen oder allgemein bekanntes Hintergrundwissen sind. Ist die Rohquelle sehr dünn, "
    "dann bleib ehrlich kürzer, statt den Text künstlich mit Füllsätzen zu strecken.\n"
    "- Keine Wiederholungen: Jeder Satz und jeder Absatz muss neue Information liefern. Sag nie "
    "in einem späteren Absatz mit anderen Worten das, was im Lead-Absatz schon stand.\n\n"
    "Schreibstil:\n"
    "- Beginne jede Meldung mit dem Wichtigsten (Lead-Prinzip): Wer/Was/Wo direkt im ersten Satz "
    "des ersten Absatzes, keine langsame Hinführung.\n"
    "- Schreibe in vollständigen, natürlich fließenden Sätzen mit variabler Satzlänge - mal ein "
    "kurzer prägnanter Satz, mal ein längerer mit Nebeninformation. Reine Aneinanderreihung von "
    "Fakten wirkt roboterhaft und ist zu vermeiden.\n"
    "- Seriöser, sachlicher Zeitungston, aber warm und zugänglich formuliert - so, wie eine "
    "Regionalzeitung für ein breites, auch älteres Publikum schreibt. Nicht steif, nicht jugendlich-locker.\n"
    "- Vermeide KI-typische Floskeln und Phrasen wie 'Zusammenfassend lässt sich sagen', "
    "'Es ist wichtig zu beachten', 'Dieser Artikel behandelt', 'Insgesamt zeigt sich' o. Ä.\n"
    "- Variiere die Formulierungen zwischen den einzelnen Meldungen - nicht jede Meldung mit "
    "demselben Satzmuster, derselben Konstruktion oder demselben Absatzaufbau beginnen.\n"
    "- Keine Bullet Points, keine Überschriften-Fragmente als Fließtext - immer echte, "
    "grammatisch vollständige Sätze und Absätze.\n"
    "- Trenne Absätze im 'summary'-Feld durch eine Leerzeile (zwei Zeilenumbrüche).\n\n"
    "WICHTIG: Formuliere IMMER in eigenen Worten um - übernimm niemals wörtliche Sätze oder "
    "Zitate aus den Originalartikeln. Fasse mehrere Artikel zum selben Thema zu einer Meldung "
    "zusammen (keine Duplikate)."
)


def summarize_category(raw_entries: list, category_label: str, max_articles: int) -> list:
    if not raw_entries:
        return []

    articles_block = "\n\n".join(
        f"[{i}] Titel: {e['title']}\nQuelle: {e['source_name']}\nLink: {e['link']}\n"
        f"Datum: {e['published']}\nBeschreibung: {e['description']}"
        for i, e in enumerate(raw_entries)
    )

    user_prompt = f"""Hier sind Rohartikel für die Rubrik "{category_label}":

{articles_block}

Wähle die {max_articles} wichtigsten, thematisch unterschiedlichen Nachrichten aus und
antworte NUR mit einem JSON-Array (keine Erklärungen, kein Markdown) in diesem Format:

[
  {{
    "title": "Prägnante, eigene Überschrift im Zeitungsstil (max. 12 Wörter, kein Klickköder)",
    "summary": "Mehrere Absätze Fließtext (durch Leerzeile getrennt), Lead-Prinzip, journalistischer Ton, eigene Worte, keine wörtlichen Zitate, keine Wiederholungen, keine erfundenen Fakten",
    "source_name": "Name der Quelle",
    "source_url": "Link zum Originalartikel",
    "published_at": "Datum/Zeit falls vorhanden, sonst leerer String"
  }}
]"""

    try:
        result = ask_claude_json(SYSTEM_PROMPT, user_prompt, max_tokens=6000)
        if isinstance(result, list):
            return result[:max_articles]
        logger.warning("Unerwartetes Antwortformat von Claude für Kategorie %s", category_label)
        return []
    except Exception:
        logger.exception("Fehler bei der Zusammenfassung der Kategorie %s", category_label)
        return []


def fetch_and_summarize_all() -> dict:
    """Lädt und fasst die Rubriken 'lokal' und 'welt' zusammen. Gibt {'lokal': [...], 'welt': [...]} zurück."""
    result = {}
    labels = {"lokal": "Lokal (Flensburg/Schleswig-Holstein)", "welt": "Welt"}
    for category, feeds in NEWS_FEEDS.items():
        logger.info("Lade RSS-Feeds für Kategorie '%s' ...", category)
        raw = fetch_raw_entries(feeds)
        logger.info("%d Rohartikel gefunden für '%s'", len(raw), category)
        result[category] = summarize_category(raw, labels.get(category, category), MAX_ARTICLES_PER_CATEGORY)
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = fetch_and_summarize_all()
    for cat, articles in data.items():
        print(f"\n=== {cat.upper()} ===")
        for a in articles:
            print(f"- {a['title']}\n  {a['summary']}\n  Quelle: {a.get('source_name')} ({a.get('source_url')})")
