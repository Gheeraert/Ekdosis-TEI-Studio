from __future__ import annotations

import re
import unicodedata
import xml.etree.ElementTree as ET

from ets.characters import resolve_speaker_block
from ets.collation.minor_variants import (
    VARIANT_ANA_CATEGORIES,
    format_ana_rule_code,
    subtype_for_candidate_class,
)
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

_XML_DECLARATION = '<?xml version="1.0" encoding="UTF-8"?>'
_TEI_PROFILE_ODD = "ets-racine.odd"
_TEI_PROFILE_RNC = "ets-racine.rnc"
_TEI_PROFILE_SCH = "ets-racine.sch"
_TEI_PROFILE_SCHEMA_KEYS = {
    "ets-racine",
    "ets-racine-rnc",
    "ets-racine-sch",
}
_TEI_PROFILE_SCHEMA_TYPES = {
    "projectODD",
    "validationRNC",
    "validationSchematron",
}
_VARIANT_TAXONOMY_ID = "ets-variant-taxonomy"


def _tei(tag: str) -> str:
    return f"{{{TEI_NS}}}{tag}"


def _tei_profile_href(profile_base_href: str, filename: str) -> str:
    if not profile_base_href:
        return filename
    return f"{profile_base_href.rstrip('/')}/{filename}"


def _xml_model_processing_instructions(*, profile_base_href: str) -> tuple[str, str]:
    rnc_href = _tei_profile_href(profile_base_href, _TEI_PROFILE_RNC)
    sch_href = _tei_profile_href(profile_base_href, _TEI_PROFILE_SCH)
    return (
        f'<?xml-model href="{rnc_href}" type="application/relax-ng-compact-syntax"?>',
        f'<?xml-model href="{sch_href}" type="application/xml" '
        'schematypens="http://purl.oclc.org/dsdl/schematron"?>',
    )


def _strip_tei_profile_xml_models(xml: str) -> str:
    pattern = re.compile(r"<\?xml-model\b[^?]*(?:ets-racine\.rnc|ets-racine\.sch)[^?]*\?>\s*")
    return pattern.sub("", xml)


def _prepend_xml_model_processing_instructions(xml: str, *, profile_base_href: str) -> str:
    xml = _strip_tei_profile_xml_models(xml).lstrip()
    processing_instructions = "\n".join(
        _xml_model_processing_instructions(profile_base_href=profile_base_href)
    )
    if xml.startswith("<?xml"):
        declaration_end = xml.find("?>")
        if declaration_end >= 0:
            declaration = _XML_DECLARATION
            rest = xml[declaration_end + 2 :].lstrip()
            return f"{declaration}\n{processing_instructions}\n{rest}"
    return f"{_XML_DECLARATION}\n{processing_instructions}\n{xml}"


def add_tei_profile_header_references(root: ET.Element, *, profile_base_href: str) -> None:
    tei_header = root.find(_tei("teiHeader"))
    if tei_header is None:
        tei_header = ET.SubElement(root, _tei("teiHeader"))

    encoding_desc = tei_header.find(_tei("encodingDesc"))
    if encoding_desc is None:
        file_desc = tei_header.find(_tei("fileDesc"))
        insert_at = list(tei_header).index(file_desc) + 1 if file_desc is not None else len(tei_header)
        encoding_desc = ET.Element(_tei("encodingDesc"))
        tei_header.insert(insert_at, encoding_desc)

    for schema_ref in list(encoding_desc.findall(_tei("schemaRef"))):
        if (
            schema_ref.get("key") in _TEI_PROFILE_SCHEMA_KEYS
            or schema_ref.get("type") in _TEI_PROFILE_SCHEMA_TYPES
            or "ets-racine." in (schema_ref.get("url") or "")
        ):
            encoding_desc.remove(schema_ref)

    odd_ref = ET.SubElement(
        encoding_desc,
        _tei("schemaRef"),
        {
            "key": "ets-racine",
            "type": "projectODD",
            "url": _tei_profile_href(profile_base_href, _TEI_PROFILE_ODD),
        },
    )
    ET.SubElement(odd_ref, _tei("desc")).text = (
        "Profil ODD ETS-Racine décrivant la TEI dramatique générée par Ekdosis-TEI Studio."
    )
    ET.SubElement(
        encoding_desc,
        _tei("schemaRef"),
        {
            "key": "ets-racine-rnc",
            "type": "validationRNC",
            "url": _tei_profile_href(profile_base_href, _TEI_PROFILE_RNC),
        },
    )
    ET.SubElement(
        encoding_desc,
        _tei("schemaRef"),
        {
            "key": "ets-racine-sch",
            "type": "validationSchematron",
            "url": _tei_profile_href(profile_base_href, _TEI_PROFILE_SCH),
        },
    )
    if _has_variant_ana(root):
        _ensure_variant_taxonomy(encoding_desc)


def _has_variant_ana(root: ET.Element) -> bool:
    return any(
        element.get("ana")
        for element in root.iter(_tei("app"))
        if element.get("type") == "minor"
    )


def _ensure_variant_taxonomy(encoding_desc: ET.Element) -> None:
    class_decl = encoding_desc.find(_tei("classDecl"))
    if class_decl is None:
        class_decl = ET.SubElement(encoding_desc, _tei("classDecl"))

    for taxonomy in list(class_decl.findall(_tei("taxonomy"))):
        if taxonomy.get(f"{{{XML_NS}}}id") == _VARIANT_TAXONOMY_ID:
            class_decl.remove(taxonomy)

    taxonomy = ET.SubElement(
        class_decl,
        _tei("taxonomy"),
        {f"{{{XML_NS}}}id": _VARIANT_TAXONOMY_ID},
    )
    for category_id, description in sorted(VARIANT_ANA_CATEGORIES.items()):
        category = ET.SubElement(
            taxonomy,
            _tei("category"),
            {f"{{{XML_NS}}}id": category_id},
        )
        ET.SubElement(category, _tei("catDesc")).text = description


def serialize_tei_with_profile_references(root: ET.Element, *, profile_base_href: str = "tei-profile/") -> str:
    add_tei_profile_header_references(root, profile_base_href=profile_base_href)
    tree = ET.ElementTree(root)
    ET.indent(tree, "  ")
    xml_body = ET.tostring(root, encoding="unicode")
    return _prepend_xml_model_processing_instructions(xml_body, profile_base_href=profile_base_href)


def with_tei_profile_references(xml: str, *, profile_base_href: str = "tei-profile/") -> str:
    root = ET.fromstring(_strip_tei_profile_xml_models(xml))
    return serialize_tei_with_profile_references(root, profile_base_href=profile_base_href)


def slugify_play_id(value: str) -> str:
    """Slug stable et compatible xml:id : minuscules, sans accent ni espace.

    Un xml:id ne peut pas commencer par un chiffre : un préfixe sûr est
    ajouté dans ce cas.
    """
    normalized = unicodedata.normalize("NFKD", value.strip())
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    if not slug:
        return "piece"
    if slug[0].isdigit():
        return f"p-{slug}"
    return slug


def resolve_play_id(config: EditionConfig) -> str:
    """Identifiant de pièce : ``config.play_id`` s'il est fourni, sinon le titre."""
    return slugify_play_id(config.play_id or config.title)


def tei_character_xml_id(character_id: str) -> str:
    """Return the TEI xml:id used for a character authority entry."""
    character_id = character_id.strip()
    if character_id.startswith("char-"):
        return character_id
    return f"char-{character_id}"


def _wit_attr(sigla: list[str]) -> str:
    return " ".join(f"#{siglum}" for siglum in sigla)


def _append_reading(parent: ET.Element, tag: str, reading: CollatedReading) -> ET.Element:
    element = ET.SubElement(parent, _tei(tag), {"wit": _wit_attr(reading.witness_sigla)})
    reading_text = reading.text
    if reading_text.strip() == "(lacune)":
        element.set("type", "omission")
        return element
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
                    app_attrs["ana"] = format_ana_rule_code(rule_code)
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
    if getattr(line, "part", None):
        attrs["part"] = line.part
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
    """Materialize missing xml:id values for dramatic acts, scenes and lines only.

    Structural identifiers are prefixed with the play identifier (the
    ``xml:id`` of the ``<text>`` element) when it is present, so that they
    stay unique across a multi-play corpus: ``bajazet-A1S1L70``.
    """

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

    text_element = root if root.tag == _tei("text") else root.find(f".//{_tei('text')}")
    play_id = _xml_id(text_element) if text_element is not None else None
    prefix = f"{play_id}-" if play_id else ""

    body = root.find(f".//{_tei('text')}/{_tei('body')}")
    if body is None:
        return

    act_index = 0
    for act in body:
        if act.tag != _tei("div") or (act.get("type") or "").strip().lower() != "act":
            continue
        act_index += 1
        act_ref = f"{prefix}A{act.get('n') or act_index}"
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
    profile_base_href: str = "tei-profile/",
) -> str:
    tei = ET.Element(_tei("TEI"), {f"{{{XML_NS}}}lang": "fr"})
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

    play_id = resolve_play_id(config)
    text = ET.SubElement(tei, _tei("text"), {"xml:id": play_id})
    if front_elements:
        front = ET.SubElement(text, _tei("front"))
        for element in front_elements:
            front.append(element)
    body = ET.SubElement(text, _tei("body"))
    implicit_counter = 0
    authority_characters = config.characters if characters is None else characters

    act_index = 0
    for act in collated.acts:
        is_prologue = act.kind == "prologue"
        if is_prologue:
            act_n = ""
            act_div = ET.SubElement(
                body,
                _tei("div"),
                {"type": "prologue", "xml:id": f"{play_id}-prologue"},
            )
        else:
            act_index += 1
            act_n = str(act_index)
            act_div = ET.SubElement(body, _tei("div"), {"type": "act", "n": act_n})
        head = ET.SubElement(act_div, _tei("head"))
        _append_collated_text(head, act.head)

        for scene_index, scene in enumerate(act.scenes, start=1):
            scene_n = str(scene_index)
            scene_div = (
                act_div
                if is_prologue
                else ET.SubElement(act_div, _tei("div"), {"type": "scene", "n": scene_n})
            )
            stage_index = 0
            line_id_prefix = (
                f"{play_id}-prologue-L"
                if is_prologue
                else f"{play_id}-A{act_n}S{scene_n}L"
            )

            def append_explicit_stage(parent: ET.Element, stage_text: CollatedText) -> None:
                nonlocal stage_index
                stage_index += 1
                stage_el = ET.SubElement(
                    parent,
                    _tei("stage"),
                    {
                        "xml:id": (
                            f"{play_id}-prologue-ST{stage_index}"
                            if is_prologue
                            else f"{play_id}-A{act_n}S{scene_n}ST{stage_index}"
                        )
                    },
                )
                _append_collated_text(stage_el, stage_text)

            if not is_prologue:
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
                        sp_attrs["who"] = f"#{tei_character_xml_id(resolution.character_id)}"
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
                                "xml:id": f"{play_id}-implicite{implicit_counter}",
                                "type": "DI",
                                "ana": f"#{element.category}",
                            },
                        )
                        for span_line in element.lines:
                            _append_collated_line(
                                span,
                                span_line,
                                line_xml_id=f"{line_id_prefix}{span_line.number}",
                            )
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
                                line_xml_id=f"{line_id_prefix}{stanza_line.number}",
                            )
                    else:
                        _append_collated_line(
                            sp,
                            element,
                            line_xml_id=f"{line_id_prefix}{element.number}",
                        )

    materialize_act_scene_line_xml_ids(tei)
    return serialize_tei_with_profile_references(tei, profile_base_href=profile_base_href)
