from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from ets.application import (
    enrich_tei_with_annotations,
    export_html,
    export_tei,
    generate_html_preview_from_tei,
    generate_html_preview_from_text,
    generate_tei_from_text,
    load_config,
    validate_text,
)
from ets.annotations import Annotation, AnnotationAnchor, AnnotationCollection


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_service_validate_text_success_on_stable_fixture() -> None:
    root = _root()
    config = load_config(root / "fixtures" / "stable" / "config.json")
    text = (root / "fixtures" / "stable" / "input.txt").read_text(encoding="utf-8")

    result = validate_text(text, config)
    assert result.ok is True
    assert all(item.level != "ERROR" for item in result.diagnostics)


def test_service_validate_text_failure_preserves_diagnostics() -> None:
    root = _root()
    config = load_config(root / "fixtures" / "known_issues" / "britannicus_scene_2_acte_2" / "config.json")
    text = (root / "fixtures" / "stable" / "britannicus_I.txt").read_text(encoding="utf-8")

    result = validate_text(text, config)
    assert result.ok is False
    assert result.diagnostics
    first = result.diagnostics[0]
    assert first.code == "E_BLOCK_SIZE"
    assert first.block_index == 159
    assert first.line_number is not None


def test_service_generate_tei_from_text_success() -> None:
    root = _root()
    config = load_config(root / "fixtures" / "stable" / "config.json")
    text = (root / "fixtures" / "stable" / "input.txt").read_text(encoding="utf-8")

    result = generate_tei_from_text(text, config)
    assert result.ok is True
    assert result.tei_xml is not None
    assert "<TEI" in result.tei_xml
    assert "<text>" in result.tei_xml


def test_service_generate_html_preview_from_tei_success() -> None:
    root = _root()
    config = load_config(root / "fixtures" / "stable" / "config.json")
    text = (root / "fixtures" / "stable" / "input.txt").read_text(encoding="utf-8")
    tei = generate_tei_from_text(text, config)
    assert tei.ok is True and tei.tei_xml is not None

    html = generate_html_preview_from_tei(tei.tei_xml)
    assert html.ok is True
    assert html.html is not None
    assert "<html" in html.html.lower()
    assert "locuteur" in html.html


def test_service_generate_html_preview_from_text_success() -> None:
    root = _root()
    config = load_config(root / "fixtures" / "stable" / "config.json")
    text = (root / "fixtures" / "stable" / "input.txt").read_text(encoding="utf-8")

    result = generate_html_preview_from_text(text, config)
    assert result.ok is True
    assert result.html is not None
    assert "scene-titre" in result.html


def test_service_export_helpers_write_files() -> None:
    root = _root()
    runtime = root / "tests" / "_runtime"
    tei_path = runtime / "service_export_test.xml"
    html_path = runtime / "service_export_test.html"

    written_tei = export_tei("<TEI/>", tei_path)
    written_html = export_html("<html><body>ok</body></html>", html_path)

    assert written_tei == tei_path.resolve()
    assert written_html == html_path.resolve()
    assert written_tei.exists()
    assert written_html.exists()
    assert written_tei.read_text(encoding="utf-8") == "<TEI/>"
    assert written_html.read_text(encoding="utf-8") == "<html><body>ok</body></html>"


def test_service_generate_tei_avoids_double_input_validation() -> None:
    root = _root()
    config = load_config(root / "fixtures" / "stable" / "config.json")
    text = (root / "fixtures" / "stable" / "input.txt").read_text(encoding="utf-8")

    with patch("ets.core.validate_input_text", side_effect=AssertionError("core validation should be skipped")):
        result = generate_tei_from_text(text, config)
    assert result.ok is True
    assert result.tei_xml is not None


def test_service_enrich_tei_preserves_annotation_target_diagnostics() -> None:
    root = _root()
    config = load_config(root / "fixtures" / "stable" / "config.json")
    text = (root / "fixtures" / "stable" / "input.txt").read_text(encoding="utf-8")
    generation = generate_tei_from_text(text, config)
    assert generation.ok is True and generation.tei_xml is not None

    annotations = AnnotationCollection(
        version=1,
        annotations=[
            Annotation(
                id="missing_target",
                type="explicative",
                anchor=AnnotationAnchor(kind="line", act="1", scene="1", line="99999"),
                content="missing",
                status="draft",
                keywords=[],
            )
        ],
    )

    result = enrich_tei_with_annotations(generation.tei_xml, annotations)
    assert result.ok is False
    assert result.tei_xml is None
    assert result.diagnostics
    assert result.diagnostics[0].code == "E_ANN_TARGET_NOT_FOUND"
    assert result.diagnostics[0].annotation_id == "missing_target"


def test_service_enrich_tei_preserves_decimal_range_diagnostics() -> None:
    root = _root()
    config = load_config(root / "fixtures" / "shared_verse" / "thebaide_2_2" / "config.json")
    text = (root / "fixtures" / "shared_verse" / "thebaide_2_2" / "input.txt").read_text(encoding="utf-8")
    generation = generate_tei_from_text(text, config)
    assert generation.ok is True and generation.tei_xml is not None

    annotations = AnnotationCollection(
        version=1,
        annotations=[
            Annotation(
                id="range_shared",
                type="dramaturgique",
                anchor=AnnotationAnchor(kind="line_range", act="2", scene="2", start_line="441", end_line="441"),
                content="shared range",
                status="draft",
                keywords=[],
            )
        ],
    )

    result = enrich_tei_with_annotations(generation.tei_xml, annotations)
    assert result.ok is False
    assert result.diagnostics
    assert result.diagnostics[0].code == "E_ANN_RANGE_DECIMAL_UNSUPPORTED"
    assert result.diagnostics[0].annotation_id == "range_shared"
