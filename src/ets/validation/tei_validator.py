from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from functools import lru_cache
from lxml import etree
from lxml.isoschematron import Schematron

import rnc2rng
from rnc2rng.parser import ParseError as RncParseError


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
    path = Path(schema_path)
    if path.suffix == ".rnc":
        with path.open(encoding="utf-8") as handle:
            compact_grammar = rnc2rng.load(handle)
        schema_doc = etree.fromstring(rnc2rng.dumps(compact_grammar).encode("utf-8"))
    else:
        schema_doc = etree.parse(schema_path)
    return etree.RelaxNG(schema_doc)


@lru_cache(maxsize=4)
def _load_schematron(schema_path: str) -> Schematron | None:
    """Charge le Schematron associe au meme profil de schema, s'il existe.

    Convention : un schema `<nom>.rnc` (ou `.rng`) est accompagne d'un
    `<nom>.sch` optionnel portant les regles de cooccurrence que la
    grammaire seule ne peut pas exprimer (ex. `<app>` doit contenir
    exactement un `<lem>`).
    """
    sch_path = Path(schema_path).with_suffix(".sch")
    if not sch_path.exists():
        return None
    return Schematron(etree.parse(str(sch_path)), store_report=True)


def default_tei_schema_path() -> Path:
    """Schema RelaxNG strict utilise en interne (profil ets-racine), pas TEI_all."""
    return Path(__file__).resolve().parents[1] / "resources" / "schemas" / "ets-racine.rnc"


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


_SVRL_NS = {"svrl": "http://purl.oclc.org/dsdl/svrl"}


def _schematron_issues(schematron: Schematron) -> list[TeiValidationIssue]:
    issues: list[TeiValidationIssue] = []
    for failed in schematron.validation_report.xpath("//svrl:failed-assert", namespaces=_SVRL_NS):
        message = (failed.findtext("svrl:text", namespaces=_SVRL_NS) or "").strip()
        issues.append(TeiValidationIssue(level="ERROR", message=message or "Schematron rule failed."))
    return issues


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
    except (etree.XMLSyntaxError, etree.RelaxNGParseError, RncParseError, OSError) as exc:
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

    try:
        schematron = _load_schematron(str(resolved_schema_path.resolve()))
    except (etree.XMLSyntaxError, OSError) as exc:
        errors.append(TeiValidationIssue(level="ERROR", message=f"Unable to load Schematron rules: {exc}"))
        schematron = None

    if schematron is not None:
        schematron_valid = bool(schematron.validate(xml_doc))
        if not schematron_valid:
            errors.extend(_schematron_issues(schematron))

    is_valid = rng_valid and not errors

    if is_valid:
        return TeiValidationResult(is_valid=True, schema_name=schema_name, engine_name=engine_name, errors=[])

    return TeiValidationResult(
        is_valid=False,
        schema_name=schema_name,
        engine_name=engine_name,
        errors=errors,
    )
