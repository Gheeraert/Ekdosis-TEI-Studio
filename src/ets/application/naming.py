from __future__ import annotations

import re

from ets.domain import EditionConfig


def sanitize_filename_component(value: str) -> str:
    cleaned = value.strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = re.sub(r"[^0-9A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF._-]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("._")
    return cleaned or "document"


def build_default_basename(text: str, config: EditionConfig) -> str:
    del text  # output naming is no longer act/scene based
    return sanitize_filename_component(config.title or "document")
