from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from ets.annotations import (
    Annotation,
    AnnotationAnchor,
    AnnotationCollection,
    AnnotationTargetNotFoundError,
    inject_annotations_into_tei,
    load_annotations,
)
from ets.core import run_pipeline, run_pipeline_from_text
from ets.domain import EditionConfig, Witness

NS = {"tei": "http://www.tei-c.org/ns/1.0"}
XML_NS = "http://www.w3.org/XML/1998/namespace"


def _fixture_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "annotations" / "berenice_1_1"


def test_injection_on_line_range_and_stage_targets() -> None:
    fixture = _fixture_dir()
    tei_xml = run_pipeline(input_path=fixture / "input.txt", config_path=fixture / "config.json")
    annotations = load_annotations(fixture / "annotations.json")

    enriched = inject_annotations_into_tei(tei_xml, annotations)
    root = ET.fromstring(enriched)
    notes = root.findall(".//tei:note", NS)

    assert len(notes) == 3
    note_by_id = {note.get(f"{{{XML_NS}}}id"): note for note in notes}
    assert note_by_id["n1"].get("target") == "#A1S1L1"
    assert note_by_id["n2"].get("target") == "#A1S1L2 #A1S1L3"
    assert note_by_id["n3"].get("target") == "#A1S1ST1"


def test_injection_target_not_found_raises_diagnostic() -> None:
    fixture = _fixture_dir()
    tei_xml = run_pipeline(input_path=fixture / "input.txt", config_path=fixture / "config.json")
    missing = AnnotationCollection(
        version=1,
        annotations=[
            Annotation(
                id="missing",
                type="explicative",
                anchor=AnnotationAnchor(kind="line", act="1", scene="1", line="404"),
                content="not found",
                status="draft",
                keywords=[],
            )
        ],
    )

    with pytest.raises(AnnotationTargetNotFoundError) as exc_info:
        inject_annotations_into_tei(tei_xml, missing)

    codes = {diag.code for diag in exc_info.value.diagnostics}
    assert "E_ANN_TARGET_NOT_FOUND" in codes


def test_regression_pipeline_without_annotations_still_generates_plain_tei() -> None:
    fixture = _fixture_dir()
    tei_xml = run_pipeline(input_path=fixture / "input.txt", config_path=fixture / "config.json")
    root = ET.fromstring(tei_xml)

    assert root.find(".//tei:note", NS) is None
    assert root.find(".//tei:l[@xml:id='A1S1L1']", {"tei": NS["tei"], "xml": XML_NS}) is not None


def test_enriched_fixture_matches_expected_xml() -> None:
    fixture = _fixture_dir()
    tei_xml = run_pipeline(input_path=fixture / "input.txt", config_path=fixture / "config.json")
    annotations = load_annotations(fixture / "annotations.json")

    enriched = inject_annotations_into_tei(tei_xml, annotations)
    expected = (fixture / "expected_annotated.xml").read_text(encoding="utf-8")

    assert ET.tostring(ET.fromstring(enriched), encoding="unicode") == ET.tostring(ET.fromstring(expected), encoding="unicode")


def test_line_anchor_resolves_when_tei_uses_roman_act_scene_numbers() -> None:
    config = EditionConfig(
        title="Test",
        author="Auteur",
        editor="Editeur",
        witnesses=[Witness(siglum="A", year="1671", description="A"), Witness(siglum="B", year="1676", description="B")],
        reference_witness=0,
        start_line_number=1,
        act_number="I",
        scene_number="I",
    )
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "##ANTIOCHUS##",
            "##ANTIOCHUS##",
            "",
            "#ANTIOCHUS#",
            "#ANTIOCHUS#",
            "",
            "Arretons.",
            "Arretons.",
        ]
    )
    tei_xml = run_pipeline_from_text(text, config)
    annotations = AnnotationCollection(
        version=1,
        annotations=[
            Annotation(
                id="n_roman",
                type="explicative",
                anchor=AnnotationAnchor(kind="line", act="1", scene="1", line="1"),
                content="Roman compatible",
                status="draft",
                keywords=[],
            )
        ],
    )

    enriched = inject_annotations_into_tei(tei_xml, annotations)
    root = ET.fromstring(enriched)
    note = root.find(".//tei:note[@xml:id='n_roman']", {"tei": NS["tei"], "xml": XML_NS})
    assert note is not None
    assert note.get("target") == "#AISIL1"


def test_line_range_over_shared_verse_returns_explicit_decimal_diagnostic() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture = root / "fixtures" / "shared_verse" / "thebaide_2_2"
    tei_xml = run_pipeline(input_path=fixture / "input.txt", config_path=fixture / "config.json")
    annotations = AnnotationCollection(
        version=1,
        annotations=[
            Annotation(
                id="n_range_shared",
                type="dramaturgique",
                anchor=AnnotationAnchor(kind="line_range", act="2", scene="2", start_line="441", end_line="441"),
                content="range on shared line",
                status="draft",
                keywords=[],
            )
        ],
    )

    with pytest.raises(AnnotationTargetNotFoundError) as exc_info:
        inject_annotations_into_tei(tei_xml, annotations)

    codes = {diag.code for diag in exc_info.value.diagnostics}
    assert "E_ANN_RANGE_DECIMAL_UNSUPPORTED" in codes
