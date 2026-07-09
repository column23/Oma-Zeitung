"""Täglicher Kreuzworträtsel-Generator: Begriffe von Claude, Gitter-Platzierung in Python."""
import logging
import random

from backend.claude_client import ask_claude_json

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Du erstellst Begriffe für ein Kreuzworträtsel in einer Zeitung für ältere Leserinnen und "
    "Leser. Die Begriffe sollen thematisch zu den gegebenen Tagesnachrichten passen, aber auch "
    "ohne Vorwissen über die Nachrichten lösbar sein (die Rätsel-Frage muss den Begriff eindeutig "
    "beschreiben, z.B. Hauptstadt, bekannte Person, allgemeiner Begriff)."
)

FALLBACK_WORDS = [
    {"word": "ZEITUNG", "clue": "Täglich gedrucktes oder digitales Nachrichtenblatt"},
    {"word": "KAFFEE", "clue": "Beliebtes Heißgetränk zum Frühstück"},
    {"word": "GARTEN", "clue": "Grünfläche rund ums Haus mit Blumen und Gemüse"},
    {"word": "OSTSEE", "clue": "Meer nördlich von Schleswig-Holstein"},
    {"word": "FLENSBURG", "clue": "Stadt an der Förde ganz im Norden"},
    {"word": "SONNTAG", "clue": "Letzter Tag der Woche"},
    {"word": "TENNIS", "clue": "Sportart mit Schläger und gelbem Ball"},
    {"word": "WETTER", "clue": "Sonne, Regen oder Wolken am Himmel"},
    {"word": "ENKEL", "clue": "Kind des eigenen Kindes"},
    {"word": "MUSIK", "clue": "Klänge und Töne zum Anhören"},
]

_UMLAUT_MAP = str.maketrans({"Ä": "AE", "Ö": "OE", "Ü": "UE", "ß": "SS"})


def _normalize_word(word: str) -> str:
    word = word.upper().translate(_UMLAUT_MAP)
    word = "".join(ch for ch in word if ch.isalpha())
    return word


def generate_words_from_news(news_articles: list, num_words: int = 10) -> list:
    """Lässt Claude Kreuzworträtsel-Begriffe zu den Tagesnachrichten vorschlagen."""
    if not news_articles:
        return []

    headlines = "\n".join(f"- {a['title']}" for a in news_articles[:12])
    user_prompt = f"""Hier sind die heutigen Nachrichten-Überschriften:

{headlines}

Erstelle {num_words} Kreuzworträtsel-Begriffe (einzelne Wörter, KEINE Leerzeichen oder \
Bindestriche, 3-12 Buchstaben, deutsche Wörter, ruhig mit Umlauten geschrieben), die \
möglichst zu diesen Themen passen. Ergänze allgemeine, altersgerechte Begriffe, falls nicht \
genug thematische Wörter passen. Antworte NUR mit einem JSON-Array (keine Erklärung, kein \
Markdown) in diesem Format:

[
  {{"word": "BEISPIEL", "clue": "Kurze, eindeutige Rätselfrage für dieses Wort"}}
]"""

    try:
        result = ask_claude_json(SYSTEM_PROMPT, user_prompt, max_tokens=3000)
        words = []
        for item in result:
            w = _normalize_word(item.get("word", ""))
            clue = item.get("clue", "").strip()
            if 3 <= len(w) <= 12 and clue:
                words.append({"word": w, "clue": clue})
        return words
    except Exception:
        logger.exception("Fehler beim Erzeugen der Kreuzworträtsel-Begriffe")
        return []


def _can_place(word, row, col, direction, grid):
    for i, ch in enumerate(word):
        r = row + (i if direction == "V" else 0)
        c = col + (i if direction == "H" else 0)
        if (r, c) in grid and grid[(r, c)] != ch:
            return False
    return True


def _place_word(word, row, col, direction, grid):
    for i, ch in enumerate(word):
        r = row + (i if direction == "V" else 0)
        c = col + (i if direction == "H" else 0)
        grid[(r, c)] = ch


def build_crossword_grid(word_clue_pairs: list) -> dict:
    """Platziert Wörter kreuzweise auf einem Gitter (einfacher, robuster Algorithmus)."""
    # Längste Wörter zuerst platzieren, das ergibt stabilere Kreuzungen
    pairs = sorted(word_clue_pairs, key=lambda p: -len(p["word"]))
    grid = {}
    placed = []

    if not pairs:
        return {"width": 0, "height": 0, "cells": [], "words": []}

    first = pairs[0]
    _place_word(first["word"], 0, 0, "H", grid)
    placed.append({"word": first["word"], "clue": first["clue"], "row": 0, "col": 0, "direction": "H"})

    for pair in pairs[1:]:
        word = pair["word"]
        best = None
        for placed_word in placed:
            pw = placed_word["word"]
            for i, ch in enumerate(word):
                if ch not in pw:
                    continue
                for j, pch in enumerate(pw):
                    if pch != ch:
                        continue
                    # Kreuzung: neues Wort senkrecht zum bereits platzierten Wort
                    new_dir = "V" if placed_word["direction"] == "H" else "H"
                    if new_dir == "V":
                        row = placed_word["row"] - i
                        col = placed_word["col"] + j
                    else:
                        row = placed_word["row"] + j
                        col = placed_word["col"] - i
                    if _can_place(word, row, col, new_dir, grid):
                        best = (row, col, new_dir)
                        break
                if best:
                    break
            if best:
                break
        if best:
            row, col, direction = best
            _place_word(word, row, col, direction, grid)
            placed.append({"word": word, "clue": pair["clue"], "row": row, "col": col, "direction": direction})
        # Kein Platz gefunden -> Wort wird ausgelassen (Rätsel bleibt trotzdem lösbar)

    rows = [r for r, c in grid]
    cols = [c for r, c in grid]
    min_r, max_r = min(rows), max(rows)
    min_c, max_c = min(cols), max(cols)
    height = max_r - min_r + 1
    width = max_c - min_c + 1

    cells = [[None for _ in range(width)] for _ in range(height)]
    for (r, c), ch in grid.items():
        cells[r - min_r][c - min_c] = ch

    for w in placed:
        w["row"] -= min_r
        w["col"] -= min_c

    start_positions = sorted({(w["row"], w["col"]) for w in placed})
    numbering = {pos: i + 1 for i, pos in enumerate(start_positions)}

    words_out = [
        {
            "number": numbering[(w["row"], w["col"])],
            "direction": "across" if w["direction"] == "H" else "down",
            "clue": w["clue"],
            "answer": w["word"],
            "row": w["row"],
            "col": w["col"],
            "length": len(w["word"]),
        }
        for w in placed
    ]

    return {"width": width, "height": height, "cells": cells, "words": words_out}


def generate_crossword(news_articles: list = None, num_words: int = 10) -> dict:
    words = generate_words_from_news(news_articles or [], num_words)
    if len(words) < 5:
        needed = num_words - len(words)
        pool = [w for w in FALLBACK_WORDS if w["word"] not in {x["word"] for x in words}]
        random.shuffle(pool)
        words.extend(pool[:needed])
    return build_crossword_grid(words)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cw = generate_crossword([{"title": "Flensburg feiert Hafenfest"}, {"title": "Neue Fährverbindung nach Dänemark"}])
    for row in cw["cells"]:
        print(" ".join(ch if ch else "." for ch in row))
    for w in cw["words"]:
        print(w["number"], w["direction"], w["answer"], "-", w["clue"])
