from __future__ import annotations

import xml.etree.ElementTree as ET

from .markdown import append_annotation_content
from .models import (
    Annotation,
    AnnotationCollection,
    AnnotationDiagnostic,
    AnnotationTargetNotFoundError,
)

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI_NS}


def _tei(tag: str) -> str:
    return f"{{{TEI_NS}}}{tag}"


def _line_target_id(act: str, scene: str, line: str) -> str:
    return f"A{act}S{scene}L{line}"


def _stage_target_id(act: str, scene: str, stage_index: int) -> str:
    return f"A{act}S{scene}ST{stage_index}"


def _int_to_roman(value: int) -> str | None:
    if value <= 0:
        return None
    mapping = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]
    remainder = value
    out: list[str] = []
    for step, symbol in mapping:
        while remainder >= step:
            out.append(symbol)
            remainder -= step
    return "".join(out)


def _roman_to_int(value: str) -> int | None:
    roman_map = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    text = value.strip().upper()
    if not text or any(char not in roman_map for char in text):
        return None
    total = 0
    prev = 0
    for char in reversed(text):
        current = roman_map[char]
        if current < prev:
            total -= current
        else:
            total += current
            prev = current
    if _int_to_roman(total) != text:
        return None
    return total


def _numeric_equivalents(token: str) -> list[str]:
    raw = token.strip()
    if not raw:
        return []
    values: list[str] = [raw]
    if raw.isdigit():
        arabic = str(int(raw))
        if arabic not in values:
            values.append(arabic)
        roman = _int_to_roman(int(raw))
        if roman and roman not in values:
            values.append(roman)
        return values

    roman_as_int = _roman_to_int(raw)
    if roman_as_int is not None:
        if raw.upper() not in values:
            values.append(raw.upper())
        arabic = str(roman_as_int)
        if arabic not in values:
            values.append(arabic)
    return values


def _resolve_scene_div(root: ET.Element, act: str, scene: str) -> tuple[ET.Element, str, str] | None:
    # Keep literal behavior first to avoid changing established ID resolution.
    literal_act = root.find(f".//tei:div[@type='act'][@n='{act}']", NS)
    if literal_act is not None:
        literal_scene = literal_act.find(f"./tei:div[@type='scene'][@n='{scene}']", NS)
        if literal_scene is not None:
            return literal_scene, act, scene

    # Compatibility layer: allow Arabic <-> Roman act/scene anchor equivalence.
    act_candidates = set(_numeric_equivalents(act))
    scene_candidates = set(_numeric_equivalents(scene))
    if not act_candidates:
        act_candidates.add(act)
    if not scene_candidates:
        scene_candidates.add(scene)

    for act_div in root.findall(".//tei:div[@type='act']", NS):
        act_n = act_div.get("n", "")
        if act_n not in act_candidates:
            continue
        for scene_div in act_div.findall("./tei:div[@type='scene']", NS):
            scene_n = scene_div.get("n", "")
            if scene_n in scene_candidates:
                return scene_div, act_n, scene_n
    return None


def _resolve_targets(
    root: ET.Element, annotation: Annotation
) -> tuple[list[str], ET.Element | None, AnnotationDiagnostic | None]:
    anchor = annotation.anchor
    if anchor.kind == "line" and anchor.line is not None:
        resolved_scene = _resolve_scene_div(root, anchor.act, anchor.scene)
        if resolved_scene is None:
            return [], None, None
        scene_div, act_n, scene_n = resolved_scene
        line = scene_div.find(f".//tei:l[@n='{anchor.line}']", NS)
        if line is None:
            return [], scene_div, None
        xml_id = line.get(f"{{{XML_NS}}}id") or _line_target_id(act_n, scene_n, anchor.line)
        return [f"#{xml_id}"], scene_div, None

    if anchor.kind == "line_range" and anchor.start_line is not None and anchor.end_line is not None:
        resolved_scene = _resolve_scene_div(root, anchor.act, anchor.scene)
        if resolved_scene is None:
            return [], None, None
        scene_div, _, _ = resolved_scene
        if not anchor.start_line.isdigit() or not anchor.end_line.isdigit():
            return [], scene_div, AnnotationDiagnostic(
                code="E_ANN_RANGE_DECIMAL_UNSUPPORTED",
                message="line_range supports only integer bounds in V1; use 'line' for shared/decimal verse numbers.",
                annotation_id=annotation.id,
            )
        start = int(anchor.start_line)
        end = int(anchor.end_line)
        targets: list[str] = []
        has_decimal_in_interval = False
        for line in scene_div.findall(".//tei:l", NS):
            n = line.get("n", "")
            if "." in n:
                base = n.split(".", maxsplit=1)[0]
                if base.isdigit() and start <= int(base) <= end:
                    has_decimal_in_interval = True
                continue
            if not n.isdigit():
                continue
            number = int(n)
            if start <= number <= end:
                xml_id = line.get(f"{{{XML_NS}}}id")
                if xml_id:
                    targets.append(f"#{xml_id}")
        if not targets and has_decimal_in_interval:
            return [], scene_div, AnnotationDiagnostic(
                code="E_ANN_RANGE_DECIMAL_UNSUPPORTED",
                message="line_range does not include shared/decimal verse lines in V1; use one or more 'line' anchors.",
                annotation_id=annotation.id,
            )
        return targets, scene_div, None

    if anchor.kind == "stage" and anchor.stage_index is not None:
        resolved_scene = _resolve_scene_div(root, anchor.act, anchor.scene)
        if resolved_scene is None:
            return [], None, None
        scene_div, act_n, scene_n = resolved_scene
        target_id = _stage_target_id(act_n, scene_n, anchor.stage_index)
        target = scene_div.find(f".//*[@xml:id='{target_id}']", {"xml": XML_NS})
        if target is not None:
            return [f"#{target_id}"], scene_div, None
        return [], scene_div, None

    return [], None, None


def _build_note(annotation: Annotation, targets: list[str]) -> ET.Element:
    attrs = {
        f"{{{XML_NS}}}id": annotation.id,
        "type": annotation.type,
        "target": " ".join(targets),
    }
    if annotation.resp:
        attrs["resp"] = annotation.resp
    attrs["ana"] = f"#{annotation.status}"
    if annotation.keywords:
        attrs["corresp"] = " ".join(f"#{keyword.replace(' ', '_')}" for keyword in annotation.keywords)

    note = ET.Element(_tei("note"), attrs)
    append_annotation_content(note, annotation.content)
    return note


def inject_annotations_into_tei(tei_xml: str, collection: AnnotationCollection) -> str:
    root = ET.fromstring(tei_xml)
    diagnostics: list[AnnotationDiagnostic] = []

    for annotation in collection.annotations:
        targets, scene_div, resolve_diagnostic = _resolve_targets(root, annotation)
        if resolve_diagnostic is not None:
            diagnostics.append(resolve_diagnostic)
            continue
        if not targets or scene_div is None:
            diagnostics.append(
                AnnotationDiagnostic(
                    code="E_ANN_TARGET_NOT_FOUND",
                    message=(
                        f"Unable to resolve annotation target for id={annotation.id}, "
                        f"kind={annotation.anchor.kind}, act={annotation.anchor.act}, scene={annotation.anchor.scene}."
                    ),
                    annotation_id=annotation.id,
                )
            )
            continue
        scene_div.append(_build_note(annotation, targets))

    if diagnostics:
        raise AnnotationTargetNotFoundError(diagnostics)

    tree = ET.ElementTree(root)
    ET.indent(tree, "  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")
