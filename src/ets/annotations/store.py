from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import (
    Annotation,
    AnnotationAnchor,
    AnnotationCollection,
    AnnotationDiagnostic,
    AnnotationValidationError,
    SUPPORTED_ANCHOR_KINDS,
    SUPPORTED_ANNOTATION_STATUS,
    SUPPORTED_ANNOTATION_TYPES,
)


def _diag(code: str, message: str, *, annotation_id: str | None = None, field: str | None = None) -> AnnotationDiagnostic:
    return AnnotationDiagnostic(code=code, message=message, annotation_id=annotation_id, field=field)


def _to_str(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized


def _is_line_identifier(value: str) -> bool:
    parts = value.split(".")
    return len(parts) in {1, 2} and all(part.isdigit() for part in parts)


def _parse_anchor(raw: Any, diagnostics: list[AnnotationDiagnostic], annotation_id: str | None) -> AnnotationAnchor | None:
    if not isinstance(raw, dict):
        diagnostics.append(_diag("E_ANN_INVALID_ANCHOR", "Anchor must be a JSON object.", annotation_id=annotation_id))
        return None

    kind = raw.get("kind")
    act = raw.get("act")
    scene = raw.get("scene")
    if kind not in SUPPORTED_ANCHOR_KINDS:
        diagnostics.append(
            _diag(
                "E_ANN_INVALID_ANCHOR",
                f"Unsupported anchor kind: {kind!r}.",
                annotation_id=annotation_id,
                field="anchor.kind",
            )
        )
    act_text = _to_str(act)
    scene_text = _to_str(scene)
    if act_text is None:
        diagnostics.append(
            _diag("E_ANN_INVALID_ANCHOR", "Anchor field 'act' must be a non-empty string.", annotation_id=annotation_id, field="anchor.act")
        )
    if scene_text is None:
        diagnostics.append(
            _diag(
                "E_ANN_INVALID_ANCHOR",
                "Anchor field 'scene' must be a non-empty string.",
                annotation_id=annotation_id,
                field="anchor.scene",
            )
        )

    line: str | None = None
    start_line: str | None = None
    end_line: str | None = None
    stage_index: int | None = None

    if kind == "line":
        line_text = _to_str(raw.get("line"))
        if line_text is None or not _is_line_identifier(line_text):
            diagnostics.append(
                _diag(
                    "E_ANN_INVALID_ANCHOR",
                    "Anchor kind 'line' requires a valid 'line' identifier.",
                    annotation_id=annotation_id,
                    field="anchor.line",
                )
            )
        else:
            line = line_text
    elif kind == "line_range":
        start_text = _to_str(raw.get("start_line"))
        end_text = _to_str(raw.get("end_line"))
        if start_text is not None and "." in start_text and _is_line_identifier(start_text):
            diagnostics.append(
                _diag(
                    "E_ANN_RANGE_DECIMAL_UNSUPPORTED",
                    "Anchor kind 'line_range' does not support decimal/shared-verse bounds in V1.",
                    annotation_id=annotation_id,
                    field="anchor.start_line",
                )
            )
        elif start_text is None or not start_text.isdigit():
            diagnostics.append(
                _diag(
                    "E_ANN_INVALID_ANCHOR",
                    "Anchor kind 'line_range' requires integer 'start_line'.",
                    annotation_id=annotation_id,
                    field="anchor.start_line",
                )
            )
        if end_text is not None and "." in end_text and _is_line_identifier(end_text):
            diagnostics.append(
                _diag(
                    "E_ANN_RANGE_DECIMAL_UNSUPPORTED",
                    "Anchor kind 'line_range' does not support decimal/shared-verse bounds in V1.",
                    annotation_id=annotation_id,
                    field="anchor.end_line",
                )
            )
        elif end_text is None or not end_text.isdigit():
            diagnostics.append(
                _diag(
                    "E_ANN_INVALID_ANCHOR",
                    "Anchor kind 'line_range' requires integer 'end_line'.",
                    annotation_id=annotation_id,
                    field="anchor.end_line",
                )
            )
        if start_text is not None and end_text is not None and start_text.isdigit() and end_text.isdigit():
            if int(start_text) > int(end_text):
                diagnostics.append(
                    _diag(
                        "E_ANN_INVALID_ANCHOR",
                        "Anchor kind 'line_range' requires start_line <= end_line.",
                        annotation_id=annotation_id,
                        field="anchor.start_line",
                    )
                )
            else:
                start_line = start_text
                end_line = end_text
    elif kind == "stage":
        stage_value = raw.get("stage_index")
        if not isinstance(stage_value, int) or stage_value <= 0:
            diagnostics.append(
                _diag(
                    "E_ANN_INVALID_ANCHOR",
                    "Anchor kind 'stage' requires positive integer 'stage_index'.",
                    annotation_id=annotation_id,
                    field="anchor.stage_index",
                )
            )
        else:
            stage_index = stage_value

    if diagnostics:
        return None
    return AnnotationAnchor(
        kind=str(kind),
        act=act_text or "",
        scene=scene_text or "",
        line=line,
        start_line=start_line,
        end_line=end_line,
        stage_index=stage_index,
    )


def _parse_annotation(raw: Any, diagnostics: list[AnnotationDiagnostic], seen_ids: set[str]) -> Annotation | None:
    start_len = len(diagnostics)
    if not isinstance(raw, dict):
        diagnostics.append(_diag("E_ANN_INVALID_JSON", "Each annotation must be a JSON object."))
        return None

    ann_id = _to_str(raw.get("id"))
    ann_type = _to_str(raw.get("type"))
    content = _to_str(raw.get("content"))
    status = _to_str(raw.get("status")) or "draft"
    resp = _to_str(raw.get("resp"))
    keywords_raw = raw.get("keywords", [])

    if ann_id is None:
        diagnostics.append(_diag("E_ANN_INVALID_JSON", "Annotation field 'id' must be a non-empty string.", field="id"))
    elif ann_id in seen_ids:
        diagnostics.append(
            _diag("E_ANN_DUPLICATE_ID", f"Duplicate annotation id: {ann_id}.", annotation_id=ann_id, field="id")
        )
    else:
        seen_ids.add(ann_id)

    if ann_type is None:
        diagnostics.append(_diag("E_ANN_INVALID_TYPE", "Annotation field 'type' must be a non-empty string.", annotation_id=ann_id))
    elif ann_type not in SUPPORTED_ANNOTATION_TYPES:
        diagnostics.append(
            _diag("E_ANN_INVALID_TYPE", f"Unsupported annotation type: {ann_type}.", annotation_id=ann_id, field="type")
        )

    if status not in SUPPORTED_ANNOTATION_STATUS:
        diagnostics.append(
            _diag("E_ANN_INVALID_STATUS", f"Unsupported annotation status: {status}.", annotation_id=ann_id, field="status")
        )

    if content is None:
        diagnostics.append(_diag("E_ANN_EMPTY_CONTENT", "Annotation content must be non-empty.", annotation_id=ann_id, field="content"))

    anchor_diagnostics: list[AnnotationDiagnostic] = []
    anchor = _parse_anchor(raw.get("anchor"), anchor_diagnostics, ann_id)
    diagnostics.extend(anchor_diagnostics)

    keywords: list[str] = []
    if not isinstance(keywords_raw, list):
        diagnostics.append(
            _diag(
                "E_ANN_INVALID_JSON",
                "Annotation field 'keywords' must be a list of strings.",
                annotation_id=ann_id,
                field="keywords",
            )
        )
    else:
        for index, item in enumerate(keywords_raw):
            keyword = _to_str(item)
            if keyword is None:
                diagnostics.append(
                    _diag(
                        "E_ANN_INVALID_JSON",
                        "Annotation keyword must be a non-empty string.",
                        annotation_id=ann_id,
                        field=f"keywords[{index}]",
                    )
                )
            else:
                keywords.append(keyword)

    if len(diagnostics) > start_len:
        return None

    if ann_id is None or ann_type is None or content is None or anchor is None:
        return None
    return Annotation(
        id=ann_id,
        type=ann_type,
        anchor=anchor,
        content=content,
        resp=resp,
        status=status,
        keywords=keywords,
    )


def _collection_to_payload(collection: AnnotationCollection) -> dict[str, Any]:
    annotations_payload: list[dict[str, Any]] = []
    for annotation in collection.annotations:
        anchor_payload: dict[str, Any] = {
            "kind": annotation.anchor.kind,
            "act": annotation.anchor.act,
            "scene": annotation.anchor.scene,
        }
        if annotation.anchor.kind == "line":
            anchor_payload["line"] = annotation.anchor.line
        elif annotation.anchor.kind == "line_range":
            anchor_payload["start_line"] = annotation.anchor.start_line
            anchor_payload["end_line"] = annotation.anchor.end_line
        elif annotation.anchor.kind == "stage":
            anchor_payload["stage_index"] = annotation.anchor.stage_index

        item: dict[str, Any] = {
            "id": annotation.id,
            "type": annotation.type,
            "anchor": anchor_payload,
            "content": annotation.content,
            "status": annotation.status,
            "keywords": annotation.keywords,
        }
        if annotation.resp:
            item["resp"] = annotation.resp
        annotations_payload.append(item)
    return {"version": collection.version, "annotations": annotations_payload}


def parse_annotations_payload(payload: Any) -> AnnotationCollection:
    diagnostics: list[AnnotationDiagnostic] = []
    if not isinstance(payload, dict):
        raise AnnotationValidationError([_diag("E_ANN_INVALID_JSON", "Top-level JSON value must be an object.")])

    version = payload.get("version")
    if version != 1:
        diagnostics.append(_diag("E_ANN_INVALID_JSON", "Field 'version' must be exactly 1.", field="version"))

    annotations_raw = payload.get("annotations")
    if not isinstance(annotations_raw, list):
        diagnostics.append(_diag("E_ANN_INVALID_JSON", "Field 'annotations' must be a list.", field="annotations"))
        raise AnnotationValidationError(diagnostics)

    seen_ids: set[str] = set()
    annotations: list[Annotation] = []
    for item in annotations_raw:
        annotation = _parse_annotation(item, diagnostics, seen_ids)
        if annotation is not None:
            annotations.append(annotation)

    if diagnostics:
        raise AnnotationValidationError(diagnostics)
    return AnnotationCollection(version=1, annotations=annotations)


def load_annotations(path: str | Path) -> AnnotationCollection:
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AnnotationValidationError(
            [_diag("E_ANN_INVALID_JSON", f"Invalid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno}).")]
        ) from exc
    return parse_annotations_payload(payload)


def save_annotations(collection: AnnotationCollection, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = _collection_to_payload(collection)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    target.write_text(serialized + "\n", encoding="utf-8")
    return target.resolve()
