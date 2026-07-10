from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from ets.core import run_pipeline_from_text
from ets.domain import EditionConfig, Witness
from ets.html import render_html_preview_from_tei
from ets.latex import tei_to_ekdosis
from ets.parser import load_config
from ets.tei.generator import with_tei_profile_references

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def _minimal_parallel_text(line_readings: list[str]) -> str:
    witness_count = len(line_readings)
    lines: list[str] = []
    lines += ["####ACTE I####"] * witness_count
    lines += [""]
    lines += ["###SCENE I###"] * witness_count
    lines += [""]
    lines += ["#ORESTE.#"] * witness_count
    lines += [""]
    lines += line_readings
    return "\n".join(lines)


def _taxonomy(root: ET.Element, taxonomy_id: str) -> ET.Element | None:
    for taxonomy in root.findall(".//tei:teiHeader/tei:encodingDesc/tei:classDecl/tei:taxonomy", TEI_NS):
        if taxonomy.attrib.get(XML_ID) == taxonomy_id:
            return taxonomy
    return None


def _taxonomy_count(root: ET.Element, taxonomy_id: str) -> int:
    return sum(
        1
        for taxonomy in root.findall(".//tei:teiHeader/tei:encodingDesc/tei:classDecl/tei:taxonomy", TEI_NS)
        if taxonomy.attrib.get(XML_ID) == taxonomy_id
    )


def test_tei_header_keeps_config_metadata_and_clean_listwit_structure() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture_dir = root / "fixtures" / "stable"
    input_text = (fixture_dir / "input.txt").read_text(encoding="utf-8")
    config = load_config(fixture_dir / "config.json")

    tei_xml = run_pipeline_from_text(input_text, config)
    xml_root = ET.fromstring(tei_xml)

    assert xml_root.attrib.get(XML_LANG) == "fr"
    text_element = xml_root.find("tei:text", namespaces=TEI_NS)
    assert text_element is not None
    assert text_element.attrib.get(XML_LANG) is None
    assert xml_root.findtext(".//tei:titleStmt/tei:title", namespaces=TEI_NS) == config.title
    assert xml_root.findtext(".//tei:titleStmt/tei:author", namespaces=TEI_NS) == config.author
    assert xml_root.findtext(".//tei:titleStmt/tei:editor", namespaces=TEI_NS) == config.editor

    source_desc = xml_root.find(".//tei:fileDesc/tei:sourceDesc", namespaces=TEI_NS)
    assert source_desc is not None
    assert source_desc.find("tei:p", TEI_NS) is None

    children_tags = [child.tag for child in list(source_desc)]
    assert children_tags == ["{http://www.tei-c.org/ns/1.0}listWit"]

    witnesses = source_desc.findall("tei:listWit/tei:witness", TEI_NS)
    assert len(witnesses) == len(config.witnesses)
    assert [w.attrib.get(XML_ID) for w in witnesses] == [w.siglum for w in config.witnesses]
    assert all("ana" not in witness.attrib for witness in witnesses)
    assert _taxonomy(xml_root, "ets-witness-taxonomy") is None


def test_witness_kind_is_encoded_in_listwit_without_changing_witness_text() -> None:
    config = EditionConfig(
        title="Britannicus",
        author="Jean Racine",
        editor="Tony Gheeraert",
        witnesses=[
            Witness(siglum="A", year="1670", description="Barbin", kind="documentary"),
            Witness(siglum="B", year="1676", description="Collective"),
            Witness(
                siglum="E",
                year="1670-Rég.",
                description="Première édition régularisée",
                kind="editorial",
            ),
        ],
        reference_witness=0,
    )

    tei_xml = run_pipeline_from_text(
        _minimal_parallel_text(["Je parle.", "Je parle.", "Je parle."]),
        config,
    )
    xml_root = ET.fromstring(tei_xml)
    witnesses = xml_root.findall(".//tei:listWit/tei:witness", TEI_NS)

    assert [witness.attrib.get(XML_ID) for witness in witnesses] == ["A", "B", "E"]
    assert witnesses[0].attrib.get("ana") == "#witness_documentary"
    assert witnesses[1].attrib.get("ana") is None
    assert witnesses[2].attrib.get("ana") == "#witness_editorial"
    assert witnesses[0].text == "A (1670) Barbin"
    assert witnesses[1].text == "B (1676) Collective"
    assert witnesses[2].text == "E (1670-Rég.) Première édition régularisée"


def test_witness_taxonomy_is_declared_once_and_resolves_witness_ana_pointers() -> None:
    config = EditionConfig(
        title="Britannicus",
        author="Jean Racine",
        editor="Tony Gheeraert",
        witnesses=[
            Witness(siglum="A", year="1670", description="Barbin", kind="documentary"),
            Witness(siglum="E", year="1670-Rég.", description="Première édition régularisée", kind="editorial"),
        ],
        reference_witness=0,
    )

    tei_xml = run_pipeline_from_text(_minimal_parallel_text(["Je parle.", "Je parle."]), config)
    xml_root = ET.fromstring(tei_xml)
    taxonomy = _taxonomy(xml_root, "ets-witness-taxonomy")

    assert taxonomy is not None
    categories = taxonomy.findall("tei:category", TEI_NS)
    assert [category.attrib.get(XML_ID) for category in categories] == [
        "witness_documentary",
        "witness_editorial",
    ]
    assert [
        category.findtext("tei:catDesc", namespaces=TEI_NS)
        for category in categories
    ] == [
        "Témoin documentaire.",
        "Témoin éditorial construit.",
    ]

    declared_categories = {category.attrib.get(XML_ID) for category in categories}
    for witness in xml_root.findall(".//tei:listWit/tei:witness[@ana]", TEI_NS):
        for pointer in witness.attrib["ana"].split():
            assert pointer.startswith("#")
            assert pointer[1:] in declared_categories

    reparsed = ET.fromstring(with_tei_profile_references(with_tei_profile_references(tei_xml)))
    assert _taxonomy_count(reparsed, "ets-witness-taxonomy") == 1


def test_witness_taxonomy_coexists_with_variant_taxonomy_and_is_idempotent() -> None:
    config = EditionConfig(
        title="Britannicus",
        author="Jean Racine",
        editor="Tony Gheeraert",
        witnesses=[
            Witness(siglum="A", year="1670", description="Barbin"),
            Witness(siglum="E", year="1670-Rég.", description="Première édition régularisée", kind="editorial"),
        ],
        reference_witness=0,
    )

    tei_xml = run_pipeline_from_text(_minimal_parallel_text(["Fils.", "fils."]), config)
    xml_root = ET.fromstring(tei_xml)

    assert _taxonomy_count(xml_root, "ets-variant-taxonomy") == 1
    assert _taxonomy_count(xml_root, "ets-witness-taxonomy") == 1

    reparsed = ET.fromstring(with_tei_profile_references(with_tei_profile_references(tei_xml)))
    assert _taxonomy_count(reparsed, "ets-variant-taxonomy") == 1
    assert _taxonomy_count(reparsed, "ets-witness-taxonomy") == 1


def test_witness_kind_ana_does_not_leak_into_html_or_ekdosis_visible_text() -> None:
    config = EditionConfig(
        title="Britannicus",
        author="Jean Racine",
        editor="Tony Gheeraert",
        witnesses=[
            Witness(siglum="A", year="1670", description="Barbin"),
            Witness(siglum="E", year="1670-Rég.", description="Première édition régularisée", kind="editorial"),
        ],
        reference_witness=0,
    )

    tei_xml = run_pipeline_from_text(_minimal_parallel_text(["Fils.", "fils."]), config)
    html = render_html_preview_from_tei(tei_xml)
    tex = tei_to_ekdosis(tei_xml, standalone=True)

    assert "witness_editorial" not in html
    assert "witness_editorial" not in tex
    assert r"\DeclareWitness{E}{1670-Rég.}{Première édition régularisée}" in tex


def test_generated_tei_declares_ets_racine_profile_models_and_schema_refs() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture_dir = root / "fixtures" / "stable"
    input_text = (fixture_dir / "input.txt").read_text(encoding="utf-8")
    config = load_config(fixture_dir / "config.json")

    tei_xml = run_pipeline_from_text(input_text, config)
    xml_root = ET.fromstring(tei_xml)

    assert tei_xml.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert (
        '<?xml-model href="tei-profile/ets-racine.rnc" '
        'type="application/relax-ng-compact-syntax"?>'
    ) in tei_xml
    assert (
        '<?xml-model href="tei-profile/ets-racine.sch" type="application/xml" '
        'schematypens="http://purl.oclc.org/dsdl/schematron"?>'
    ) in tei_xml

    encoding_desc = xml_root.find(".//tei:teiHeader/tei:encodingDesc", namespaces=TEI_NS)
    assert encoding_desc is not None
    schema_refs = {
        (schema_ref.attrib.get("key"), schema_ref.attrib.get("type")): schema_ref.attrib.get("url")
        for schema_ref in encoding_desc.findall("tei:schemaRef", namespaces=TEI_NS)
    }
    assert schema_refs[("ets-racine", "projectODD")] == "tei-profile/ets-racine.odd"
    assert schema_refs[("ets-racine-rnc", "validationRNC")] == "tei-profile/ets-racine.rnc"
    assert schema_refs[("ets-racine-sch", "validationSchematron")] == "tei-profile/ets-racine.sch"


def test_tei_header_includes_optional_transcriber_respstmt() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture_dir = root / "fixtures" / "stable"
    input_text = (fixture_dir / "input.txt").read_text(encoding="utf-8")
    base_config = load_config(fixture_dir / "config.json")
    config = EditionConfig(
        title=base_config.title,
        author=base_config.author,
        editor="Caroline Labrune",
        witnesses=base_config.witnesses,
        reference_witness=base_config.reference_witness,
        transcriber="Jeanne Martin",
    )

    tei_xml = run_pipeline_from_text(input_text, config)
    xml_root = ET.fromstring(tei_xml)

    editor = xml_root.find(".//tei:titleStmt/tei:editor", namespaces=TEI_NS)
    assert editor is not None
    assert editor.text == "Caroline Labrune"
    assert editor.attrib.get("role") == "scientific"
    assert xml_root.findtext(".//tei:titleStmt/tei:respStmt/tei:resp", namespaces=TEI_NS) == "Transcription"
    assert xml_root.findtext(".//tei:titleStmt/tei:respStmt/tei:name", namespaces=TEI_NS) == "Jeanne Martin"


def test_tei_header_omits_empty_scientific_editor_and_empty_transcriber() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture_dir = root / "fixtures" / "stable"
    input_text = (fixture_dir / "input.txt").read_text(encoding="utf-8")
    base_config = load_config(fixture_dir / "config.json")
    config = EditionConfig(
        title=base_config.title,
        author=base_config.author,
        editor="",
        witnesses=base_config.witnesses,
        reference_witness=base_config.reference_witness,
        transcriber="",
    )

    tei_xml = run_pipeline_from_text(input_text, config)
    xml_root = ET.fromstring(tei_xml)

    assert xml_root.find(".//tei:titleStmt/tei:editor", namespaces=TEI_NS) is None
    assert xml_root.find(".//tei:titleStmt/tei:respStmt", namespaces=TEI_NS) is None
