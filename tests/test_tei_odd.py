from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ODD_PATH = ROOT / "src" / "ets" / "resources" / "odd" / "ets-racine.odd"
TEI_NS = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI_NS}


def _parse_odd() -> ET.Element:
    return ET.parse(ODD_PATH).getroot()


def _text_content(root: ET.Element) -> str:
    return " ".join(root.itertext())


def _constraint_text(root: ET.Element) -> str:
    constraints = root.findall(".//tei:constraintSpec", NS)
    return " ".join(ET.tostring(element, encoding="unicode") for element in constraints)


def test_ets_racine_odd_exists_and_is_well_formed_tei() -> None:
    assert ODD_PATH.is_file()
    root = _parse_odd()
    assert root.tag == f"{{{TEI_NS}}}TEI"


def test_odd_contains_schema_spec_and_expected_modules() -> None:
    root = _parse_odd()
    schema = root.find(".//tei:schemaSpec", NS)
    assert schema is not None
    assert schema.get("ident") == "ets-racine"
    assert schema.get("start") == "TEI"

    modules = {module.get("key") for module in schema.findall("tei:moduleRef", NS)}
    assert {
        "tei",
        "header",
        "core",
        "textstructure",
        "drama",
        "textcrit",
        "verse",
        "tagdocs",
    }.issubset(modules)


def test_odd_documents_central_ets_racine_elements() -> None:
    root = _parse_odd()
    elements = {element.get("ident") for element in root.findall(".//tei:elementSpec", NS)}
    assert {
        "text",
        "body",
        "div",
        "stage",
        "sp",
        "speaker",
        "l",
        "lg",
        "app",
        "lem",
        "rdg",
        "hi",
        "listWit",
        "witness",
    }.issubset(elements)


def test_odd_states_scope_and_exclusions() -> None:
    content = _text_content(_parse_odd()).lower()
    for token in [
        "corps dramatique",
        "pièces de racine",
        "produit automatiquement",
        "tei de sortie",
        "front matter",
        "paratextes",
    ]:
        assert token in content

    root = _parse_odd()
    assert not root.findall(".//tei:div[@type='front']", NS)


def test_odd_documents_implicit_stage_categories() -> None:
    content = _text_content(_parse_odd())
    for token in ["SPC", "ASP", "TMP", "EVT", "SET", "PROX", "ATT", "VOI"]:
        assert token in content


def test_odd_contains_schematron_constraints_for_critical_rules() -> None:
    root = _parse_odd()
    constraints = root.findall(".//tei:constraintSpec", NS)
    assert constraints

    content = _constraint_text(root)
    for token in [
        "stage[@type='DI']",
        "app[@type='minor']",
        "lem",
        "rdg",
        "@wit",
        "witness",
        "hi",
        "italic",
        "lg",
        "stanza",
    ]:
        assert token in content


def test_odd_references_operational_schemas() -> None:
    content = _text_content(_parse_odd())
    assert "ets-racine.rnc" in content
    assert "ets-racine.sch" in content
