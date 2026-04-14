from __future__ import annotations

from ets.ui.tk.dialogs.annotation_dialog import AnnotationDialog


def _validate(**overrides: str) -> tuple[bool, str | None, str | None]:
    payload = {
        "annotation_id": "n1",
        "ann_type": "explicative",
        "kind": "line",
        "act": "1",
        "scene": "1",
        "line": "42",
        "start_line": "",
        "end_line": "",
        "stage_index": "",
        "content": "Texte",
        "status": "draft",
    }
    payload.update(overrides)
    return AnnotationDialog._validate_form_values(**payload)


def test_dialog_validation_rejects_missing_line_for_line_anchor() -> None:
    ok, _message, field = _validate(line="")
    assert ok is False
    assert field == "line"


def test_dialog_validation_rejects_empty_content() -> None:
    ok, _message, field = _validate(content="")
    assert ok is False
    assert field == "content"


def test_dialog_validation_rejects_invalid_stage_index() -> None:
    ok, _message, field = _validate(kind="stage", line="", stage_index="0")
    assert ok is False
    assert field == "stage_index"


def test_dialog_validation_rejects_missing_line_range_bounds() -> None:
    ok, _message, field = _validate(kind="line_range", line="", start_line="", end_line="3")
    assert ok is False
    assert field == "start_line"


def test_dialog_validation_accepts_valid_payload() -> None:
    ok, message, field = _validate()
    assert ok is True
    assert message is None
    assert field is None
