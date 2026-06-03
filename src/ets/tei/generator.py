from __future__ import annotations

import xml.etree.ElementTree as ET

from ets.characters import resolve_speaker_block
from ets.domain import (
    ApparatusLine,
    ApparatusTokenSegment,
    CollatedImplicitStageSpan,
    CollatedPlay,
    CollatedReading,
    CollatedStanza,
    CollatedStageDirection,
    CollatedText,
    EditionConfig,
    LiteralLine,
    LiteralTokenSegment,
    TokenCollatedLine,
)

TEI_NS = "http://www.tei-c.org/ns/1.0"
ET.register_namespace("", TEI_NS)


def _tei(tag: str) -> str:
    return f"{{{TEI_NS}}}{tag}"


def _wit_attr(sigla: list[str]) -> str:
    return " ".join(f"#{siglum}" for siglum in sigla)


def _append_reading(parent: ET.Element, tag: str, reading: CollatedReading) -> None:
    element = ET.SubElement(parent, _tei(tag), {"wit": _wit_attr(reading.witness_sigla)})
    _append_inline_italics(element, None, reading.text.replace("_", ""))


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

    for segment in text.segments:
        if isinstance(segment, LiteralTokenSegment):
            append_literal_segment(segment.text)
            continue
        if isinstance(segment, ApparatusTokenSegment):
            if not italic_open and has_open_marker_in_apparatus(segment):
                italic_open = True
                italic_element = ET.SubElement(parent, _tei("hi"), {"rend": "italic"})
                last_child = italic_element
                italic_last_child = None

            app_parent = italic_element if italic_open and italic_element is not None else parent
            app = ET.SubElement(app_parent, _tei("app"))
            _append_reading(app, "lem", segment.lemma)
            for rdg in segment.readings:
                _append_reading(app, "rdg", rdg)
            if italic_open and italic_element is not None:
                italic_last_child = app
            else:
                last_child = app

            if italic_open and has_close_marker_in_apparatus(segment):
                italic_open = False
                italic_element = None
                italic_last_child = None


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


def generate_tei_xml(collated: CollatedPlay, config: EditionConfig) -> str:
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
    body = ET.SubElement(text, _tei("body"))
    implicit_counter = 0

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
                if config.characters and speech.speaker_readings:
                    resolution = resolve_speaker_block(speech.speaker_readings, config.characters)
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

    tree = ET.ElementTree(tei)
    ET.indent(tree, "  ")
    return ET.tostring(tei, encoding="utf-8", xml_declaration=True).decode("utf-8")
