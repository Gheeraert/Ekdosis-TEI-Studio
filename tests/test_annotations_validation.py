from __future__ import annotations

import pytest

from ets.annotations import (
    Annotation,
    AnnotationAnchor,
    AnnotationCollection,
    AnnotationValidationError,
    delete_annotation,
    parse_annotations_payload,
    update_annotation,
)


def test_duplicate_annotation_id_rejected() -> None:
    payload = {
        "version": 1,
        "annotations": [
            {
                "id": "n1",
                "type": "explicative",
                "anchor": {"kind": "line", "act": "1", "scene": "1", "line": "1"},
                "content": "ok",
                "status": "draft",
                "keywords": [],
            },
            {
                "id": "n1",
                "type": "dramaturgique",
                "anchor": {"kind": "line", "act": "1", "scene": "1", "line": "2"},
                "content": "ok",
                "status": "reviewed",
                "keywords": [],
            },
        ],
    }

    with pytest.raises(AnnotationValidationError) as exc_info:
        parse_annotations_payload(payload)

    codes = {diag.code for diag in exc_info.value.diagnostics}
    assert "E_ANN_DUPLICATE_ID" in codes


def test_invalid_anchor_rejected() -> None:
    payload = {
        "version": 1,
        "annotations": [
            {
                "id": "n1",
                "type": "explicative",
                "anchor": {"kind": "stage", "act": "1", "scene": "1", "stage_index": 0},
                "content": "ok",
                "status": "draft",
                "keywords": [],
            }
        ],
    }

    with pytest.raises(AnnotationValidationError) as exc_info:
        parse_annotations_payload(payload)

    codes = {diag.code for diag in exc_info.value.diagnostics}
    assert "E_ANN_INVALID_ANCHOR" in codes


def test_invalid_type_status_and_empty_content_rejected() -> None:
    payload = {
        "version": 1,
        "annotations": [
            {
                "id": "n1",
                "type": "inconnue",
                "anchor": {"kind": "line", "act": "1", "scene": "1", "line": "1"},
                "content": "   ",
                "status": "unknown",
                "keywords": [],
            }
        ],
    }

    with pytest.raises(AnnotationValidationError) as exc_info:
        parse_annotations_payload(payload)

    codes = {diag.code for diag in exc_info.value.diagnostics}
    assert "E_ANN_INVALID_TYPE" in codes
    assert "E_ANN_INVALID_STATUS" in codes
    assert "E_ANN_EMPTY_CONTENT" in codes


def test_line_range_decimal_bounds_rejected_with_precise_code() -> None:
    payload = {
        "version": 1,
        "annotations": [
            {
                "id": "n1",
                "type": "dramaturgique",
                "anchor": {"kind": "line_range", "act": "1", "scene": "1", "start_line": "441.1", "end_line": "441.2"},
                "content": "shared verse range",
                "status": "draft",
                "keywords": [],
            }
        ],
    }

    with pytest.raises(AnnotationValidationError) as exc_info:
        parse_annotations_payload(payload)

    codes = {diag.code for diag in exc_info.value.diagnostics}
    assert "E_ANN_RANGE_DECIMAL_UNSUPPORTED" in codes


def test_update_delete_missing_annotation_uses_not_found_code() -> None:
    collection = AnnotationCollection(
        version=1,
        annotations=[
            Annotation(
                id="n1",
                type="explicative",
                anchor=AnnotationAnchor(kind="line", act="1", scene="1", line="1"),
                content="ok",
                status="draft",
                keywords=[],
            )
        ],
    )

    with pytest.raises(AnnotationValidationError) as update_exc:
        update_annotation(
            collection,
            Annotation(
                id="missing",
                type="explicative",
                anchor=AnnotationAnchor(kind="line", act="1", scene="1", line="2"),
                content="x",
                status="draft",
                keywords=[],
            ),
        )
    with pytest.raises(AnnotationValidationError) as delete_exc:
        delete_annotation(collection, "missing")

    assert update_exc.value.diagnostics[0].code == "E_ANN_NOT_FOUND"
    assert delete_exc.value.diagnostics[0].code == "E_ANN_NOT_FOUND"
