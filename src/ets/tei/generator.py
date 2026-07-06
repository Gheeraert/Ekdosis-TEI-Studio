from __future__ import annotations

import xml.etree.ElementTree as ET

from ets.characters import resolve_speaker_block
from ets.collation.minor_variants import subtype_for_candidate_class
from ets.tei.terminal_punctuation import normalize_terminal_punctuation_segments
from ets.domain import (
    ApparatusLine,
    ApparatusTokenSegment,
    CollatedImplicitStageSpan,
    CollatedPlay,
    CollatedReading,
    CollatedStanza,
    CollatedStageDirection,
    CollatedText,
    Character,
    EditionConfig,
    LiteralLine,
    LiteralTokenSegment,
    TokenCollatedLine,
)

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("", TEI_NS)


def _tei(tag: str) -> str:
    return f"{{{TEI_NS}}}{tag}"


def _wit_attr(sigla: list[str]) -> str:
    return " ".join(f"#{siglum}" for siglum in sigla)


def _append_reading(parent: ET.Element, tag: str, reading: CollatedReading) -> ET.Element:
    element = ET.SubElement(parent, _tei(tag), {"wit": _wit_attr(reading.witness_sigla)})
    reading_text = reading.text
    if reading_text.count("_") % 2 != 0:
        stripped = reading_text.strip()
        if stripped.startswith("_"):
            leading = reading_text[: reading_text.find("_")]
            content = reading_text[reading_text.find("_") + 1 :]
            _append_text(element, None, leading)
            hi = ET.SubElement(element, _tei("hi"), {"rend": "italic"})
            hi.text = content
            return element
        if stripped.endswith("_"):
            marker = reading_text.rfind("_")
            content = reading_text[:marker]
            trailing = reading_text[marker + 1 :]
            hi = ET.SubElement(element, _tei("hi"), {"rend": "italic"})
            hi.text = content
            hi.tail = trailing
            return element
        reading_text = reading_text.replace("_", "")
    _append_inline_italics(element, None, reading_text)
    return element


def _append_text(container: ET.Element, last_child: ET.Element | None, text: str) -> None:
    if not text:
        return
    if last_child is None:
        container.text = (container.text or "") + text
    else:
        last_child.tail = (last_child.tail or "") + text


def _append_inline_italics(
    container: ET.Element,
    last_child: ET.Element | None,
    text: str,
) -> ET.Element | None:
    if not text:
        return last_child

    cursor = 0
    while cursor < len(text):
        start = text.find("_", cursor)
        if start < 0:
            _append_text(container, last_child, text[cursor:])
            break

        end = text.find("_", start + 1)
        if end < 0:
            _append_text(container, last_child, text[cursor:])
            break

        if start > cursor:
            _append_text(container, last_child, text[cursor:start])

        content = text[start + 1 : end]
        if content:
            hi = ET.SubElement(container, _tei("hi"), {"rend": "italic"})
            hi.text = content
            last_child = hi
        else:
            _append_text(container, last_child, text[start : end + 1])

        cursor = end + 1

    return last_child


def _append_collated_text(parent: ET.Element, text: CollatedText) -> None:
    segments = normalize_terminal_punctuation_segments(text.segments)
    last_child: ET.Element | None = None
    italic_open = False
    italic_element: ET.Element | None = None
    italic_last_child: ET.Element | None = None

    def append_literal_segment(segment_text: str) -> None:
        nonlocal last_child, italic_open, italic_element, italic_last_child
        cursor = 0
        while cursor < len(segment_text):
            marker = segment_text.find("_", cursor)
            if marker < 0:
                chunk = segment_text[cursor:]
                if italic_open and italic_element is not None:
                    _append_text(italic_element, italic_last_child, chunk)
                else:
                    _append_text(parent, last_child, chunk)
                break

            if marker > cursor:
                chunk = segment_text[cursor:marker]
                if italic_open and italic_element is not None:
                    _append_text(italic_element, italic_last_child, chunk)
                else:
                    _append_text(parent, last_child, chunk)

            if italic_open:
                italic_open = False
                italic_element = None
                italic_last_child = None
            else:
                italic_open = True
                italic_element = ET.SubElement(parent, _tei("hi"), {"rend": "italic"})
                last_child = italic_element
                italic_last_child = None
            cursor = marker + 1

    def has_open_marker_in_apparatus(segment: ApparatusTokenSegment) -> bool:
        readings = [segment.lemma, *segment.readings]
        return any(item.text.lstrip().startswith("_") for item in readings if item.text)

    def has_close_marker_in_apparatus(segment: ApparatusTokenSegment) -> bool:
        readings = [segment.lemma, *segment.readings]
        return any(item.text.rstrip().endswith("_") for item in readings if item.text)

    def has_italic_markup_variant(segment: ApparatusTokenSegment) -> bool:
        readings = [segment.lemma, *segment.readings]
        raw_texts = {item.text for item in readings}
        plain_texts = {item.text.replace("_", "") for item in readings}
        return len(raw_texts) > 1 and len(plain_texts) == 1

    def markup_variant_opens_italic(segment: ApparatusTokenSegment) -> bool:
        readings = [segment.lemma, *segment.readings]
        return any(item.text.lstrip().startswith("_") for item in readings if item.text)

    def markup_variant_closes_italic(segment: ApparatusTokenSegment) -> bool:
        readings = [segment.lemma, *segment.readings]
        return any(item.text.rstrip().endswith("_") for item in readings if item.text)

    def reading_has_edge_italic(reading: CollatedReading) -> bool:
        return reading.text.lstrip().startswith("_") or reading.text.rstrip().endswith("_")

    def wrap_italic_if_needed(value: str, italic: bool) -> str:
        return f"_{value}_" if italic else value

    def compatible_witnesses(opening: CollatedReading, closing: CollatedReading) -> list[str]:
        closing_sigla = set(closing.witness_sigla)
        return [siglum for siglum in opening.witness_sigla if siglum in closing_sigla]

    def matching_opening_reading(
        readings: list[CollatedReading],
        closing: CollatedReading,
    ) -> tuple[CollatedReading, list[str]] | None:
        matches = [
            (reading, compatible_witnesses(reading, closing))
            for reading in readings
            if reading_has_edge_italic(reading) == reading_has_edge_italic(closing)
        ]
        matches = [(reading, sigla) for reading, sigla in matches if sigla]
        if len(matches) == 1:
            return matches[0]
        return None

    def find_grouped_italic_variant_end(start_index: int) -> int | None:
        for candidate_index in range(start_index + 1, len(segments)):
            candidate = segments[candidate_index]
            if isinstance(candidate, LiteralTokenSegment):
                continue
            if not isinstance(candidate, ApparatusTokenSegment):
                return None
            if markup_variant_closes_italic(candidate):
                return candidate_index
            return None
        return None

    def append_grouped_italic_variant(start_index: int, end_index: int) -> bool:
        nonlocal last_child
        start_segment = segments[start_index]
        end_segment = segments[end_index]
        if not isinstance(start_segment, ApparatusTokenSegment) or not isinstance(end_segment, ApparatusTokenSegment):
            raise TypeError("Grouped italic variant boundaries must be apparatus segments.")

        middle = "".join(
            segment.text
            for segment in segments[start_index + 1 : end_index]
            if isinstance(segment, LiteralTokenSegment)
        )
        opening_readings = [start_segment.lemma, *start_segment.readings]
        closing_readings = [end_segment.lemma, *end_segment.readings]
        grouped_readings: list[tuple[str, CollatedReading]] = []
        for closing in closing_readings:
            # Long italic variant boundaries must be witness-aware to avoid hybrid readings.
            matched = matching_opening_reading(opening_readings, closing)
            if matched is None:
                return False
            opening, witness_sigla = matched
            italic = reading_has_edge_italic(opening)
            reading_text = opening.text.replace("_", "") + middle + closing.text.replace("_", "")
            tag = "lem" if not grouped_readings else "rdg"
            grouped_readings.append(
                (
                    tag,
                    CollatedReading(
                        text=wrap_italic_if_needed(reading_text, italic),
                        witness_sigla=witness_sigla,
                    ),
                )
            )

        app = ET.SubElement(parent, _tei("app"))
        for tag, reading in grouped_readings:
            _append_reading(app, tag, reading)
        last_child = app
        return True

    index = 0
    while index < len(segments):
        segment = segments[index]
        if isinstance(segment, LiteralTokenSegment):
            append_literal_segment(segment.text)
            index += 1
            continue
        if isinstance(segment, ApparatusTokenSegment):
            markup_variant = has_italic_markup_variant(segment)
            opens_markup_variant = markup_variant and markup_variant_opens_italic(segment)
            closes_markup_variant = markup_variant and markup_variant_closes_italic(segment)
            if opens_markup_variant and not closes_markup_variant and not italic_open:
                grouped_end = find_grouped_italic_variant_end(index)
                if grouped_end is not None:
                    if append_grouped_italic_variant(index, grouped_end):
                        index = grouped_end + 1
                        continue
            if markup_variant and closes_markup_variant and italic_open:
                italic_open = False
                italic_element = None
                italic_last_child = None
            if not markup_variant and not italic_open and has_open_marker_in_apparatus(segment):
                italic_open = True
                italic_element = ET.SubElement(parent, _tei("hi"), {"rend": "italic"})
                last_child = italic_element
                italic_last_child = None

            app_parent = italic_element if not markup_variant and italic_open and italic_element is not None else parent
            app_attrs: dict[str, str] = {}
            if getattr(segment, "visibility_policy", "visible") in {"hide_safe", "inspect"}:
                app_attrs["type"] = "minor"
                candidate_class = getattr(segment, "candidate_class", "minor")
                subtype = subtype_for_candidate_class(candidate_class)
                app_attrs["subtype"] = subtype
                rule_code = getattr(segment, "rule_code", "")
                if rule_code:
                    app_attrs["ana"] = f"#{rule_code}"
                if getattr(segment, "visibility_policy", "visible") == "inspect":
                    app_attrs["cert"] = "low"
            app = ET.SubElement(app_parent, _tei("app"), app_attrs)
            punctuation_only = (
                getattr(segment, "candidate_class", "") == "minor_punctuation"
                or getattr(segment, "rule_code", "") == "punctuation_only"
            )
            lem_element = _append_reading(app, "lem", segment.lemma)
            if punctuation_only and not segment.lemma.text:
                lem_element.set("type", "omission")
            for rdg in segment.readings:
                rdg_element = _append_reading(app, "rdg", rdg)
                if punctuation_only and not rdg.text:
                    rdg_element.set("type", "omission")
            if not markup_variant and italic_open and italic_element is not None:
                italic_last_child = app
            else:
                last_child = app

            if opens_markup_variant and not closes_markup_variant and not italic_open:
                italic_open = True
                italic_element = ET.SubElement(parent, _tei("hi"), {"rend": "italic"})
                last_child = italic_element
                italic_last_child = None

            if not markup_variant and italic_open and has_close_marker_in_apparatus(segment):
                italic_open = False
                italic_element = None
                italic_last_child = None
        index += 1


def _append_collated_line(
    parent: ET.Element,
    line: LiteralLine | ApparatusLine | TokenCollatedLine,
    *,
    line_xml_id: str | None = None,
) -> None:
    attrs = {"n": line.number}
    if line_xml_id:
        attrs["xml:id"] = line_xml_id
    if getattr(line, "met", None):
        attrs["met"] = line.met
    l_element = ET.SubElement(parent, _tei("l"), attrs)
    if isinstance(line, TokenCollatedLine):
        _append_collated_text(l_element, line.text)
        return

    if isinstance(line, LiteralLine):
        _append_inline_italics(l_element, None, line.text)
        return

    app = ET.SubElement(l_element, _tei("app"))
    _append_reading(app, "lem", line.lemma)
    for rdg in line.readings:
        _append_reading(app, "rdg", rdg)


def _xml_id(element: ET.Element) -> str | None:
    return element.get(f"{{{XML_NS}}}id") or element.get("xml:id")


def _set_xml_id(element: ET.Element, value: str) -> None:
    element.attrib.pop("xml:id", None)
    element.set(f"{{{XML_NS}}}id", value)


def _reserve_xml_id(candidate: str, used: set[str]) -> str:
    if candidate not in used:
        used.add(candidate)
        return candidate
    suffix = 2
    while f"{candidate}-{suffix}" in used:
        suffix += 1
    value = f"{candidate}-{suffix}"
    used.add(value)
    return value


def materialize_act_scene_line_xml_ids(root: ET.Element) -> None:
    """Materialize missing xml:id values for dramatic acts, scenes and lines only."""

    for element in root.iter():
        literal_id = element.get("xml:id")
        namespaced_id = element.get(f"{{{XML_NS}}}id")
        if literal_id and not namespaced_id:
            _set_xml_id(element, literal_id)

    used_ids = {
        value
        for element in root.iter()
        for value in [_xml_id(element)]
        if value
    }

    body = root.find(f".//{_tei('text')}/{_tei('body')}")
    if body is None:
        return

    act_index = 0
    for act in body:
        if act.tag != _tei("div") or (act.get("type") or "").strip().lower() != "act":
            continue
        act_index += 1
        act_ref = f"A{act.get('n') or act_index}"
        if not _xml_id(act):
            _set_xml_id(act, _reserve_xml_id(act_ref, used_ids))

        scene_index = 0
        for scene in act:
            if scene.tag != _tei("div") or (scene.get("type") or "").strip().lower() != "scene":
                continue
            scene_index += 1
            scene_ref = f"{act_ref}S{scene.get('n') or scene_index}"
            if not _xml_id(scene):
                _set_xml_id(scene, _reserve_xml_id(scene_ref, used_ids))

            for line in scene.iter(_tei("l")):
                if _xml_id(line):
                    continue
                line_n = (line.get("n") or "").strip()
                if not line_n:
                    continue
                _set_xml_id(line, _reserve_xml_id(f"{scene_ref}L{line_n}", used_ids))


def generate_tei_xml(
    collated: CollatedPlay,
    config: EditionConfig,
    *,
    front_elements: list[ET.Element] | None = None,
    characters: list[Character] | None = None,
) -> str:
    tei = ET.Element(_tei("TEI"))
    tei_header = ET.SubElement(tei, _tei("teiHeader"))
    file_desc = ET.SubElement(tei_header, _tei("fileDesc"))
    title_stmt = ET.SubElement(file_desc, _tei("titleStmt"))
    ET.SubElement(title_stmt, _tei("title")).text = config.title
    ET.SubElement(title_stmt, _tei("author")).text = config.author
    if config.editor:
        editor = ET.SubElement(title_stmt, _tei("editor"), {"role": "scientific"})
        editor.text = config.editor
    if config.transcriber:
        resp_stmt = ET.SubElement(title_stmt, _tei("respStmt"))
        ET.SubElement(resp_stmt, _tei("resp")).text = "Transcription"
        ET.SubElement(resp_stmt, _tei("name"), {"role": "transcriber"}).text = config.transcriber

    publication_stmt = ET.SubElement(file_desc, _tei("publicationStmt"))
    ET.SubElement(publication_stmt, _tei("p")).text = "Generated by Ekdosis TEI Studio v2 core"

    source_desc = ET.SubElement(file_desc, _tei("sourceDesc"))

    if config.witnesses:
        list_wit = ET.SubElement(source_desc, _tei("listWit"))
        for witness in config.witnesses:
            wit = ET.SubElement(list_wit, _tei("witness"), {"xml:id": witness.siglum})
            wit.text = f"{witness.siglum} ({witness.year}) {witness.description}".strip()
    else:
        ET.SubElement(source_desc, _tei("p")).text = "Generated from plain-text parallel witnesses."

    text = ET.SubElement(tei, _tei("text"))
    if front_elements:
        front = ET.SubElement(text, _tei("front"))
        for element in front_elements:
            front.append(element)
    body = ET.SubElement(text, _tei("body"))
    implicit_counter = 0
    authority_characters = config.characters if characters is None else characters

    for act_index, act in enumerate(collated.acts, start=1):
        act_n = str(act_index)
        act_div = ET.SubElement(body, _tei("div"), {"type": "act", "n": act_n})
        head = ET.SubElement(act_div, _tei("head"))
        _append_collated_text(head, act.head)

        for scene_index, scene in enumerate(act.scenes, start=1):
            scene_n = str(scene_index)
            scene_div = ET.SubElement(act_div, _tei("div"), {"type": "scene", "n": scene_n})
            stage_index = 0

            def append_explicit_stage(parent: ET.Element, stage_text: CollatedText) -> None:
                nonlocal stage_index
                stage_index += 1
                stage_el = ET.SubElement(
                    parent,
                    _tei("stage"),
                    {"xml:id": f"A{act_n}S{scene_n}ST{stage_index}"},
                )
                _append_collated_text(stage_el, stage_text)

            scene_head = ET.SubElement(scene_div, _tei("head"))
            _append_collated_text(scene_head, scene.head)
            if scene.cast:
                stage_cast = ET.SubElement(scene_div, _tei("stage"), {"type": "personnages"})
                _append_collated_text(stage_cast, scene.cast)
            for stage in scene.stage_directions:
                append_explicit_stage(scene_div, stage.text)

            for speech in scene.speeches:
                sp_attrs: dict[str, str] = {}
                if authority_characters and speech.speaker_readings:
                    resolution = resolve_speaker_block(speech.speaker_readings, authority_characters)
                    if resolution.status == "resolved" and resolution.character_id is not None:
                        sp_attrs["who"] = f"#{resolution.character_id}"
                sp = ET.SubElement(scene_div, _tei("sp"), sp_attrs)
                speaker = ET.SubElement(sp, _tei("speaker"))
                _append_collated_text(speaker, speech.speaker)
                for element in speech.elements:
                    if isinstance(element, CollatedStageDirection):
                        append_explicit_stage(sp, element.text)
                    elif isinstance(element, CollatedImplicitStageSpan):
                        implicit_counter += 1
                        span = ET.SubElement(
                            sp,
                            _tei("stage"),
                            {
                                "xml:id": f"implicite{implicit_counter}",
                                "type": "DI",
                                "ana": f"#{element.category}",
                            },
                        )
                        for span_line in element.lines:
                            _append_collated_line(span, span_line, line_xml_id=f"A{act_n}S{scene_n}L{span_line.number}")
                    elif isinstance(element, CollatedStanza):
                        attrs = {"type": "stanza"}
                        if element.subtype:
                            attrs["subtype"] = element.subtype
                        if element.rhyme:
                            attrs["rhyme"] = element.rhyme
                        lg = ET.SubElement(sp, _tei("lg"), attrs)
                        for stanza_line in element.lines:
                            _append_collated_line(
                                lg,
                                stanza_line,
                                line_xml_id=f"A{act_n}S{scene_n}L{stanza_line.number}",
                            )
                    else:
                        _append_collated_line(sp, element, line_xml_id=f"A{act_n}S{scene_n}L{element.number}")

    materialize_act_scene_line_xml_ids(tei)
    tree = ET.ElementTree(tei)
    ET.indent(tree, "  ")
    return ET.tostring(tei, encoding="utf-8", xml_declaration=True).decode("utf-8")
