from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from ets.collation import token_counts_for_readings


class DiagnosticLevel(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class ValidationDiagnostic:
    level: DiagnosticLevel
    code: str
    message: str
    line_number: int | None = None
    block_index: int | None = None
    act: str | None = None
    scene: str | None = None
    speaker: str | None = None
    excerpt: str | None = None
    block_type: str | None = None
    token_counts: list[int] | None = None
    witness_labels: list[str] | None = None
    block_lines: list[str] | None = None


@dataclass(frozen=True)
class ValidationReport:
    diagnostics: list[ValidationDiagnostic]

    @property
    def has_errors(self) -> bool:
        return any(item.level == DiagnosticLevel.ERROR for item in self.diagnostics)


class InputValidationError(ValueError):
    def __init__(self, diagnostics: list[ValidationDiagnostic]) -> None:
        self.diagnostics = diagnostics
        joined = "; ".join(item.message for item in diagnostics[:5])
        suffix = "" if len(diagnostics) <= 5 else f" (+{len(diagnostics) - 5} more)"
        super().__init__(f"Input validation failed: {joined}{suffix}")


@dataclass(frozen=True)
class _Block:
    index: int
    start_line_number: int
    lines: list[str]

    @property
    def first(self) -> str:
        return self.lines[0].strip()


_ACT_RE = re.compile(r"^####(.+?)####$")
_SCENE_RE = re.compile(r"^###(.+?)###$")
_SPEAKER_RE = re.compile(r"^#(.+?)#$")
_CAST_LINE_RE = re.compile(r"^(##.+##)(\s+##.+##)*$")
_CAST_TOKEN_RE = re.compile(r"##(.*?)##")
_STAGE_RE = re.compile(r"^\*\*(?!\*)(.+?)(?<!\*)\*\*$")
_IMPLICIT_OPEN_RE = re.compile(r"^\$\$([A-Za-z][A-Za-z0-9_-]*)\$\$$")
_IMPLICIT_CLOSE_RE = re.compile(r"^\$\$fin\$\$$", re.IGNORECASE)


def _split_parallel_blocks(text: str) -> list[_Block]:
    blocks: list[_Block] = []
    current: list[str] = []
    current_start = 1
    for index, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip("\r")
        if line.strip() == "":
            if current:
                blocks.append(_Block(index=len(blocks), start_line_number=current_start, lines=current))
                current = []
            current_start = index + 1
            continue
        if not current:
            current_start = index
        current.append(line)
    if current:
        blocks.append(_Block(index=len(blocks), start_line_number=current_start, lines=current))
    return blocks


def _extract_act_label(line: str) -> str:
    match = _ACT_RE.match(line.strip())
    return match.group(1).strip() if match else line.strip()


def _extract_scene_label(line: str) -> str:
    match = _SCENE_RE.match(line.strip())
    return match.group(1).strip() if match else line.strip()


def _extract_speaker_label(line: str) -> str:
    match = _SPEAKER_RE.match(line.strip())
    return match.group(1).strip() if match else line.strip()


def _append_error(
    diagnostics: list[ValidationDiagnostic],
    *,
    code: str,
    message: str,
    line_number: int | None,
    block_index: int | None,
    act: str | None,
    scene: str | None,
    speaker: str | None,
    excerpt: str | None = None,
    block_type: str | None = None,
    token_counts: list[int] | None = None,
    witness_labels: list[str] | None = None,
    block_lines: list[str] | None = None,
) -> None:
    diagnostics.append(
        ValidationDiagnostic(
            level=DiagnosticLevel.ERROR,
            code=code,
            message=message,
            line_number=line_number,
            block_index=block_index,
            act=act,
            scene=scene,
            speaker=speaker,
            excerpt=excerpt,
            block_type=block_type,
            token_counts=token_counts,
            witness_labels=witness_labels,
            block_lines=block_lines,
        )
    )


def _append_warning(
    diagnostics: list[ValidationDiagnostic],
    *,
    code: str,
    message: str,
    line_number: int | None,
    block_index: int | None,
    act: str | None,
    scene: str | None,
    speaker: str | None,
    excerpt: str | None = None,
    block_type: str | None = None,
    token_counts: list[int] | None = None,
    witness_labels: list[str] | None = None,
    block_lines: list[str] | None = None,
) -> None:
    diagnostics.append(
        ValidationDiagnostic(
            level=DiagnosticLevel.WARNING,
            code=code,
            message=message,
            line_number=line_number,
            block_index=block_index,
            act=act,
            scene=scene,
            speaker=speaker,
            excerpt=excerpt,
            block_type=block_type,
            token_counts=token_counts,
            witness_labels=witness_labels,
            block_lines=block_lines,
        )
    )


def _clean_verse_for_collation(raw: str) -> tuple[str, bool]:
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
    return text.strip().replace("~", "\u00A0"), whole_line_variant


def _validate_token_count_consistency(
    diagnostics: list[ValidationDiagnostic],
    *,
    normalized_readings: list[str],
    witness_labels: list[str],
    block_type: str,
    line_number: int,
    block_index: int,
    act: str | None,
    scene: str | None,
    speaker: str | None,
    block_lines: list[str],
) -> None:
    counts = token_counts_for_readings(normalized_readings)
    if len(set(counts)) == 1:
        return
    counts_display = ", ".join(f"{label}:{count}" for label, count in zip(witness_labels, counts))
    _append_error(
        diagnostics,
        code="E_TOKEN_COUNT_MISMATCH",
        message=(
            f"Token count mismatch in collatable parallel block "
            f"(type={block_type}, block={block_index}, counts=[{counts_display}])."
        ),
        line_number=line_number,
        block_index=block_index,
        act=act,
        scene=scene,
        speaker=speaker,
        excerpt=block_lines[0].strip() if block_lines else None,
        block_type=block_type,
        token_counts=counts,
        witness_labels=witness_labels,
        block_lines=block_lines,
    )


def validate_input_text(text: str, witness_count: int, witness_sigla: list[str] | None = None) -> ValidationReport:
    diagnostics: list[ValidationDiagnostic] = []
    blocks = _split_parallel_blocks(text)
    labels = witness_sigla if witness_sigla is not None and len(witness_sigla) == witness_count else [
        f"W{i + 1}" for i in range(witness_count)
    ]

    current_act: str | None = None
    current_scene: str | None = None
    current_speaker: str | None = None
    implicit_open: bool = False
    shared_open: bool = False
    shared_carried_across_scene: bool = False
    seen_scene = False
    seen_speaker = False

    for block in blocks:
        first = block.first
        line = block.start_line_number

        if len(block.lines) != witness_count:
            _append_error(
                diagnostics,
                code="E_BLOCK_SIZE",
                message=(
                    f"Malformed parallel block at index {block.index}: "
                    f"expected {witness_count} lines, got {len(block.lines)}."
                ),
                line_number=line,
                block_index=block.index,
                act=current_act,
                scene=current_scene,
                speaker=current_speaker,
                excerpt=first,
            )
            continue

        kinds = {
            "act": _ACT_RE.match(first) is not None and not first.startswith("#####"),
            "scene": _SCENE_RE.match(first) is not None and not first.startswith("####"),
            "cast": _CAST_LINE_RE.match(first) is not None and first.startswith("##") and not first.startswith("###"),
            "speaker": _SPEAKER_RE.match(first) is not None and not first.startswith("##"),
            "stage": _STAGE_RE.match(first) is not None,
            "implicit_open": _IMPLICIT_OPEN_RE.match(first) is not None,
            "implicit_close": _IMPLICIT_CLOSE_RE.match(first) is not None,
            "whole_line_variant": first.startswith("#####"),
        }

        if kinds["act"]:
            normalized_act: list[str] = []
            malformed = False
            for idx, raw in enumerate(block.lines):
                match = _ACT_RE.match(raw.strip())
                if match is None:
                    _append_error(
                        diagnostics,
                        code="E_ACT_MARKER_MALFORMED",
                        message="Malformed act marker line.",
                        line_number=line + idx,
                        block_index=block.index,
                        act=current_act,
                        scene=current_scene,
                        speaker=current_speaker,
                        excerpt=raw.strip(),
                    )
                    malformed = True
                else:
                    normalized_act.append(match.group(1).strip())
            if not malformed:
                _validate_token_count_consistency(
                    diagnostics,
                    normalized_readings=normalized_act,
                    witness_labels=labels,
                    block_type="act_head",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    block_lines=block.lines,
                )
            if implicit_open:
                _append_error(
                    diagnostics,
                    code="E_IMPLICIT_SPAN_UNCLOSED",
                    message="Unclosed implicit stage span before act boundary.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
                implicit_open = False
            current_act = _extract_act_label(first)
            current_scene = None
            current_speaker = None
            shared_open = False
            shared_carried_across_scene = False
            continue

        if kinds["scene"]:
            normalized_scene: list[str] = []
            malformed = False
            for idx, raw in enumerate(block.lines):
                match = _SCENE_RE.match(raw.strip())
                if match is None:
                    _append_error(
                        diagnostics,
                        code="E_SCENE_MARKER_MALFORMED",
                        message="Malformed scene marker line.",
                        line_number=line + idx,
                        block_index=block.index,
                        act=current_act,
                        scene=current_scene,
                        speaker=current_speaker,
                        excerpt=raw.strip(),
                    )
                    malformed = True
                else:
                    normalized_scene.append(match.group(1).strip())
            if not malformed:
                _validate_token_count_consistency(
                    diagnostics,
                    normalized_readings=normalized_scene,
                    witness_labels=labels,
                    block_type="scene_head",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    block_lines=block.lines,
                )
            if implicit_open:
                _append_error(
                    diagnostics,
                    code="E_IMPLICIT_SPAN_UNCLOSED",
                    message="Unclosed implicit stage span before scene boundary.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
                implicit_open = False
            if shared_open:
                if shared_carried_across_scene:
                    # Keep parser-compatible behavior: close deterministically at the second
                    # boundary and report as non-blocking diagnostic.
                    _append_warning(
                        diagnostics,
                        code="W_SHARED_VERSE_FORCE_CLOSE",
                        message="Shared verse was force-closed after crossing one scene boundary without continuation.",
                        line_number=line,
                        block_index=block.index,
                        act=current_act,
                        scene=current_scene,
                        speaker=current_speaker,
                        excerpt=first,
                    )
                    shared_open = False
                    shared_carried_across_scene = False
                else:
                    shared_carried_across_scene = True
            seen_scene = True
            current_scene = _extract_scene_label(first)
            current_speaker = None
            continue

        if kinds["cast"]:
            normalized_cast: list[str] = []
            malformed = False
            for idx, raw in enumerate(block.lines):
                stripped = raw.strip()
                if _CAST_LINE_RE.match(stripped) is None:
                    _append_error(
                        diagnostics,
                        code="E_CAST_MARKER_MALFORMED",
                        message="Malformed cast marker line.",
                        line_number=line + idx,
                        block_index=block.index,
                        act=current_act,
                        scene=current_scene,
                        speaker=current_speaker,
                        excerpt=stripped,
                    )
                    malformed = True
                names = [part.strip() for part in _CAST_TOKEN_RE.findall(raw)]
                normalized_cast.append(" ".join(name for name in names if name))
            if not malformed:
                _validate_token_count_consistency(
                    diagnostics,
                    normalized_readings=normalized_cast,
                    witness_labels=labels,
                    block_type="cast",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    block_lines=block.lines,
                )
            if implicit_open:
                _append_error(
                    diagnostics,
                    code="E_IMPLICIT_SPAN_UNCLOSED",
                    message="Unclosed implicit stage span before cast block.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
                implicit_open = False
            if current_scene is None:
                _append_error(
                    diagnostics,
                    code="E_CAST_OUTSIDE_SCENE",
                    message="Cast found before scene.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
            continue

        if kinds["speaker"]:
            normalized_speaker: list[str] = []
            malformed = False
            for idx, raw in enumerate(block.lines):
                match = _SPEAKER_RE.match(raw.strip())
                if match is None or raw.strip().startswith("##"):
                    _append_error(
                        diagnostics,
                        code="E_SPEAKER_MARKER_MALFORMED",
                        message="Malformed speaker marker line.",
                        line_number=line + idx,
                        block_index=block.index,
                        act=current_act,
                        scene=current_scene,
                        speaker=current_speaker,
                        excerpt=raw.strip(),
                    )
                    malformed = True
                else:
                    normalized_speaker.append(match.group(1).strip())
            if not malformed:
                _validate_token_count_consistency(
                    diagnostics,
                    normalized_readings=normalized_speaker,
                    witness_labels=labels,
                    block_type="speaker",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    block_lines=block.lines,
                )
            if implicit_open:
                _append_error(
                    diagnostics,
                    code="E_IMPLICIT_SPAN_UNCLOSED",
                    message="Unclosed implicit stage span before speaker change.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
                implicit_open = False
            if current_scene is None:
                _append_error(
                    diagnostics,
                    code="E_SPEAKER_OUTSIDE_SCENE",
                    message="Speaker found before scene.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
            seen_speaker = True
            current_speaker = _extract_speaker_label(first)
            continue

        if kinds["stage"]:
            normalized_stage: list[str] = []
            malformed = False
            for idx, raw in enumerate(block.lines):
                match = _STAGE_RE.match(raw.strip())
                if match is None:
                    _append_error(
                        diagnostics,
                        code="E_STAGE_MARKER_MALFORMED",
                        message="Malformed explicit stage direction marker.",
                        line_number=line + idx,
                        block_index=block.index,
                        act=current_act,
                        scene=current_scene,
                        speaker=current_speaker,
                        excerpt=raw.strip(),
                    )
                    malformed = True
                else:
                    normalized_stage.append(match.group(1).strip())
            if not malformed:
                _validate_token_count_consistency(
                    diagnostics,
                    normalized_readings=normalized_stage,
                    witness_labels=labels,
                    block_type="stage_direction",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    block_lines=block.lines,
                )
            if current_scene is None:
                _append_error(
                    diagnostics,
                    code="E_STAGE_OUTSIDE_SCENE",
                    message="Stage direction found before scene.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
            if implicit_open:
                _append_error(
                    diagnostics,
                    code="E_IMPLICIT_SPAN_STAGE_MIX",
                    message="Explicit stage directions inside implicit stage span are unsupported.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
            continue

        if kinds["implicit_close"]:
            for idx, raw in enumerate(block.lines):
                if _IMPLICIT_CLOSE_RE.match(raw.strip()) is None:
                    _append_error(
                        diagnostics,
                        code="E_IMPLICIT_CLOSE_MALFORMED",
                        message="Malformed implicit stage closing marker.",
                        line_number=line + idx,
                        block_index=block.index,
                        act=current_act,
                        scene=current_scene,
                        speaker=current_speaker,
                        excerpt=raw.strip(),
                    )
            if not implicit_open:
                _append_error(
                    diagnostics,
                    code="E_IMPLICIT_CLOSE_WITHOUT_OPEN",
                    message="Unexpected $$fin$$ without open implicit stage span.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
            implicit_open = False
            continue

        if kinds["implicit_open"]:
            categories: set[str] = set()
            malformed = False
            for idx, raw in enumerate(block.lines):
                stripped = raw.strip()
                match = _IMPLICIT_OPEN_RE.match(stripped)
                if match is None:
                    malformed = True
                    _append_error(
                        diagnostics,
                        code="E_IMPLICIT_OPEN_MALFORMED",
                        message="Malformed implicit stage opening marker.",
                        line_number=line + idx,
                        block_index=block.index,
                        act=current_act,
                        scene=current_scene,
                        speaker=current_speaker,
                        excerpt=stripped,
                    )
                else:
                    categories.add(match.group(1))
            if malformed:
                continue
            if len(categories) != 1:
                _append_error(
                    diagnostics,
                    code="E_IMPLICIT_OPEN_VARIATION",
                    message="Implicit stage opening marker variation between witnesses is unsupported.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
            if current_speaker is None:
                _append_error(
                    diagnostics,
                    code="E_IMPLICIT_OPEN_BEFORE_SPEAKER",
                    message="Implicit stage span opening marker found before speaker.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
            if implicit_open:
                _append_error(
                    diagnostics,
                    code="E_IMPLICIT_NESTED",
                    message="Nested implicit stage spans are unsupported.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
            implicit_open = True
            continue

        if current_speaker is None:
            _append_error(
                diagnostics,
                code="E_VERSE_WITHOUT_SPEAKER",
                message="Verse found before speaker.",
                line_number=line,
                block_index=block.index,
                act=current_act,
                scene=current_scene,
                speaker=current_speaker,
                excerpt=first,
            )
            continue

        normalized_verse: list[str] = []
        whole_line_variant_any = False
        for raw in block.lines:
            cleaned, whole_line_variant = _clean_verse_for_collation(raw)
            normalized_verse.append(cleaned)
            whole_line_variant_any = whole_line_variant_any or whole_line_variant
        if not whole_line_variant_any:
            _validate_token_count_consistency(
                diagnostics,
                normalized_readings=normalized_verse,
                witness_labels=labels,
                block_type="verse",
                line_number=line,
                block_index=block.index,
                act=current_act,
                scene=current_scene,
                speaker=current_speaker,
                block_lines=block.lines,
            )

        starts = [raw.strip().endswith("***") for raw in block.lines]
        continues = [raw.strip().startswith("***") for raw in block.lines]
        starts_any = any(starts)
        continues_any = any(continues)
        if any(raw.strip().startswith("#####") and len(raw.strip()) <= 5 for raw in block.lines):
            _append_error(
                diagnostics,
                code="E_WHOLE_LINE_VARIANT_MALFORMED",
                message="Malformed whole-line variant marker (##### requires content).",
                line_number=line,
                block_index=block.index,
                act=current_act,
                scene=current_scene,
                speaker=current_speaker,
                excerpt=first,
            )

        if continues_any and not shared_open:
            _append_warning(
                diagnostics,
                code="W_SHARED_VERSE_CONTINUE_WITHOUT_OPEN",
                message="Shared-verse continuation marker '***' used without open shared verse; treated as normal verse.",
                line_number=line,
                block_index=block.index,
                act=current_act,
                scene=current_scene,
                speaker=current_speaker,
                excerpt=first,
            )
        if starts_any and shared_open and not continues_any:
            _append_warning(
                diagnostics,
                code="W_SHARED_VERSE_REOPEN",
                message="Shared-verse opening marker '***' encountered while a shared verse is open; state will be reset.",
                line_number=line,
                block_index=block.index,
                act=current_act,
                scene=current_scene,
                speaker=current_speaker,
                excerpt=first,
            )

        if shared_open and continues_any:
            shared_carried_across_scene = False
        elif shared_open and not continues_any:
            shared_open = False
            shared_carried_across_scene = False

        if starts_any:
            shared_open = True

    if implicit_open:
        _append_error(
            diagnostics,
            code="E_IMPLICIT_SPAN_UNCLOSED",
            message="Unclosed implicit stage span at end of input.",
            line_number=None,
            block_index=None,
            act=current_act,
            scene=current_scene,
            speaker=current_speaker,
            excerpt=None,
        )
    if shared_open and shared_carried_across_scene:
        _append_warning(
            diagnostics,
            code="W_SHARED_VERSE_FORCE_CLOSE",
            message="Shared verse was force-closed at end of input after crossing a scene boundary without continuation.",
            line_number=None,
            block_index=None,
            act=current_act,
            scene=current_scene,
            speaker=current_speaker,
            excerpt=None,
        )
    if not seen_scene:
        _append_error(
            diagnostics,
            code="E_NO_SCENE",
            message="Aucune scène (###...###) n'est définie.",
            line_number=None,
            block_index=None,
            act=current_act,
            scene=current_scene,
            speaker=current_speaker,
        )
    if not seen_speaker:
        _append_error(
            diagnostics,
            code="E_NO_SPEAKER",
            message="Aucun locuteur (#...#) n'est défini.",
            line_number=None,
            block_index=None,
            act=current_act,
            scene=current_scene,
            speaker=current_speaker,
        )

    return ValidationReport(diagnostics=diagnostics)
