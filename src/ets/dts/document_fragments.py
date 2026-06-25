from __future__ import annotations

from collections.abc import Callable, Iterator
from copy import deepcopy
from pathlib import Path
from urllib.parse import quote

from lxml import etree

from .models import DTSNavNode, DTSTeiIndex

TEI_NS = "http://www.tei-c.org/ns/1.0"
DTS_NS = "https://w3id.org/api/dts#"


def encoded_reference(reference: str) -> str:
    return quote(reference, safe="-._~")


def fragment_document_relpath(slug: str, reference: str) -> Path:
    return Path("api") / "dts" / "document" / slug / f"{encoded_reference(reference)}.xml"


def _parse_source(source_path: Path) -> etree._ElementTree:
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    return etree.parse(str(source_path), parser)


def _source_nodes(
    tree: etree._ElementTree,
    index: DTSTeiIndex,
) -> Iterator[tuple[DTSNavNode, etree._Element]]:
    acts = tree.xpath(
        "//*[local-name()='text']/*[local-name()='body']/*[local-name()='div'][@type='act']"
    )
    for act_node, act_element in zip(index.navigation, acts, strict=True):
        yield act_node, act_element
        scenes = act_element.xpath("./*[local-name()='div'][@type='scene']")
        for scene_node, scene_element in zip(act_node.children, scenes, strict=True):
            yield scene_node, scene_element
            lines = scene_element.xpath(".//*[local-name()='l']")
            for line_node, line_element in zip(scene_node.children, lines, strict=True):
                yield line_node, line_element


def _line_content(line: etree._Element) -> etree._Element:
    speech = next(
        (
            ancestor
            for ancestor in line.iterancestors()
            if etree.QName(ancestor).localname == "sp"
        ),
        None,
    )
    if speech is None:
        return deepcopy(line)

    reduced_speech = etree.Element(speech.tag, attrib=dict(speech.attrib), nsmap=speech.nsmap)
    for child in speech:
        if etree.QName(child).localname == "speaker":
            reduced_speech.append(deepcopy(child))
    reduced_speech.append(deepcopy(line))
    return reduced_speech


def _fragment_xml(
    tree: etree._ElementTree,
    node: DTSNavNode,
    source_element: etree._Element,
) -> bytes:
    root = etree.Element(
        f"{{{TEI_NS}}}TEI",
        nsmap={None: TEI_NS, "dts": DTS_NS},
    )
    headers = tree.xpath("/*[local-name()='TEI']/*[local-name()='teiHeader'][1]")
    if headers:
        root.append(deepcopy(headers[0]))
    else:
        etree.SubElement(root, f"{{{TEI_NS}}}teiHeader")

    text = etree.SubElement(root, f"{{{TEI_NS}}}text")
    body = etree.SubElement(text, f"{{{TEI_NS}}}body")
    fragment = etree.SubElement(body, f"{{{DTS_NS}}}fragment")
    fragment.set("ref", node.identifier)
    content = _line_content(source_element) if node.cite_type == "line" else deepcopy(source_element)
    fragment.append(content)
    return etree.tostring(
        root,
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=True,
    )


def export_document_fragments(
    output_root: Path,
    index: DTSTeiIndex,
    *,
    safe_target: Callable[[Path, Path], Path],
) -> tuple[str, ...]:
    slug = index.resource.slug
    warnings: list[str] = []
    try:
        tree = _parse_source(index.resource.source_path)
        source_nodes = list(_source_nodes(tree, index))
    except Exception as exc:
        return tuple(
            f"DTS fragment export skipped for {slug}/{node.identifier}: {exc}"
            for node in _flatten(index.navigation)
        )

    for node, source_element in source_nodes:
        try:
            target = safe_target(output_root, fragment_document_relpath(slug, node.identifier))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(_fragment_xml(tree, node, source_element))
        except Exception as exc:
            warnings.append(
                f"DTS fragment export skipped for {slug}/{node.identifier}: {exc}"
            )
    return tuple(warnings)


def _flatten(nodes: tuple[DTSNavNode, ...]) -> Iterator[DTSNavNode]:
    for node in nodes:
        yield node
        yield from _flatten(node.children)
