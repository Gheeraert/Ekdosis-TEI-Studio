from __future__ import annotations

from pathlib import Path

import pytest

from ets.annotations import AnnotationValidationError, load_annotations, save_annotations


def test_load_annotations_valid_fixture() -> None:
    root = Path(__file__).resolve().parents[1]
    collection = load_annotations(root / "fixtures" / "annotations" / "berenice_1_1" / "annotations.json")

    assert collection.version == 1
    assert len(collection.annotations) == 3
    assert collection.annotations[0].id == "n1"
    assert collection.annotations[1].anchor.kind == "line_range"
    assert collection.annotations[2].anchor.stage_index == 1


def test_save_annotations_writes_human_readable_json() -> None:
    root = Path(__file__).resolve().parents[1]
    source = root / "fixtures" / "annotations" / "berenice_1_1" / "annotations.json"
    collection = load_annotations(source)

    output = root / "tests" / "_runtime" / "annotations.saved.json"
    written = save_annotations(collection, output)

    assert written == output.resolve()
    raw = output.read_text(encoding="utf-8")
    assert '"version": 1' in raw
    assert '\n  "annotations": [' in raw


def test_load_annotations_rejects_invalid_json_shape() -> None:
    root = Path(__file__).resolve().parents[1]
    bad = root / "tests" / "_runtime" / "bad_annotations.json"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text('{"version": 1, "annotations": {"id": "n1"}}', encoding="utf-8")

    with pytest.raises(AnnotationValidationError) as exc_info:
        load_annotations(bad)

    codes = {diag.code for diag in exc_info.value.diagnostics}
    assert "E_ANN_INVALID_JSON" in codes
