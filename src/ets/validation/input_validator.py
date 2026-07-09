from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from ets.characters import resolve_speaker_block
from ets.collation import token_counts_for_readings
from ets.domain import Character


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


_ACT_RE = re.compile(r"^####([^#]+?)####$")
_PROLOGUE_RE = re.compile(r"^####\s*PROLOGUE\.?\s*####$", re.IGNORECASE)
_SCENE_RE = re.compile(r"^###([^#]+?)###$")
_SPEAKER_RE = re.compile(r"^#([^#]+?)#$")
_CAST_LINE_RE = re.compile(r"^(##[^#]+##)(\s+##[^#]+##)*$")
_CAST_TOKEN_RE = re.compile(r"##([^#]*?)##")
_STAGE_RE = re.compile(r"^\*\*(?!\*)(.+?)(?<!\*)\*\*$")
_IMPLICIT_OPEN_RE = re.compile(r"^\$\$([A-Za-z][A-Za-z0-9_-]*)\$\$$")
_IMPLICIT_CLOSE_RE = re.compile(r"^\$\$fin\$\$$", re.IGNORECASE)
_STANZA_OPEN_RE = re.compile(r"^%%strophe(?:\s+(.+?))?%%$")
_STANZA_CLOSE_RE = re.compile(r"^%%fin_strophe%%$", re.IGNORECASE)
_METRICAL_PREFIX_RE = re.compile(r"^=(\d{2})=(.*)$")
_STANZA_WHOLE_LINE_VARIANT_METRICAL_RE = re.compile(r"^#####=(\d{2})=(.*)$")
_SHARED_VERSE_RE = re.compile(r"^(?:\*\*\*.+|.+\*\*\*)$")
_WHOLE_LINE_VARIANT_RE = re.compile(r"^#####\s*\S.*$")

STANZA_SUBTYPE_LINE_COUNTS = {
    "distique": 2,
    "tercet": 3,
    "quatrain": 4,
    "quintil": 5,
    "sixain": 6,
    "sizain": 6,
    "septain": 7,
    "huitain": 8,
    "neuvain": 9,
    "dizain": 10,
    "onzain": 11,
    "douzain": 12,
}


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


def _parse_stanza_open_attrs(raw: str) -> tuple[dict[str, str], str | None]:
    match = _STANZA_OPEN_RE.match(raw.strip())
    if match is None:
        return {}, "malformed"
    attrs: dict[str, str] = {}
    raw_attrs = (match.group(1) or "").strip()
    if not raw_attrs:
        return attrs, None
    for item in raw_attrs.split():
        if "=" not in item:
            return attrs, "malformed"
        key, value = item.split("=", maxsplit=1)
        if key == "type":
            return attrs, "type_forbidden"
        if key not in {"subtype", "rhyme"}:
            return attrs, key
        attrs[key] = value
    return attrs, None


def _stanza_signature(raw: str) -> tuple[str | None, str | None] | None:
    attrs, error = _parse_stanza_open_attrs(raw)
    if error is not None:
        return None
    return attrs.get("subtype"), attrs.get("rhyme")


def _read_stanza_verse_marker(raw: str) -> tuple[str | None, str | None, bool]:
    stripped = raw.strip()
    whole_line_match = _STANZA_WHOLE_LINE_VARIANT_METRICAL_RE.match(stripped)
    if whole_line_match:
        text = whole_line_match.group(2)
        return str(int(whole_line_match.group(1))), f"#####{text}", True

    match = _METRICAL_PREFIX_RE.match(stripped)
    if match is None:
        return None, None, False
    return str(int(match.group(1))), match.group(2), False


def _classify_line_marker(line: str) -> str:
    stripped = line.strip()
    if _ACT_RE.match(stripped) and not stripped.startswith("#####"):
        return "act"
    if _SCENE_RE.match(stripped) and not stripped.startswith("####"):
        return "scene"
    if _CAST_LINE_RE.match(stripped) and stripped.startswith("##") and not stripped.startswith("###"):
        return "cast"
    if _SPEAKER_RE.match(stripped) and not stripped.startswith("##"):
        return "speaker"
    if _STAGE_RE.match(stripped):
        return "stage"
    if _IMPLICIT_OPEN_RE.match(stripped):
        return "implicit_open"
    if _IMPLICIT_CLOSE_RE.match(stripped):
        return "implicit_close"
    if _STANZA_OPEN_RE.match(stripped):
        return "stanza_open"
    if _STANZA_CLOSE_RE.match(stripped):
        return "stanza_close"
    if _WHOLE_LINE_VARIANT_RE.match(stripped):
        return "whole_line_variant"
    if _SHARED_VERSE_RE.match(stripped):
        return "shared_verse"
    return "verse"


def _line_has_malformed_hash_marker(line: str) -> bool:
    stripped = line.strip()
    if "#" not in stripped:
        return False
    if stripped.startswith("#####"):
        if not _WHOLE_LINE_VARIANT_RE.match(stripped):
            return True
        content = stripped[5:].lstrip()
        return "#" in content
    if stripped.startswith("####"):
        return _ACT_RE.match(stripped) is None
    if stripped.startswith("###"):
        return _SCENE_RE.match(stripped) is None
    if stripped.startswith("##"):
        return _CAST_LINE_RE.match(stripped) is None
    if stripped.startswith("#"):
        return _SPEAKER_RE.match(stripped) is None
    # In ETS input, any '#' must belong to a valid ETS marker.
    return True


def _line_has_malformed_star_marker(line: str, *, shared_open: bool = False) -> tuple[bool, str | None]:
    stripped = line.strip()
    if "*" not in stripped:
        return False, None

    if stripped.startswith("***") or stripped.endswith("***"):
        if stripped.startswith("****") or stripped.endswith("****"):
            return True, "shared"

        is_triple_both = stripped.startswith("***") and stripped.endswith("***")
        is_hybrid_stage_shared = (
            (stripped.startswith("**") and not stripped.startswith("***") and stripped.endswith("***"))
            or (stripped.startswith("***") and stripped.endswith("**") and not stripped.endswith("***"))
        )
        if is_hybrid_stage_shared:
            return True, "stage"

        if is_triple_both:
            middle = stripped[3:-3].strip()
            if not middle:
                return True, "shared"
            if shared_open:
                return False, None
            return True, "stage"

        if _SHARED_VERSE_RE.match(stripped):
            return False, None
        return True, "shared"
    if stripped.startswith("**") or stripped.endswith("**"):
        if _STAGE_RE.match(stripped):
            return False, None
        return True, "stage"
    return False, None


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


def _append_character_speaker_warning(
    diagnostics: list[ValidationDiagnostic],
    *,
    speaker_readings: list[str],
    characters: list[Character],
    character_alias_hint: str,
    line_number: int,
    block_index: int,
    act: str | None,
    scene: str | None,
    block_lines: list[str],
) -> None:
    if not characters:
        return
    resolution = resolve_speaker_block(speaker_readings, characters)
    if resolution.status == "resolved":
        return
    code_by_status = {
        "unresolved": "W_CHARACTER_WHO_UNRESOLVED",
        "ambiguous": "W_CHARACTER_WHO_AMBIGUOUS",
        "conflict": "W_CHARACTER_WHO_CONFLICT",
    }
    forms = ", ".join(repr(form) for form in resolution.problematic_forms) or "empty speaker label"
    _append_warning(
        diagnostics,
        code=code_by_status[resolution.status],
        message=(
            f"Character authority could not safely resolve speaker form(s): {forms}. "
            f"{character_alias_hint}"
        ),
        line_number=line_number,
        block_index=block_index,
        act=act,
        scene=scene,
        speaker=speaker_readings[0] if speaker_readings else None,
        excerpt=block_lines[0].strip() if block_lines else None,
        block_type="speaker",
        block_lines=block_lines,
    )


def validate_input_text(
    text: str,
    witness_count: int,
    witness_sigla: list[str] | None = None,
    characters: list[Character] | None = None,
    character_alias_hint: str = "Complete Personnages > aliases in the configuration if this speaker should receive @who.",
) -> ValidationReport:
    diagnostics: list[ValidationDiagnostic] = []
    blocks = _split_parallel_blocks(text)
    character_table = characters or []
    labels = witness_sigla if witness_sigla is not None and len(witness_sigla) == witness_count else [
        f"W{i + 1}" for i in range(witness_count)
    ]

    current_act: str | None = None
    current_scene: str | None = None
    current_speaker: str | None = None
    implicit_open: bool = False
    stanza_open: bool = False
    stanza_subtype: str | None = None
    stanza_rhyme: str | None = None
    stanza_line_count = 0
    shared_open: bool = False
    shared_carried_across_scene: bool = False
    seen_scene = False
    seen_speaker = False
    suppress_next_verse_without_speaker = False
    in_prologue = False

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

        marker_types = {_classify_line_marker(raw) for raw in block.lines}
        non_verse_types = {kind for kind in marker_types if kind != "verse"}
        if len(non_verse_types) > 1:
            _append_error(
                diagnostics,
                code="E_MARKER_MIXED_BLOCK",
                message="Parallel block mixes incompatible marker types.",
                line_number=line,
                block_index=block.index,
                act=current_act,
                scene=current_scene,
                speaker=current_speaker,
                excerpt=first,
                block_lines=block.lines,
            )
            continue

        malformed_marker_found = False
        for idx, raw in enumerate(block.lines):
            if _line_has_malformed_hash_marker(raw):
                _append_error(
                    diagnostics,
                    code="E_HASH_MARKER_MALFORMED",
                    message="Malformed hash marker sequence.",
                    line_number=line + idx,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=raw.strip(),
                )
                malformed_marker_found = True
            malformed_star, star_kind = _line_has_malformed_star_marker(raw, shared_open=shared_open)
            if malformed_star:
                _append_error(
                    diagnostics,
                    code="E_SHARED_VERSE_MARKER_MALFORMED" if star_kind == "shared" else "E_STAGE_MARKER_MALFORMED",
                    message=(
                        "Malformed shared-verse marker."
                        if star_kind == "shared"
                        else "Malformed explicit stage direction marker."
                    ),
                    line_number=line + idx,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=raw.strip(),
                )
                malformed_marker_found = True
        if malformed_marker_found:
            continue

        kinds = {
            "act": _ACT_RE.match(first) is not None and not first.startswith("#####"),
            "scene": _SCENE_RE.match(first) is not None and not first.startswith("####"),
            "cast": _CAST_LINE_RE.match(first) is not None and first.startswith("##") and not first.startswith("###"),
            "speaker": _SPEAKER_RE.match(first) is not None and not first.startswith("##"),
            "stage": _STAGE_RE.match(first) is not None,
            "implicit_open": _IMPLICIT_OPEN_RE.match(first) is not None,
            "implicit_close": _IMPLICIT_CLOSE_RE.match(first) is not None,
            "stanza_open": _STANZA_OPEN_RE.match(first) is not None,
            "stanza_close": _STANZA_CLOSE_RE.match(first) is not None,
            "whole_line_variant": first.startswith("#####"),
        }

        if kinds["act"]:
            if stanza_open:
                _append_error(
                    diagnostics,
                    code="E_STANZA_UNCLOSED",
                    message="Unclosed stanza before act boundary.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
                stanza_open = False
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
            in_prologue = _PROLOGUE_RE.match(first) is not None
            current_act = "PROLOGUE" if in_prologue else _extract_act_label(first)
            current_scene = None
            current_speaker = None
            shared_open = False
            shared_carried_across_scene = False
            continue

        if kinds["scene"]:
            if stanza_open:
                _append_error(
                    diagnostics,
                    code="E_STANZA_UNCLOSED",
                    message="Unclosed stanza before scene boundary.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
                stanza_open = False
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
            if stanza_open:
                _append_error(
                    diagnostics,
                    code="E_STANZA_UNCLOSED",
                    message="Unclosed stanza before cast block.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
                stanza_open = False
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
            cast_tokens_per_line = [[part.strip() for part in _CAST_TOKEN_RE.findall(raw)] for raw in block.lines]
            cast_is_single_token = all(len(tokens) == 1 for tokens in cast_tokens_per_line)
            if (
                cast_is_single_token
                and current_scene is not None
                and block.index + 1 < len(blocks)
            ):
                next_block = blocks[block.index + 1]
                next_types = {_classify_line_marker(raw) for raw in next_block.lines}
                if next_types == {"verse"}:
                    _append_error(
                        diagnostics,
                        code="E_SPEAKER_MARKER_TOO_MANY_HASHES",
                        message="Cette ligne ressemble a un locuteur encode avec deux dieses. Utilisez #NOM# et non ##NOM##.",
                        line_number=line,
                        block_index=block.index,
                        act=current_act,
                        scene=current_scene,
                        speaker=current_speaker,
                        excerpt=first,
                        block_lines=block.lines,
                    )
                    if current_speaker is None:
                        suppress_next_verse_without_speaker = True
                    # Avoid silently attaching following verses to the previous speaker.
                    current_speaker = None
            continue

        if kinds["speaker"]:
            if stanza_open:
                _append_error(
                    diagnostics,
                    code="E_STANZA_UNCLOSED",
                    message="Unclosed stanza before speaker change.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
                stanza_open = False
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
                _append_character_speaker_warning(
                    diagnostics,
                    speaker_readings=normalized_speaker,
                    characters=character_table,
                    character_alias_hint=character_alias_hint,
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
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
            if current_scene is None and not in_prologue:
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
            if stanza_open:
                _append_error(
                    diagnostics,
                    code="E_STANZA_UNCLOSED",
                    message="Unclosed stanza before explicit stage direction.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
                stanza_open = False
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

        if kinds["stanza_close"]:
            for idx, raw in enumerate(block.lines):
                if _STANZA_CLOSE_RE.match(raw.strip()) is None:
                    _append_error(
                        diagnostics,
                        code="E_STANZA_CLOSE_MALFORMED",
                        message="Malformed stanza closing marker.",
                        line_number=line + idx,
                        block_index=block.index,
                        act=current_act,
                        scene=current_scene,
                        speaker=current_speaker,
                        excerpt=raw.strip(),
                    )
            if not stanza_open:
                _append_error(
                    diagnostics,
                    code="E_STANZA_CLOSE_WITHOUT_OPEN",
                    message="Unexpected %%fin_strophe%% without open stanza.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
            else:
                if stanza_subtype:
                    expected = STANZA_SUBTYPE_LINE_COUNTS.get(stanza_subtype)
                    if expected is not None and stanza_line_count != expected:
                        _append_error(
                            diagnostics,
                            code="E_STANZA_SUBTYPE_COUNT_MISMATCH",
                            message=f"Stanza subtype {stanza_subtype!r} expects {expected} verse lines, got {stanza_line_count}.",
                            line_number=line,
                            block_index=block.index,
                            act=current_act,
                            scene=current_scene,
                            speaker=current_speaker,
                            excerpt=first,
                        )
                if stanza_rhyme and len(stanza_rhyme) != stanza_line_count:
                    _append_error(
                        diagnostics,
                        code="E_STANZA_RHYME_COUNT_MISMATCH",
                        message=f"Stanza rhyme scheme expects {len(stanza_rhyme)} verse lines, got {stanza_line_count}.",
                        line_number=line,
                        block_index=block.index,
                        act=current_act,
                        scene=current_scene,
                        speaker=current_speaker,
                        excerpt=first,
                    )
            stanza_open = False
            stanza_subtype = None
            stanza_rhyme = None
            stanza_line_count = 0
            continue

        if kinds["stanza_open"]:
            signatures: set[tuple[str | None, str | None]] = set()
            malformed = False
            for idx, raw in enumerate(block.lines):
                attrs, error = _parse_stanza_open_attrs(raw)
                if error == "type_forbidden":
                    _append_error(
                        diagnostics,
                        code="E_STANZA_TYPE_ATTRIBUTE_FORBIDDEN",
                        message="Stanza marker must use subtype=..., not type=....",
                        line_number=line + idx,
                        block_index=block.index,
                        act=current_act,
                        scene=current_scene,
                        speaker=current_speaker,
                        excerpt=raw.strip(),
                    )
                    malformed = True
                elif error is not None:
                    _append_error(
                        diagnostics,
                        code="E_STANZA_UNKNOWN_ATTRIBUTE" if error != "malformed" else "E_STANZA_OPEN_MALFORMED",
                        message=(
                            f"Unknown stanza attribute: {error}."
                            if error != "malformed"
                            else "Malformed stanza opening marker."
                        ),
                        line_number=line + idx,
                        block_index=block.index,
                        act=current_act,
                        scene=current_scene,
                        speaker=current_speaker,
                        excerpt=raw.strip(),
                    )
                    malformed = True
                else:
                    signatures.add((attrs.get("subtype"), attrs.get("rhyme")))
            if malformed:
                continue
            if len(signatures) != 1:
                _append_error(
                    diagnostics,
                    code="E_STANZA_OPEN_VARIATION",
                    message="Stanza opening marker variation between witnesses is unsupported.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                    block_lines=block.lines,
                )
            if current_speaker is None:
                _append_error(
                    diagnostics,
                    code="E_STANZA_OPEN_BEFORE_SPEAKER",
                    message="Stanza opening marker found before speaker.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
            if stanza_open:
                _append_error(
                    diagnostics,
                    code="E_STANZA_NESTED",
                    message="Nested stanzas are unsupported.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
            signature = next(iter(signatures)) if signatures else (None, None)
            stanza_open = True
            stanza_subtype, stanza_rhyme = signature
            stanza_line_count = 0
            continue

        if kinds["implicit_close"]:
            if stanza_open:
                _append_error(
                    diagnostics,
                    code="E_STANZA_UNCLOSED",
                    message="Unclosed stanza before implicit stage closing marker.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
                stanza_open = False
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
            if stanza_open:
                _append_error(
                    diagnostics,
                    code="E_STANZA_UNCLOSED",
                    message="Unclosed stanza before implicit stage opening marker.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
                stanza_open = False
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

        if current_speaker is None and in_prologue:
            _validate_token_count_consistency(
                diagnostics,
                normalized_readings=[raw.strip() for raw in block.lines],
                witness_labels=labels,
                block_type="stage",
                line_number=line,
                block_index=block.index,
                act=current_act,
                scene=current_scene,
                speaker=current_speaker,
                block_lines=block.lines,
            )
            continue

        if current_speaker is None:
            if any(_METRICAL_PREFIX_RE.match(raw.strip()) for raw in block.lines):
                _append_error(
                    diagnostics,
                    code="E_METRICAL_MARKER_OUTSIDE_STANZA",
                    message="Metrical marker =nn= is only allowed inside a stanza.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                )
            if not suppress_next_verse_without_speaker:
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
            suppress_next_verse_without_speaker = False
            continue
        suppress_next_verse_without_speaker = False

        verse_block_lines = block.lines
        if stanza_open:
            meters: list[str] = []
            stripped_lines: list[str] = []
            for idx, raw in enumerate(block.lines):
                raw_meter, stripped_line, whole_line_variant = _read_stanza_verse_marker(raw)
                if raw_meter is None or stripped_line is None:
                    _append_error(
                        diagnostics,
                        code="E_STANZA_VERSE_WITHOUT_MET",
                        message="Verse inside stanza requires a metrical prefix =02= to =12=.",
                        line_number=line + idx,
                        block_index=block.index,
                        act=current_act,
                        scene=current_scene,
                        speaker=current_speaker,
                        excerpt=raw.strip(),
                    )
                    continue
                if whole_line_variant and not stripped_line[5:].strip():
                    _append_error(
                        diagnostics,
                        code="E_WHOLE_LINE_VARIANT_MALFORMED",
                        message="Malformed whole-line variant marker (#####=nn= requires content or explicit lacuna).",
                        line_number=line + idx,
                        block_index=block.index,
                        act=current_act,
                        scene=current_scene,
                        speaker=current_speaker,
                        excerpt=raw.strip(),
                    )
                raw_value = int(raw_meter)
                if raw_value < 2 or raw_value > 12:
                    _append_error(
                        diagnostics,
                        code="E_METRICAL_VALUE_OUT_OF_RANGE",
                        message="Metrical value must be between 02 and 12.",
                        line_number=line + idx,
                        block_index=block.index,
                        act=current_act,
                        scene=current_scene,
                        speaker=current_speaker,
                        excerpt=raw.strip(),
                    )
                meters.append(raw_meter)
                stripped_lines.append(stripped_line)
            if len(meters) == witness_count and len(set(meters)) != 1:
                _append_error(
                    diagnostics,
                    code="E_STANZA_METRICAL_VALUE_VARIATION",
                    message="Metrical values vary between witnesses of the same stanza verse block.",
                    line_number=line,
                    block_index=block.index,
                    act=current_act,
                    scene=current_scene,
                    speaker=current_speaker,
                    excerpt=first,
                    witness_labels=labels,
                    block_lines=block.lines,
                )
            if len(stripped_lines) == witness_count:
                verse_block_lines = stripped_lines
            stanza_line_count += 1
        elif any(_METRICAL_PREFIX_RE.match(raw.strip()) for raw in block.lines):
            _append_error(
                diagnostics,
                code="E_METRICAL_MARKER_OUTSIDE_STANZA",
                message="Metrical marker =nn= is only allowed inside a stanza.",
                line_number=line,
                block_index=block.index,
                act=current_act,
                scene=current_scene,
                speaker=current_speaker,
                excerpt=first,
                block_lines=block.lines,
            )
            continue

        normalized_verse: list[str] = []
        whole_line_variant_any = False
        for raw in verse_block_lines:
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

        starts = [raw.strip().endswith("***") for raw in verse_block_lines]
        continues = [raw.strip().startswith("***") for raw in verse_block_lines]
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
    if stanza_open:
        _append_error(
            diagnostics,
            code="E_STANZA_UNCLOSED",
            message="Unclosed stanza at end of input.",
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
