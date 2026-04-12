from __future__ import annotations

import re

_SPACE_RE = re.compile(r"[ ]+")


def tokenize_editorial_text(text: str) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    return [token for token in _SPACE_RE.split(stripped) if token]


def tokenize_parallel_readings(readings: list[str]) -> list[list[str]]:
    return [tokenize_editorial_text(text) for text in readings]


def token_counts_for_readings(readings: list[str]) -> list[int]:
    return [len(tokens) for tokens in tokenize_parallel_readings(readings)]
