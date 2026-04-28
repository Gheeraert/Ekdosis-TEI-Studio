from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any

from ets.collation import collate_play
from ets.domain import (
    ApparatusLine,
    CollatedImplicitStageSpan,
    CollatedLine,
    CollatedPlay,
    CollatedReading,
    CollatedStageDirection,
    CollatedText,
    EditionConfig,
    LiteralLine,
    LiteralTokenSegment,
    TokenCollatedLine,
    Witness,
)
from ets.domain import ApparatusTokenSegment
from ets.parser import parse_play
from ets.validation import DiagnosticLevel, validate_input_text


template_ekdosis_preamble = r"""
\documentclass{book}
\usepackage[main=french, spanish, latin]{babel}
\usepackage[T1]{fontenc}
\usepackage{fontspec}
\usepackage{csquotes}
\usepackage[teiexport, divs=ekdosis, poetry=verse]{ekdosis}
\usepackage{setspace}
\usepackage{lettrine}
\usepackage{hyperref}
\usepackage{zref-user,zref-abspage}

\singlespacing
\DeclareApparatus{default}

\newenvironment{speech}{\par}{\par}
\newcommand{\speaker}[1]{\vspace{1em}\large\centering\textsc{#1}\par}
\newcommand{\didas}[1]{\par\vspace{0.5em}\begin{center}\textit{#1}\end{center}\vspace{0.5em}}
\newcommand{\stage}[1]{\par\vspace{1em}\begin{center}\Large\textsc{#1}\end{center}\vspace{1em}}
\newcommand{\vnum}[2]{\linelabel{v#1}#2\par}

\SetLineation{vmodulo=5}
\SetLineation{lineation=none}
"""

template_ekdosis_debut_doc = r"""
\begin{document}
\begin{ekdosis}
"""

template_ekdosis_fin_doc = r"""
\end{ekdosis}
\end{document}
"""

_ITALIC_RE = re.compile(r"_([^_\n]+)_")
_TILDE_RUN_RE = re.compile(r"[~\u00A0]+")
_TILDE_PLACEHOLDER_RE = re.compile(r"\[\[ETSTILDE(\d+)]]")
_ITALIC_MARKER = "\uE000"
_DICT_SIGLUM_KEYS = ("siglum", "abbr", "id", "witness")
_DICT_YEAR_KEYS = ("year", "date")
_DICT_DESC_KEYS = ("description", "desc", "label", "note")
_DICT_TITLE_KEYS = ("title", "titre", "Titre de la piece", "Titre de la pièce")
_DICT_AUTHOR_KEYS = ("author", "auteur", "Auteur")
_DICT_EDITOR_KEYS = ("editor", "editeur", "éditeur")


@dataclass(frozen=True)
class EkdosisMetadata:
    title: str = "Titre non renseigne"
    author: str = "Auteur inconnu"
    editor: str = "Edition critique"


@dataclass(frozen=True)
class EkdosisWitness:
    siglum: str
    year: str = ""
    description: str = ""


@dataclass(frozen=True)
class EkdosisResult:
    body: str
    full_document: str
    diagnostics: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class EkdosisGenerationError(ValueError):
    def __init__(self, message: str, *, diagnostics: list[str] | None = None, warnings: list[str] | None = None) -> None:
        self.diagnostics = diagnostics or []
        self.warnings = warnings or []
        super().__init__(message)


WitnessLike = Witness | EkdosisWitness | dict[str, Any] | str


def _pick(mapping: dict[str, Any], keys: tuple[str, ...], default: str = "") -> str:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return str(mapping[key]).strip()
    return default


def _normalize_metadata(metadata: EkdosisMetadata | dict[str, Any] | None) -> EkdosisMetadata:
    if metadata is None:
        return EkdosisMetadata()
    if isinstance(metadata, EkdosisMetadata):
        return metadata
    title = _pick(metadata, _DICT_TITLE_KEYS, default="Titre non renseigne")
    author = _pick(metadata, _DICT_AUTHOR_KEYS, default="Auteur inconnu")
    editor = _pick(metadata, _DICT_EDITOR_KEYS, default="Edition critique")
    return EkdosisMetadata(title=title or "Titre non renseigne", author=author or "Auteur inconnu", editor=editor or "Edition critique")


def _normalize_witnesses(witnesses: list[WitnessLike]) -> tuple[list[EkdosisWitness], list[str]]:
    normalized: list[EkdosisWitness] = []
    warnings: list[str] = []

    if not witnesses:
        raise EkdosisGenerationError("At least one witness is required for Ekdosis generation.")

    for index, witness in enumerate(witnesses):
        if isinstance(witness, EkdosisWitness):
            current = witness
        elif isinstance(witness, Witness):
            current = EkdosisWitness(siglum=witness.siglum.strip(), year=witness.year.strip(), description=witness.description.strip())
        elif isinstance(witness, dict):
            current = EkdosisWitness(
                siglum=_pick(witness, _DICT_SIGLUM_KEYS),
                year=_pick(witness, _DICT_YEAR_KEYS),
                description=_pick(witness, _DICT_DESC_KEYS),
            )
        elif isinstance(witness, str):
            current = EkdosisWitness(siglum=witness.strip())
        else:
            raise EkdosisGenerationError(f"Unsupported witness type at index {index}: {type(witness)!r}")

        if not current.siglum:
            raise EkdosisGenerationError(f"Witness at index {index} has no siglum/abbr.")
        normalized.append(current)

    sigla = [w.siglum for w in normalized]
    if len(set(sigla)) != len(sigla):
        raise EkdosisGenerationError("Witness sigla must be unique.")

    for witness in normalized:
        if not witness.year:
            warnings.append(f"Witness '{witness.siglum}' has no year metadata; a minimal \\DeclareWitness entry was generated.")
        if not witness.description:
            warnings.append(f"Witness '{witness.siglum}' has no description metadata; a minimal \\DeclareWitness entry was generated.")
    return normalized, warnings


def _resolve_reference_index(reference_witness: str | int | None, witnesses: list[EkdosisWitness]) -> int:
    if reference_witness is None:
        return 0

    if isinstance(reference_witness, int):
        if 0 <= reference_witness < len(witnesses):
            return reference_witness
        raise EkdosisGenerationError(
            f"reference_witness index out of range: {reference_witness} (expected 0..{len(witnesses) - 1})."
        )

    raw = str(reference_witness).strip()
    if not raw:
        return 0

    for idx, witness in enumerate(witnesses):
        if raw == witness.siglum or raw.lower() == witness.siglum.lower():
            return idx

    try:
        maybe_index = int(raw)
    except ValueError as exc:
        raise EkdosisGenerationError(f"Unknown reference witness '{reference_witness}'.") from exc

    if 0 <= maybe_index < len(witnesses):
        return maybe_index
    if 1 <= maybe_index <= len(witnesses):
        return maybe_index - 1
    raise EkdosisGenerationError(f"reference_witness value out of range: {reference_witness}")


def _format_validation_diagnostic(diagnostic: Any) -> str:
    location: list[str] = []
    line_number = getattr(diagnostic, "line_number", None)
    block_index = getattr(diagnostic, "block_index", None)
    if line_number is not None:
        location.append(f"line={line_number}")
    if block_index is not None:
        location.append(f"block={block_index}")
    suffix = f" ({', '.join(location)})" if location else ""
    return f"{diagnostic.level.value} {diagnostic.code}: {diagnostic.message}{suffix}"


def _escape_plain_text(text: str) -> str:
    text = _TILDE_PLACEHOLDER_RE.sub(lambda match: "~" * int(match.group(1)), text)
    escaped = (
        text.replace("&", r"\&")
        .replace("%", r"\%")
        .replace("$", r"\$")
        .replace("#", r"\#")
        .replace("_", r"\_")
        .replace("{", r"\{")
        .replace("}", r"\}")
    )

    def _replace_tildes(match: re.Match[str]) -> str:
        count = len(match.group(0))
        if count == 1:
            return "~"
        if count == 2:
            return r"\enspace"
        if count == 3:
            return r"\quad"
        if count == 4:
            return r"\qquad"
        return rf"\hspace*{{{count}em}}"

    return _TILDE_RUN_RE.sub(_replace_tildes, escaped)


def _escape_ekdosis_text_with_state(text: str, italic_open: bool) -> tuple[str, bool]:
    parts = text.split(_ITALIC_MARKER)
    rendered: list[str] = []
    for index, part in enumerate(parts):
        rendered.append(_escape_plain_text(part))
        if index == len(parts) - 1:
            continue
        if italic_open:
            rendered.append("}")
        else:
            rendered.append(r"\textit{")
        italic_open = not italic_open
    return "".join(rendered), italic_open


def escape_ekdosis_text(text: str) -> str:
    chunks: list[str] = []
    cursor = 0
    for match in _ITALIC_RE.finditer(text):
        chunks.append(text[cursor:match.start()])
        chunks.append(f"{_ITALIC_MARKER}{match.group(1)}{_ITALIC_MARKER}")
        cursor = match.end()
    chunks.append(text[cursor:])
    rendered, italic_open = _escape_ekdosis_text_with_state("".join(chunks), italic_open=False)
    if italic_open:
        rendered += "}"
    return rendered


def _render_collated_reading_macro(tag: str, reading: CollatedReading, italic_open: bool) -> tuple[str, bool]:
    sigla = ", ".join(reading.witness_sigla)
    content, italic_open = _escape_ekdosis_text_with_state(reading.text, italic_open=italic_open)
    return rf"  \{tag}[wit={{{sigla}}}]{{{content}}}", italic_open


def _render_collated_text(text: CollatedText) -> str:
    rendered: list[str] = []
    italic_open = False
    for segment in text.segments:
        if isinstance(segment, LiteralTokenSegment):
            content, italic_open = _escape_ekdosis_text_with_state(segment.text, italic_open=italic_open)
            rendered.append(content)
            continue
        if isinstance(segment, ApparatusTokenSegment):
            lines = [r"\app{"]
            lemma, italic_open = _render_collated_reading_macro("lem", segment.lemma, italic_open=italic_open)
            lines.append(lemma)
            for reading in segment.readings:
                rdg, italic_open = _render_collated_reading_macro("rdg", reading, italic_open=italic_open)
                lines.append(rdg)
            lines.append("}")
            rendered.append("\n".join(lines))
    if italic_open:
        rendered.append("}")
    return "".join(rendered)


def _render_line_text(line: CollatedLine) -> str:
    if isinstance(line, TokenCollatedLine):
        return _render_collated_text(line.text)
    if isinstance(line, LiteralLine):
        return escape_ekdosis_text(line.text)
    if isinstance(line, ApparatusLine):
        parts = [r"\app{", _render_collated_reading_macro("lem", line.lemma)]
        for reading in line.readings:
            parts.append(_render_collated_reading_macro("rdg", reading))
        parts.append("}")
        return "\n".join(parts)
    raise TypeError(f"Unsupported collated line type: {type(line)!r}")


def _offset_line_number(number: str, offset: int) -> str:
    if offset == 0:
        return number
    head, sep, tail = number.partition(".")
    if not head.isdigit():
        return number
    updated = str(int(head) + offset)
    if sep:
        return f"{updated}.{tail}"
    return updated


def _render_verse_line(line: CollatedLine, *, line_offset: int) -> str:
    rendered_text = _render_line_text(line)
    updated_number = _offset_line_number(line.number, line_offset)
    return "\n".join(
        [
            rf"\vnum{{{updated_number}}}{{",
            f"{rendered_text}\\\\",
            "}",
        ]
    )


def _render_body(collated_play: CollatedPlay, *, line_offset: int, warnings: list[str]) -> str:
    lines: list[str] = []
    implicit_categories_warned: set[str] = set()

    for act_index, act in enumerate(collated_play.acts, start=1):
        act_head = _render_collated_text(act.head).strip()
        lines.append(rf"\ekddiv{{type=act, n={act_index}, depth=2}}")
        if act_head:
            lines.append(rf"\stage{{{act_head}}}")

        for scene_index, scene in enumerate(act.scenes, start=1):
            scene_head = _render_collated_text(scene.head).strip()
            lines.append(rf"\ekddiv{{type=scene, n={scene_index}, depth=3}}")
            if scene_head:
                lines.append(rf"\stage{{{scene_head}}}")
            if scene.cast is not None:
                lines.append(rf"\stage{{{_render_collated_text(scene.cast).strip()}}}")
            for stage in scene.stage_directions:
                lines.append(rf"\didas{{{_render_collated_text(stage.text).strip()}}}")

            for speech in scene.speeches:
                speaker = _render_collated_text(speech.speaker).strip()
                lines.append(r"\begin{speech}")
                lines.append(rf"\speaker{{{speaker}}}")
                lines.append(r"\begin{ekdverse}")

                for element in speech.elements:
                    if isinstance(element, CollatedStageDirection):
                        lines.append(rf"\didas{{{_render_collated_text(element.text).strip()}}}")
                        continue
                    if isinstance(element, CollatedImplicitStageSpan):
                        if element.category not in implicit_categories_warned:
                            warnings.append(
                                "Implicit stage marker '$$TYPE$$...$$fin$$' was preserved as regular verse lines "
                                f"(category={element.category})."
                            )
                            implicit_categories_warned.add(element.category)
                        for implicit_line in element.lines:
                            lines.append(_render_verse_line(implicit_line, line_offset=line_offset))
                        continue
                    lines.append(_render_verse_line(element, line_offset=line_offset))

                lines.append(r"\end{ekdverse}")
                lines.append(r"\end{speech}")
    return "\n".join(lines).strip() + "\n"


def _render_witness_declarations(witnesses: list[EkdosisWitness]) -> str:
    return "\n".join(
        rf"\DeclareWitness{{{witness.siglum}}}{{{escape_ekdosis_text(witness.year)}}}{{{escape_ekdosis_text(witness.description)}}}"
        for witness in witnesses
    )


def _render_titlepage(metadata: EkdosisMetadata) -> str:
    title = escape_ekdosis_text(metadata.title)
    author = escape_ekdosis_text(metadata.author)
    editor = escape_ekdosis_text(metadata.editor)
    return "\n".join(
        [
            r"\begin{titlepage}",
            r"\centering",
            rf"{{\Huge \textbf{{\MakeUppercase{{{title}}}}} \par}}",
            r"\vspace{1.5cm}",
            rf"{{\LARGE {author} \par}}",
            r"\vspace{2cm}",
            rf"{{\Large \textit{{Edition critique par {editor}}} \par}}",
            r"\vspace{2cm}",
            r"{\large \today}",
            r"\vfill",
            r"\end{titlepage}",
        ]
    )


def _build_full_document(*, body: str, witnesses: list[EkdosisWitness], metadata: EkdosisMetadata) -> str:
    witness_declarations = _render_witness_declarations(witnesses)
    titlepage = _render_titlepage(metadata)
    return "\n".join(
        [
            template_ekdosis_preamble.strip(),
            witness_declarations,
            template_ekdosis_debut_doc.strip(),
            titlepage,
            body.rstrip(),
            template_ekdosis_fin_doc.strip(),
            "",
        ]
    )


def _build_config(metadata: EkdosisMetadata, witnesses: list[EkdosisWitness], reference_index: int) -> EditionConfig:
    return EditionConfig(
        title=metadata.title,
        author=metadata.author,
        editor=metadata.editor,
        witnesses=[Witness(siglum=w.siglum, year=w.year, description=w.description) for w in witnesses],
        reference_witness=reference_index,
    )


def _encode_tilde_runs_for_pipeline(text: str) -> str:
    return re.sub(r"~+", lambda match: f"[[ETSTILDE{len(match.group(0))}]]", text)


def _encode_italics_for_pipeline(text: str) -> str:
    return _ITALIC_RE.sub(lambda match: f"{_ITALIC_MARKER}{match.group(1)}{_ITALIC_MARKER}", text)


def generate_ekdosis_from_text(
    text: str,
    witnesses: list[WitnessLike],
    reference_witness: str | int | None = None,
    metadata: EkdosisMetadata | dict[str, Any] | None = None,
    start_line_number: int = 1,
) -> EkdosisResult:
    if start_line_number < 1:
        raise EkdosisGenerationError("start_line_number must be >= 1.")

    normalized_witnesses, witness_warnings = _normalize_witnesses(witnesses)
    reference_index = _resolve_reference_index(reference_witness, normalized_witnesses)
    normalized_metadata = _normalize_metadata(metadata)
    pipeline_text = _encode_tilde_runs_for_pipeline(_encode_italics_for_pipeline(text))

    report = validate_input_text(
        pipeline_text,
        len(normalized_witnesses),
        witness_sigla=[w.siglum for w in normalized_witnesses],
    )
    diagnostics = [_format_validation_diagnostic(item) for item in report.diagnostics]
    warnings = list(witness_warnings)
    warnings.extend(
        _format_validation_diagnostic(item)
        for item in report.diagnostics
        if item.level == DiagnosticLevel.WARNING
    )
    if report.has_errors:
        raise EkdosisGenerationError(
            "Input validation failed for Ekdosis generation.",
            diagnostics=diagnostics,
            warnings=warnings,
        )

    config = _build_config(normalized_metadata, normalized_witnesses, reference_index)

    try:
        parsed_play = parse_play(pipeline_text, config)
        collated_play = collate_play(
            parsed_play,
            witness_sigla=[w.siglum for w in normalized_witnesses],
            reference_witness=reference_index,
        )
    except ValueError as exc:
        raise EkdosisGenerationError(
            f"Ekdosis generation failed: {exc}",
            diagnostics=diagnostics,
            warnings=warnings,
        ) from exc

    line_offset = start_line_number - 1
    body = _render_body(collated_play, line_offset=line_offset, warnings=warnings)
    full_document = _build_full_document(body=body, witnesses=normalized_witnesses, metadata=normalized_metadata)
    return EkdosisResult(body=body, full_document=full_document, diagnostics=diagnostics, warnings=warnings)


def generate_ekdosis_from_config(
    text: str,
    config: EditionConfig,
    *,
    start_line_number: int = 1,
) -> EkdosisResult:
    metadata = EkdosisMetadata(title=config.title, author=config.author, editor=config.editor)
    return generate_ekdosis_from_text(
        text=text,
        witnesses=list(config.witnesses),
        reference_witness=config.reference_witness,
        metadata=metadata,
        start_line_number=start_line_number,
    )


def export_ekdosis(full_document: str, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(full_document, encoding="utf-8")
    return path.resolve()
