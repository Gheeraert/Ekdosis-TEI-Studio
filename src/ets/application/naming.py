from __future__ import annotations

import re

from ets.domain import EditionConfig

_ACT_RE = re.compile(r"^####(.+?)####$")
_SCENE_RE = re.compile(r"^###(.+?)###$")


def _roman_to_int(value: str) -> int | None:
    roman = value.upper()
    if not roman or any(ch not in "IVXLCDM" for ch in roman):
        return None
    mapping = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    prev = 0
    for char in reversed(roman):
        num = mapping[char]
        if num < prev:
            total -= num
        else:
            total += num
            prev = num
    return total


def _normalize_act_number(raw: str) -> str | None:
    text = raw.strip()
    if not text:
        return None
    if text.isdigit():
        return str(int(text))
    roman = _roman_to_int(text)
    if roman is not None:
        return str(roman)
    return None


def _extract_act_number(label: str) -> str | None:
    compact = re.sub(r"\s+", " ", label.strip().upper())
    match = re.search(r"ACTE\s+([IVXLCDM]+|\d+)", compact)
    if not match:
        return None
    return _normalize_act_number(match.group(1))


def _split_parallel_blocks_loose(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        if line.strip() == "":
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)
    if current:
        blocks.append(current)
    return blocks


def infer_scene_count_for_act(text: str, config: EditionConfig) -> int | None:
    target_act = _normalize_act_number(config.act_number)
    blocks = _split_parallel_blocks_loose(text)
    if not blocks:
        return None

    current_act: str | None = None
    count = 0
    for block in blocks:
        first = block[0].strip()
        act_match = _ACT_RE.match(first)
        if act_match:
            current_act = _extract_act_number(act_match.group(1))
            continue
        scene_match = _SCENE_RE.match(first)
        if scene_match and current_act is not None and target_act is not None and current_act == target_act:
            count += 1
    return count if count > 0 else None


def sanitize_filename_component(value: str) -> str:
    cleaned = value.strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = re.sub(r"[^0-9A-Za-zÀ-ÖØ-öø-ÿ._-]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("._")
    return cleaned or "document"


def build_default_basename(text: str, config: EditionConfig) -> str:
    title = sanitize_filename_component(config.title or "document")
    act = sanitize_filename_component(config.act_number or "1")
    scene = sanitize_filename_component(config.scene_number or "1")
    total = infer_scene_count_for_act(text, config)
    if total is None:
        return f"{title}_A{act}_S{scene}"
    return f"{title}_A{act}_S{scene}of{total}"
