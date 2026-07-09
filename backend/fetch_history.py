"""'Auf den Tag vor X Jahren' - historischer Rückblick, generiert von Claude."""
import logging
import random
from datetime import date

from backend.claude_client import ask_claude_json
from backend.config import HISTORY_YEARS_AGO_MAX, HISTORY_YEARS_AGO_MIN

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Du bist Redakteur einer täglichen Zeitung. Du schreibst die Rubrik 'Auf den Tag vor X "
    "Jahren' mit einem interessanten, gut dokumentierten historischen Ereignis, das an einem "
    "bestimmten Kalendertag stattgefunden hat.\n\n"
    "Schreibstil: Erzähle es wie eine kleine, gut geschriebene Anekdote - mit einem Einstieg, "
    "der Lust aufs Weiterlesen macht, nicht wie ein Lexikoneintrag ('Am [Datum] geschah...'). "
    "Vollständige, natürlich fließende Sätze, ein sachlicher aber warmer Erzählton. Wähle nach "
    "Möglichkeit ein Ereignis, das unterhaltsam oder bewegend ist (z. B. aus Kultur, Technik, "
    "Politik, Gesellschaft) und für ein breites, auch älteres Publikum interessant ist."
)


def fetch_history_fact(today: date = None) -> dict:
    today = today or date.today()
    years_ago = random.randint(HISTORY_YEARS_AGO_MIN, HISTORY_YEARS_AGO_MAX)
    target_year = today.year - years_ago

    day_month = today.strftime("%d.%m.")
    user_prompt = f"""Nenne ein interessantes, historisch belegtes Ereignis, das am {day_month} \
im Jahr {target_year} stattgefunden hat (also heute vor {years_ago} Jahren). Falls dir für \
genau dieses Jahr kein gutes Ereignis einfällt, wähle stattdessen ein anderes Jahr, das \
zwischen {today.year - HISTORY_YEARS_AGO_MAX} und {today.year - HISTORY_YEARS_AGO_MIN} liegt \
und am {day_month} ein belegtes Ereignis hat.

Antworte NUR mit einem JSON-Objekt (keine Erklärungen, kein Markdown) in diesem Format:

{{
  "year": 1969,
  "event_text": "3-5 Sätze über das Ereignis, erzählerisch und lebendig, aber sachlich korrekt."
}}"""

    try:
        result = ask_claude_json(SYSTEM_PROMPT, user_prompt, max_tokens=600)
        year = int(result.get("year", target_year))
        return {
            "year": year,
            "years_ago": today.year - year,
            "event_text": result.get("event_text", "").strip(),
        }
    except Exception:
        logger.exception("Fehler beim Erzeugen des historischen Rückblicks")
        return {
            "year": target_year,
            "years_ago": years_ago,
            "event_text": "Für den heutigen Tag konnte leider kein historisches Ereignis geladen werden.",
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(fetch_history_fact())
