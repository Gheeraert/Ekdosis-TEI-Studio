from __future__ import annotations

import re

from ets.domain import Act, EditionConfig, Play, Scene, Speech, StageDirection, VerseLine

_ACT_RE = re.compile(r"^####(.+?)####$")
_SCENE_RE = re.compile(r"^###(.+?)###$")
_SPEAKER_RE = re.compile(r"^#(.+?)#$")
_CAST_RE = re.compile(r"##(.*?)##")
_STAGE_RE = re.compile(r"^\*\*(.+?)\*\*$")


def _split_parallel_blocks(text: str, witness_count: int) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip("\r")
        if line.strip() == "":
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)
    if current:
        blocks.append(current)

    for index, block in enumerate(blocks):
        if len(block) != witness_count:
            raise ValueError(
                f"Malformed parallel block at index {index}: expected {witness_count} lines, got {len(block)}."
            )
    return blocks


def _extract_wrapped(block: list[str], pattern: re.Pattern[str]) -> list[str]:
    extracted: list[str] = []
    for line in block:
        match = pattern.match(line.strip())
        if not match:
            raise ValueError(f"Malformed marker line: {line}")
        extracted.append(match.group(1).strip())
    return extracted


def _extract_cast(block: list[str]) -> list[str]:
    result: list[str] = []
    for line in block:
        names = [part.strip() for part in _CAST_RE.findall(line)]
        result.append(" ".join(name for name in names if name))
    return result


def _clean_verse_reading(raw: str) -> tuple[str, bool, bool, bool]:
    text = raw.strip()
    split_continue = text.startswith("***")
    split_start = text.endswith("***")
    whole_line_variant = text.startswith("#####")

    if split_continue:
        text = text[3:]
    if split_start:
        text = text[:-3]
    if whole_line_variant:
        text = text[5:]

    text = text.strip().replace("~", "\u00A0")
    return text, split_start, split_continue, whole_line_variant


def parse_play(text: str, config: EditionConfig) -> Play:
    blocks = _split_parallel_blocks(text, len(config.witnesses))
    play = Play()
    current_act: Act | None = None
    current_scene: Scene | None = None
    current_speech: Speech | None = None

    line_number = config.start_line_number
    shared_base: int | None = None
    shared_part = 0

    for block_index, block in enumerate(blocks):
        first = block[0].strip()

        if _ACT_RE.match(first):
            current_act = Act(head_readings=_extract_wrapped(block, _ACT_RE), head_block_index=block_index)
            play.acts.append(current_act)
            current_scene = None
            current_speech = None
            shared_base = None
            shared_part = 0
            continue

        if _SCENE_RE.match(first) and not first.startswith("####"):
            if current_act is None:
                implicit_head = [f"ACTE {config.act_number}" for _ in config.witnesses]
                current_act = Act(head_readings=implicit_head, head_block_index=-1)
                play.acts.append(current_act)
            current_scene = Scene(head_readings=_extract_wrapped(block, _SCENE_RE), head_block_index=block_index, cast_readings=[])
            current_act.scenes.append(current_scene)
            current_speech = None
            shared_base = None
            shared_part = 0
            continue

        if first.startswith("##") and not first.startswith("###") and _CAST_RE.search(first):
            if current_scene is None:
                raise ValueError("Cast found before scene.")
            current_scene.cast_readings = _extract_cast(block)
            current_scene.cast_block_index = block_index
            continue

        if _SPEAKER_RE.match(first) and not first.startswith("##"):
            if current_scene is None:
                raise ValueError("Speaker found before scene.")
            current_speech = Speech(speaker_readings=_extract_wrapped(block, _SPEAKER_RE), speaker_block_index=block_index)
            current_scene.speeches.append(current_speech)
            continue

        if _STAGE_RE.match(first):
            if current_scene is None:
                raise ValueError("Stage direction found before scene.")
            readings = _extract_wrapped(block, _STAGE_RE)
            direction = StageDirection(readings=readings, block_index=block_index)
            if current_speech is not None:
                current_speech.elements.append(direction)
            else:
                current_scene.stage_directions.append(direction)
            continue

        if current_speech is None:
            raise ValueError("Verse found before speaker.")

        cleaned: list[str] = []
        split_starts = False
        split_continues = False
        whole_line_variant = False
        for line in block:
            line_text, starts, continues, whole_line = _clean_verse_reading(line)
            cleaned.append(line_text)
            split_starts = split_starts or starts
            split_continues = split_continues or continues
            whole_line_variant = whole_line_variant or whole_line

        if shared_base is not None and split_continues:
            shared_part += 1
            number = f"{shared_base}.{shared_part}"
        else:
            base = line_number
            line_number += 1
            if split_starts:
                shared_base = base
                shared_part = 1
                number = f"{base}.1"
            else:
                number = str(base)
                shared_base = None
                shared_part = 0

        if shared_base is not None and not split_starts:
            shared_base = None
            shared_part = 0

        current_speech.elements.append(
            VerseLine(
                number=number,
                readings=cleaned,
                block_index=block_index,
                whole_line_variant=whole_line_variant,
            )
        )

    return play
