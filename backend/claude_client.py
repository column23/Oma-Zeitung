"""Gemeinsamer Wrapper für Aufrufe der Anthropic API (Claude)."""
import json
import re

from anthropic import Anthropic

from backend.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

_client = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY ist nicht gesetzt. Bitte .env-Datei anlegen (siehe .env.example)."
            )
        _client = Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def _extract_json(text: str):
    """Extrahiert ein JSON-Objekt/Array aus einer Claude-Antwort (auch bei Markdown-Codeblöcken)."""
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    return json.loads(text)


def ask_claude_json(system: str, user_prompt: str, max_tokens: int = 2000, temperature: float = None):
    """Schickt einen Prompt an Claude und erwartet eine JSON-Antwort (Objekt oder Array)."""
    client = get_client()
    kwargs = {}
    if temperature is not None:
        kwargs["temperature"] = temperature
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
        **kwargs,
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return _extract_json(text)


def ask_claude_text(system: str, user_prompt: str, max_tokens: int = 1000, temperature: float = None) -> str:
    """Schickt einen Prompt an Claude und liefert reinen Text zurück."""
    client = get_client()
    kwargs = {}
    if temperature is not None:
        kwargs["temperature"] = temperature
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
        **kwargs,
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()
