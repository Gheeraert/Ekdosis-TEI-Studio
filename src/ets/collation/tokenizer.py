from __future__ import annotations

import re

_SPACE_RE = re.compile(r"[ ]+")


def tokenize_editorial_text(text: str) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    return [token for token in _SPACE_RE.split(stripped) if token]
