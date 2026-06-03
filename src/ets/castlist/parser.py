from __future__ import annotations

from dataclasses import dataclass, field
import re

from ets.domain import CastEntry, DramatisPersonae, EditionConfig
from ets.validation import DiagnosticLevel, InputValidationError, ValidationDiagnostic


_CAST_ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")
_MARKER_RE = re.compile(r"^%%(.+?)%%$")
_CAST_OPEN_RE = re.compile(r"^%%cast(?:\s+(.+?))?%%$")
_ATTR_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*")
_ALLOWED_CAST_ATTRS = {"id", "role", "desc", "aliases"}


@dataclass
class _OpenBlock:
    kind: str
    line_number: int
    block_index: int
    attrs: dict[str, str] = field(default_factory=dict)
    readings: list[str] = field(default_factory=list)
    attr_errors: bool = False


def _error(
    diagnostics: list[ValidationDiagnostic],
    *,
    code: str,
    message: str,
    line_number: int | None,
    block_index: int | None,
    excerpt: str | None = None,
    block_lines: list[str] | None = None,
) -> None:
    diagnostics.append(
        ValidationDiagnostic(
            level=DiagnosticLevel.ERROR,
            code=code,
            message=message,
            line_number=line_number,
            block_index=block_index,
            excerpt=excerpt,
            block_type="castlist",
            block_lines=block_lines,
        )
    )


def _warning(
    diagnostics: list[ValidationDiagnostic],
    *,
    code: str,
    message: str,
    line_number: int | None,
    block_index: int | None,
    excerpt: str | None = None,
) -> None:
    diagnostics.append(
        ValidationDiagnostic(
            level=DiagnosticLevel.WARNING,
            code=code,
            message=message,
            line_number=line_number,
            block_index=block_index,
            excerpt=excerpt,
            block_type="castlist",
        )
    )


def _parse_attrs(
    raw: str,
    diagnostics: list[ValidationDiagnostic],
    *,
    line_number: int,
    block_index: int,
) -> tuple[dict[str, str], bool]:
    attrs: dict[str, str] = {}
    position = 0
    has_errors = False
    while position < len(raw):
        while position < len(raw) and raw[position].isspace():
            position += 1
        if position >= len(raw):
            break

        name_match = _ATTR_NAME_RE.match(raw, position)
        if name_match is None:
            _error(
                diagnostics,
                code="E_CAST_ATTR_MALFORMED",
                message="Malformed cast attribute.",
                line_number=line_number,
                block_index=block_index,
                excerpt=raw[position:].strip(),
            )
            return attrs, True

        name = name_match.group(0)
        position = name_match.end()
        if name not in _ALLOWED_CAST_ATTRS:
            _error(
                diagnostics,
                code="E_CAST_ATTR_UNKNOWN",
                message=f"Unknown cast attribute {name!r}.",
                line_number=line_number,
                block_index=block_index,
                excerpt=name,
            )
            has_errors = True

        if position >= len(raw) or raw[position] != "=":
            _error(
                diagnostics,
                code="E_CAST_ATTR_MALFORMED",
                message=f"Malformed cast attribute {name!r}: missing '='.",
                line_number=line_number,
                block_index=block_index,
                excerpt=name,
            )
            return attrs, True
        position += 1

        if position < len(raw) and raw[position] == '"':
            position += 1
            end_quote = raw.find('"', position)
            if end_quote < 0:
                _error(
                    diagnostics,
                    code="E_CAST_ATTR_MALFORMED",
                    message=f"Malformed cast attribute {name!r}: unclosed quote.",
                    line_number=line_number,
                    block_index=block_index,
                    excerpt=name,
                )
                return attrs, True
            attrs[name] = raw[position:end_quote]
            position = end_quote + 1
            if position < len(raw) and not raw[position].isspace():
                _error(
                    diagnostics,
                    code="E_CAST_ATTR_MALFORMED",
                    message=f"Malformed cast attribute {name!r}: expected whitespace after value.",
                    line_number=line_number,
                    block_index=block_index,
                    excerpt=name,
                )
                return attrs, True
            continue

        value_start = position
        while position < len(raw) and not raw[position].isspace():
            position += 1
        value = raw[value_start:position]
        if name != "id":
            _error(
                diagnostics,
                code="E_CAST_ATTR_MALFORMED",
                message=f"Cast attribute {name!r} must use straight double quotes.",
                line_number=line_number,
                block_index=block_index,
                excerpt=f"{name}={value}",
            )
            has_errors = True
            continue
        attrs[name] = value

    return attrs, has_errors


def _is_marker(line: str) -> bool:
    return _MARKER_RE.match(line.strip()) is not None


def _is_open_marker(line: str) -> bool:
    stripped = line.strip()
    return stripped in {"%%head%%", "%%setting%%", "%%castlist%%"} or _CAST_OPEN_RE.match(stripped) is not None


def _expected_close(kind: str) -> str:
    return {
        "head": "%%fin_head%%",
        "setting": "%%fin_setting%%",
        "cast": "%%fin_cast%%",
    }[kind]


def _split_aliases(raw: str) -> list[str]:
    return [item.strip() for item in raw.split("|") if item.strip()]


def _check_reading_count(
    diagnostics: list[ValidationDiagnostic],
    *,
    code: str,
    block: _OpenBlock,
    witness_count: int,
) -> None:
    if len(block.readings) == witness_count:
        return
    _error(
        diagnostics,
        code=code,
        message=(
            f"Dramatis personae {block.kind} block expects {witness_count} non-empty readings, "
            f"got {len(block.readings)}."
        ),
        line_number=block.line_number,
        block_index=block.block_index,
        excerpt=f"%%{block.kind}%%",
        block_lines=block.readings,
    )


def _finish_block(
    *,
    block: _OpenBlock,
    witness_count: int,
    diagnostics: list[ValidationDiagnostic],
    head_readings: list[str],
    entries: list[CastEntry],
    setting_readings: list[str],
    seen_ids: set[str],
) -> None:
    if block.kind == "head":
        _check_reading_count(
            diagnostics,
            code="E_CAST_HEAD_READING_COUNT_MISMATCH",
            block=block,
            witness_count=witness_count,
        )
        head_readings[:] = block.readings
        return

    if block.kind == "setting":
        _check_reading_count(
            diagnostics,
            code="E_CAST_SETTING_READING_COUNT_MISMATCH",
            block=block,
            witness_count=witness_count,
        )
        setting_readings[:] = block.readings
        return

    character_id = block.attrs.get("id", "").strip()
    role = block.attrs.get("role", "").strip()
    if not block.attr_errors:
        if not character_id:
            _error(
                diagnostics,
                code="E_CAST_ID_MISSING",
                message="Dramatis personae cast entry is missing required id.",
                line_number=block.line_number,
                block_index=block.block_index,
                excerpt="%%cast%%",
            )
        elif not _CAST_ID_RE.fullmatch(character_id):
            _error(
                diagnostics,
                code="E_CAST_ID_INVALID",
                message=f"Dramatis personae cast id {character_id!r} is not XML-compatible.",
                line_number=block.line_number,
                block_index=block.block_index,
                excerpt=character_id,
            )
        elif character_id in seen_ids:
            _error(
                diagnostics,
                code="E_CAST_ID_DUPLICATE",
                message=f"Dramatis personae cast id {character_id!r} is duplicated.",
                line_number=block.line_number,
                block_index=block.block_index,
                excerpt=character_id,
            )
        else:
            seen_ids.add(character_id)

        if not role:
            _error(
                diagnostics,
                code="E_CAST_ROLE_MISSING",
                message="Dramatis personae cast entry is missing required role.",
                line_number=block.line_number,
                block_index=block.block_index,
                excerpt=character_id or "%%cast%%",
            )

    _check_reading_count(
        diagnostics,
        code="E_CAST_READING_COUNT_MISMATCH",
        block=block,
        witness_count=witness_count,
    )

    desc = block.attrs.get("desc", "").strip()
    aliases = _split_aliases(block.attrs.get("aliases", ""))
    if "desc" not in block.attrs:
        _warning(
            diagnostics,
            code="W_CAST_DESC_EMPTY",
            message=f"Dramatis personae cast entry {character_id or '<missing id>'} has no desc attribute.",
            line_number=block.line_number,
            block_index=block.block_index,
            excerpt=character_id or None,
        )
    if "aliases" not in block.attrs:
        _warning(
            diagnostics,
            code="W_CAST_ALIASES_EMPTY",
            message=f"Dramatis personae cast entry {character_id or '<missing id>'} has no aliases attribute.",
            line_number=block.line_number,
            block_index=block.block_index,
            excerpt=character_id or None,
        )

    entries.append(
        CastEntry(
            id=character_id,
            role=role,
            desc=desc,
            aliases=aliases,
            readings=block.readings,
            block_index=block.block_index,
            line_number=block.line_number,
        )
    )


def _parse_castlist(text: str, witness_count: int) -> tuple[DramatisPersonae, list[ValidationDiagnostic]]:
    diagnostics: list[ValidationDiagnostic] = []
    head_readings: list[str] = []
    entries: list[CastEntry] = []
    setting_readings: list[str] = []
    seen_ids: set[str] = set()
    opened = False
    closed = False
    head_seen = False
    setting_seen = False
    current: _OpenBlock | None = None
    marker_index = -1

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.rstrip("\r")
        stripped = line.strip()
        if not stripped:
            continue

        if not opened:
            if stripped == "%%castlist%%":
                opened = True
                marker_index += 1
            else:
                _error(
                    diagnostics,
                    code="E_CASTLIST_CONTENT_BEFORE_OPEN",
                    message="Non-empty content is not allowed before %%castlist%%.",
                    line_number=line_number,
                    block_index=None,
                    excerpt=stripped,
                )
            continue

        if closed:
            _error(
                diagnostics,
                code="E_CASTLIST_UNKNOWN_MARKER",
                message="Unexpected content after %%fin_castlist%%.",
                line_number=line_number,
                block_index=marker_index,
                excerpt=stripped,
            )
            continue

        if current is not None:
            if stripped == _expected_close(current.kind):
                _finish_block(
                    block=current,
                    witness_count=witness_count,
                    diagnostics=diagnostics,
                    head_readings=head_readings,
                    entries=entries,
                    setting_readings=setting_readings,
                    seen_ids=seen_ids,
                )
                current = None
                continue
            if _is_open_marker(stripped):
                _error(
                    diagnostics,
                    code="E_CASTLIST_NESTED_BLOCK",
                    message="Nested dramatis personae blocks are not allowed.",
                    line_number=line_number,
                    block_index=current.block_index,
                    excerpt=stripped,
                )
                continue
            if _is_marker(stripped):
                _error(
                    diagnostics,
                    code="E_CASTLIST_UNKNOWN_MARKER",
                    message="Unexpected marker inside dramatis personae block.",
                    line_number=line_number,
                    block_index=current.block_index,
                    excerpt=stripped,
                )
                continue
            current.readings.append(line)
            continue

        if stripped == "%%fin_castlist%%":
            closed = True
            marker_index += 1
            continue

        if stripped == "%%head%%":
            marker_index += 1
            if head_seen:
                _error(
                    diagnostics,
                    code="E_CASTLIST_DUPLICATE_HEAD",
                    message="Dramatis personae file must not contain multiple head blocks.",
                    line_number=line_number,
                    block_index=marker_index,
                    excerpt=stripped,
                )
            head_seen = True
            current = _OpenBlock(kind="head", line_number=line_number, block_index=marker_index)
            continue

        if stripped == "%%setting%%":
            marker_index += 1
            if setting_seen:
                _error(
                    diagnostics,
                    code="E_CASTLIST_DUPLICATE_SETTING",
                    message="Dramatis personae file must not contain multiple setting blocks.",
                    line_number=line_number,
                    block_index=marker_index,
                    excerpt=stripped,
                )
            setting_seen = True
            current = _OpenBlock(kind="setting", line_number=line_number, block_index=marker_index)
            continue

        cast_match = _CAST_OPEN_RE.match(stripped)
        if cast_match is not None:
            marker_index += 1
            attrs, attr_errors = _parse_attrs(
                cast_match.group(1) or "",
                diagnostics,
                line_number=line_number,
                block_index=marker_index,
            )
            current = _OpenBlock(
                kind="cast",
                line_number=line_number,
                block_index=marker_index,
                attrs=attrs,
                attr_errors=attr_errors,
            )
            continue

        _error(
            diagnostics,
            code="E_CASTLIST_UNKNOWN_MARKER",
            message="Unknown dramatis personae marker or content outside a block.",
            line_number=line_number,
            block_index=marker_index,
            excerpt=stripped,
        )

    if not opened:
        _error(
            diagnostics,
            code="E_CASTLIST_MISSING_OPEN",
            message="Dramatis personae file must start with %%castlist%%.",
            line_number=None,
            block_index=None,
        )
    if current is not None:
        _error(
            diagnostics,
            code="E_CASTLIST_BLOCK_UNCLOSED",
            message=f"Dramatis personae {current.kind} block is not explicitly closed.",
            line_number=current.line_number,
            block_index=current.block_index,
            excerpt=f"%%{current.kind}%%",
            block_lines=current.readings,
        )
    if opened and not closed:
        _error(
            diagnostics,
            code="E_CASTLIST_MISSING_CLOSE",
            message="Dramatis personae file must end with %%fin_castlist%%.",
            line_number=None,
            block_index=None,
        )
    if opened and not entries:
        _error(
            diagnostics,
            code="E_CASTLIST_NO_CAST_ENTRY",
            message="Dramatis personae file must contain at least one cast entry.",
            line_number=None,
            block_index=None,
        )

    return DramatisPersonae(
        head_readings=head_readings,
        entries=entries,
        setting_readings=setting_readings,
    ), diagnostics


def parse_castlist_text(text: str, config: EditionConfig) -> DramatisPersonae:
    dramatis_personae, diagnostics = _parse_castlist(text, len(config.witnesses))
    errors = [diagnostic for diagnostic in diagnostics if diagnostic.level == DiagnosticLevel.ERROR]
    if errors:
        raise InputValidationError(errors)
    return dramatis_personae
