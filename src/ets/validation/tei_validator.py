from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from functools import lru_cache
from lxml import etree


@dataclass(frozen=True)
class TeiValidationIssue:
    level: str
    message: str
    line: int | None = None
    column: int | None = None


@dataclass(frozen=True)
class TeiValidationResult:
    is_valid: bool
    schema_name: str
    engine_name: str
    errors: list[TeiValidationIssue] = field(default_factory=list)


@lru_cache(maxsize=4)
def _load_relaxng(schema_path: str) -> etree.RelaxNG:
    schema_doc = etree.parse(schema_path)
    return etree.RelaxNG(schema_doc)

def default_tei_schema_path() -> Path:
    return Path(__file__).resolve().parents[1] / "resources" / "schemas" / "tei_all.rng"


def _validate_source_desc_children(xml_doc: etree._Element) -> list[TeiValidationIssue]:
    tei_ns = "http://www.tei-c.org/ns/1.0"
    ns = {"tei": tei_ns}
    issues: list[TeiValidationIssue] = []
    for source_desc in xml_doc.xpath(".//tei:fileDesc/tei:sourceDesc", namespaces=ns):
        has_p = bool(source_desc.xpath("./tei:p", namespaces=ns))
        has_list_wit = bool(source_desc.xpath("./tei:listWit", namespaces=ns))
        if has_p and has_list_wit:
            issues.append(
                TeiValidationIssue(
                    level="ERROR",
                    message="sourceDesc must not mix <p> and <listWit> siblings.",
                    line=source_desc.sourceline,
                    column=None,
                )
            )
    return issues


def _issue_from_log_entry(entry: etree._LogEntry) -> TeiValidationIssue:
    return TeiValidationIssue(
        level=entry.level_name,
        message=entry.message,
        line=entry.line,
        column=entry.column,
    )


def validate_tei_xml(xml_text: str, schema_path: str | Path | None = None) -> TeiValidationResult:
    """Validate TEI XML against a local generic TEI Relax NG schema."""
    resolved_schema_path = Path(schema_path) if schema_path is not None else default_tei_schema_path()
    schema_name = resolved_schema_path.name
    engine_name = "lxml-relaxng"

    if not resolved_schema_path.exists():
        return TeiValidationResult(
            is_valid=False,
            schema_name=schema_name,
            engine_name=engine_name,
            errors=[
                TeiValidationIssue(
                    level="ERROR",
                    message=f"Schema not found: {resolved_schema_path}",
                )
            ],
        )

    try:
        relaxng = _load_relaxng(str(resolved_schema_path.resolve()))
    except (etree.XMLSyntaxError, etree.RelaxNGParseError, OSError) as exc:
        return TeiValidationResult(
            is_valid=False,
            schema_name=schema_name,
            engine_name=engine_name,
            errors=[TeiValidationIssue(level="ERROR", message=f"Unable to load schema: {exc}")],
        )

    try:
        xml_doc = etree.fromstring(xml_text.encode("utf-8"))
    except etree.XMLSyntaxError as exc:
        return TeiValidationResult(
            is_valid=False,
            schema_name=schema_name,
            engine_name=engine_name,
            errors=[
                TeiValidationIssue(
                    level="ERROR",
                    message=f"Malformed XML: {exc.msg}",
                    line=exc.lineno,
                    column=exc.offset,
                )
            ],
        )

    rng_valid = bool(relaxng.validate(xml_doc))
    errors = [_issue_from_log_entry(entry) for entry in relaxng.error_log]
    errors.extend(_validate_source_desc_children(xml_doc))
    is_valid = rng_valid and not errors

    if is_valid:
        return TeiValidationResult(is_valid=True, schema_name=schema_name, engine_name=engine_name, errors=[])

    return TeiValidationResult(
        is_valid=False,
        schema_name=schema_name,
        engine_name=engine_name,
        errors=errors,
    )
