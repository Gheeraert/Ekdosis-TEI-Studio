from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from ets.core import run_pipeline_from_text
from ets.domain import EditionConfig, Witness
from ets.parser import load_config

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"


def test_tei_header_keeps_config_metadata_and_clean_listwit_structure() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture_dir = root / "fixtures" / "stable"
    input_text = (fixture_dir / "input.txt").read_text(encoding="utf-8")
    config = load_config(fixture_dir / "config.json")

    tei_xml = run_pipeline_from_text(input_text, config)
    xml_root = ET.fromstring(tei_xml)

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
