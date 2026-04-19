from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from .models import ImportDiagnostic, ImportResult, ReferenceRecord


def import_references(path: str | Path) -> ImportResult:
    source_path = Path(path)
    suffix = source_path.suffix.lower()
    if suffix == ".json":
        return import_csl_json(source_path)
    if suffix in {".bib", ".bibtex"}:
        return ImportResult(
            references=(),
            diagnostics=(ImportDiagnostic(code="W_REF_IMPORT_BIBTEX_TODO", severity="WARNING", message="Import BibTeX non implémenté dans cette passe."),),
            source_format="bibtex",
        )
    if suffix == ".ris":
        return ImportResult(
            references=(),
            diagnostics=(ImportDiagnostic(code="W_REF_IMPORT_RIS_TODO", severity="WARNING", message="Import RIS non implémenté dans cette passe."),),
            source_format="ris",
        )
    return ImportResult(
        references=(),
        diagnostics=(ImportDiagnostic(code="E_REF_IMPORT_FORMAT", message=f"Format de fichier non pris en charge: {source_path.suffix or '(sans extension)'}"),),
        source_format="unknown",
    )


def import_csl_json(path: str | Path) -> ImportResult:
    source_path = Path(path)
    try:
        payload = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return ImportResult(
            references=(),
            diagnostics=(ImportDiagnostic(code="E_REF_IMPORT_CSL_JSON", message=str(exc)),),
            source_format="csl_json",
        )

    if isinstance(payload, dict):
        items = [payload]
    elif isinstance(payload, list):
        items = payload
    else:
        return ImportResult(
            references=(),
            diagnostics=(ImportDiagnostic(code="E_REF_IMPORT_CSL_STRUCTURE", message="Le fichier CSL JSON doit contenir un objet ou une liste d'objets."),),
            source_format="csl_json",
        )

    refs: list[ReferenceRecord] = []
    diags: list[ImportDiagnostic] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            diags.append(
                ImportDiagnostic(
                    code="W_REF_IMPORT_CSL_ITEM",
                    severity="WARNING",
                    message=f"Entrée {index} ignorée (objet JSON attendu).",
                )
            )
            continue
        refs.append(_from_csl_item(item))
    return ImportResult(references=tuple(refs), diagnostics=tuple(diags), source_format="csl_json")


def _from_csl_item(item: dict[str, Any]) -> ReferenceRecord:
    identifier = str(item.get("id") or f"ref-{uuid4().hex[:10]}")
    title = _text(item.get("title")) or "Sans titre"
    source_key = _text(item.get("id"))
    entry_type = _text(item.get("type")) or "book"
    authors = tuple(_author_to_text(author) for author in item.get("author", []) if _author_to_text(author))
    date_value = _extract_date(item.get("issued"))
    publisher = _text(item.get("publisher"))
    container_title = _container_title(item.get("container-title"))
    pages = _text(item.get("page"))
    volume = _text(item.get("volume"))
    issue = _text(item.get("issue"))
    place = _text(item.get("publisher-place"))
    doi = _text(item.get("DOI"))
    url = _text(item.get("URL"))
    editor = _join_names(item.get("editor"))
    translator = _join_names(item.get("translator"))

    normalized = {
        "author": authors,
        "title": title,
        "date": date_value,
        "type": entry_type,
    }

    return ReferenceRecord(
        id=identifier,
        origin="zotero_file",
        source_key=source_key,
        type=entry_type,
        title=title,
        authors=authors,
        date=date_value,
        publisher=publisher,
        container_title=container_title,
        volume=volume,
        issue=issue,
        pages=pages,
        place=place,
        url=url,
        doi=doi,
        raw_data=item,
        normalized_data=normalized,
        editor=editor,
        translator=translator,
    )


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        val = value.strip()
        return val or None
    return str(value)


def _author_to_text(author: Any) -> str:
    if isinstance(author, str):
        return author.strip()
    if isinstance(author, dict):
        literal = _text(author.get("literal"))
        if literal:
            return literal
        family = _text(author.get("family")) or ""
        given = _text(author.get("given")) or ""
        full = " ".join(part for part in (given, family) if part).strip()
        return full
    return ""


def _extract_date(issued: Any) -> str | None:
    if isinstance(issued, dict):
        date_parts = issued.get("date-parts")
        if isinstance(date_parts, list) and date_parts and isinstance(date_parts[0], list) and date_parts[0]:
            first = date_parts[0][0]
            return str(first)
        raw = issued.get("raw")
        if raw:
            return str(raw)
    return None


def _container_title(value: Any) -> str | None:
    if isinstance(value, list):
        for item in value:
            text = _text(item)
            if text:
                return text
        return None
    return _text(value)


def _join_names(value: Any) -> str | None:
    if not isinstance(value, list):
        return None
    names = [name for name in (_author_to_text(item) for item in value) if name]
    if not names:
        return None
    return ", ".join(names)

