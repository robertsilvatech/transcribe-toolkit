"""Slugify utility — normalize text to safe folder/filename slugs."""

import re
import unicodedata


def slugify(text: str, max_len: int = 60) -> str:
    """Converte texto em slug seguro para nome de pasta/arquivo."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:max_len].rstrip("-")
