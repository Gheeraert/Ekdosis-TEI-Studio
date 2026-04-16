from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from lxml import etree


TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
XML_ID = f"{{{XML_NS}}}id"
REF_ATTRS = (
    "ana",
    "corresp",
    "copyOf",
    "exclude",
    "next",
    "passive",
    "prev",
    "ref",
    "resp",
    "sameAs",
    "select",
    "synch",
    "target",
    "who",
    "wit",
)


class DramaticTeiMergeError(ValueError):
    """Raised when dramatic TEI files cannot be merged safely."""


@dataclass(frozen=True)
class DramaticTeiMergeRequest:
    act_xml_paths: tuple[Path, ...]
    output_path: Path | None = None
    collision_policy: Literal["rename_on_collision", "prefix_all"] = "rename_on_collision"
    xml_id_prefix_template: str = "a{index}_"
    title_override: str | None = None


@dataclass(frozen=True)
class DramaticTeiMergeResult:
    merged_xml: str
    merged_act_count: int
    warnings: tuple[str, ...] = ()
    output_path: Path | None = None


@dataclass(frozen=True)
class _ParsedActDocument:
    source_path: Path
    tree: etree._ElementTree
    header: etree._Element
    body: etree._Element
    act_divisions: tuple[etree._Element, ...]
    title: str | None
    author: str | None
    witness_ids: tuple[str, ...]
    header_signature: bytes


def _first_text(tree: etree._ElementTree, xpath: str) -> str | None:
    values = tree.xpath(xpath)
    if not values:
        return None
    first = values[0]
    if isinstance(first, etree._Element):
        text = " ".join(first.itertext()).strip()
        return text or None
    text = str(first).strip()
    return text or None


def _header_signature(header: etree._Element) -> bytes:
    # Canonical bytes allow deterministic "same/different header" checks.
    return etree.tostring(header, method="c14n", exclusive=False, with_comments=False)


def _normalize(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(value.split()).casefold()


def _collect_duplicate_xml_ids(root: etree._Element) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for node in root.iter():
        xml_id = node.get(XML_ID)
        if not xml_id:
            continue
        if xml_id in seen and xml_id not in duplicates:
            duplicates.append(xml_id)
        seen.add(xml_id)
    return tuple(duplicates)


def _collect_xml_ids(root: etree._Element) -> set[str]:
    xml_ids: set[str] = set()
    for node in root.iter():
        value = node.get(XML_ID)
        if value:
            xml_ids.add(value)
    return xml_ids


def _parse_act_document(source_path: Path) -> _ParsedActDocument:
    resolved = source_path.resolve()
    if not resolved.exists() or not resolved.is_file():
        raise DramaticTeiMergeError(f"Missing dramatic TEI input file: '{source_path}'.")

    parser = etree.XMLParser(recover=False, remove_blank_text=False)
    try:
        tree = etree.parse(str(resolved), parser)
    except (OSError, etree.XMLSyntaxError) as exc:
        raise DramaticTeiMergeError(f"Cannot parse dramatic TEI file '{resolved}': {exc}") from exc

    root = tree.getroot()
    if etree.QName(root).localname != "TEI":
        raise DramaticTeiMergeError(f"Input file '{resolved}' is not a TEI root document.")

    duplicate_ids = _collect_duplicate_xml_ids(root)
    if duplicate_ids:
        preview = ", ".join(duplicate_ids[:5])
        raise DramaticTeiMergeError(f"Input file '{resolved}' contains duplicate xml:id values: {preview}.")

    headers = root.xpath("./*[local-name()='teiHeader']")
    if not headers:
        raise DramaticTeiMergeError(f"Input file '{resolved}' has no teiHeader.")
    header = headers[0]

    bodies = root.xpath("./*[local-name()='text']/*[local-name()='body']")
    if not bodies:
        raise DramaticTeiMergeError(f"Input file '{resolved}' has no text/body.")
    body = bodies[0]

    act_divisions = tuple(body.xpath("./*[local-name()='div' and @type='act']"))
    if not act_divisions:
        raise DramaticTeiMergeError(
            f"Input file '{resolved}' does not expose direct body/div[@type='act'] content."
        )

    title = _first_text(
        tree,
        "string((//*[local-name()='teiHeader']//*[local-name()='titleStmt']/*[local-name()='title'])[1])",
    )
    author = _first_text(
        tree,
        "string((//*[local-name()='teiHeader']//*[local-name()='titleStmt']/*[local-name()='author'])[1])",
    )

    witness_ids = tuple(
        node.get(XML_ID)
        for node in root.xpath("//*[local-name()='listWit']/*[local-name()='witness']")
        if isinstance(node, etree._Element) and node.get(XML_ID)
    )

    return _ParsedActDocument(
        source_path=resolved,
        tree=tree,
        header=header,
        body=body,
        act_divisions=act_divisions,
        title=title,
        author=author,
        witness_ids=tuple(sorted(set(witness_ids))),
        header_signature=_header_signature(header),
    )


def _build_id_prefix(template: str, index: int) -> str:
    try:
        prefix = template.format(index=index)
    except (KeyError, IndexError, ValueError) as exc:
        raise DramaticTeiMergeError(
            "Invalid xml_id_prefix_template. Use a valid format string, for example 'a{index}_'."
        ) from exc
    prefix = prefix.strip()
    if not prefix:
        raise DramaticTeiMergeError("xml_id_prefix_template must produce a non-empty prefix.")
    return prefix


def _remap_ids_in_subtree(
    subtree: etree._Element,
    *,
    existing_ids: set[str],
    prefix: str,
    collision_policy: Literal["rename_on_collision", "prefix_all"],
) -> tuple[dict[str, str], list[str]]:
    id_map: dict[str, str] = {}
    warnings: list[str] = []

    for node in subtree.iter():
        xml_id = node.get(XML_ID)
        if not xml_id:
            continue

        should_rename = collision_policy == "prefix_all" or xml_id in existing_ids
        if not should_rename:
            existing_ids.add(xml_id)
            continue

        base = f"{prefix}{xml_id}"
        candidate = base
        counter = 2
        while candidate in existing_ids:
            candidate = f"{base}_{counter}"
            counter += 1

        node.set(XML_ID, candidate)
        id_map[xml_id] = candidate
        existing_ids.add(candidate)
        warnings.append(f"Renamed colliding xml:id '{xml_id}' to '{candidate}'.")

    return id_map, warnings


def _rewrite_reference_tokens(value: str, id_map: dict[str, str]) -> str:
    if not id_map:
        return value
    tokens = value.split()
    if not tokens:
        return value

    changed = False
    rewritten: list[str] = []
    for token in tokens:
        if token.startswith("#"):
            old = token[1:]
            new = id_map.get(old)
            if new:
                rewritten.append(f"#{new}")
                changed = True
                continue
        rewritten.append(token)
    return " ".join(rewritten) if changed else value


def _rewrite_references_in_subtree(subtree: etree._Element, id_map: dict[str, str]) -> None:
    if not id_map:
        return
    for node in subtree.iter():
        for attr in REF_ATTRS:
            value = node.get(attr)
            if not value:
                continue
            rewritten = _rewrite_reference_tokens(value, id_map)
            if rewritten != value:
                node.set(attr, rewritten)


def _apply_title_override(root: etree._Element, title_override: str) -> None:
    titles = root.xpath(
        "./*[local-name()='teiHeader']//*[local-name()='titleStmt']/*[local-name()='title']"
    )
    if titles:
        titles[0].text = title_override
        return

    title_stmts = root.xpath("./*[local-name()='teiHeader']//*[local-name()='titleStmt']")
    if not title_stmts:
        raise DramaticTeiMergeError("Cannot apply title override: teiHeader/titleStmt is missing.")

    etree.SubElement(title_stmts[0], f"{{{TEI_NS}}}title").text = title_override


def _validate_compatibility(documents: tuple[_ParsedActDocument, ...]) -> tuple[str | None, str | None, tuple[str, ...]]:
    first = documents[0]
    warnings: list[str] = []

    for index, document in enumerate(documents[1:], start=2):
        if _normalize(first.title) and _normalize(document.title) and _normalize(first.title) != _normalize(document.title):
            raise DramaticTeiMergeError(
                f"Incompatible merge input at position {index}: title differs ('{document.title}' vs '{first.title}')."
            )
        if _normalize(first.author) and _normalize(document.author) and _normalize(first.author) != _normalize(document.author):
            raise DramaticTeiMergeError(
                f"Incompatible merge input at position {index}: author differs ('{document.author}' vs '{first.author}')."
            )
        if document.header_signature != first.header_signature:
            warnings.append(
                f"Header differs for '{document.source_path.name}'; keeping teiHeader from first file '{first.source_path.name}'."
            )
        if first.witness_ids and document.witness_ids and document.witness_ids != first.witness_ids:
            warnings.append(
                f"Witness declarations differ in '{document.source_path.name}' compared to first file."
            )

    return first.title, first.author, tuple(warnings)


def merge_dramatic_tei_acts(request: DramaticTeiMergeRequest) -> DramaticTeiMergeResult:
    if not request.act_xml_paths:
        raise DramaticTeiMergeError("At least one dramatic TEI file is required for merge.")

    parsed_documents = tuple(_parse_act_document(path) for path in request.act_xml_paths)
    _, _, compatibility_warnings = _validate_compatibility(parsed_documents)

    merged_root = deepcopy(parsed_documents[0].tree.getroot())
    merged_bodies = merged_root.xpath("./*[local-name()='text']/*[local-name()='body']")
    if not merged_bodies:
        raise DramaticTeiMergeError("First merge input has no text/body in merged copy.")
    merged_body = merged_bodies[0]

    if request.title_override and request.title_override.strip():
        _apply_title_override(merged_root, request.title_override.strip())

    existing_ids = _collect_xml_ids(merged_root)
    warnings: list[str] = list(compatibility_warnings)

    merged_act_count = len(parsed_documents[0].act_divisions)

    for index, document in enumerate(parsed_documents[1:], start=2):
        prefix = _build_id_prefix(request.xml_id_prefix_template, index)
        merged_act_count += len(document.act_divisions)

        for act_node in document.act_divisions:
            cloned_act = deepcopy(act_node)
            id_map, rename_warnings = _remap_ids_in_subtree(
                cloned_act,
                existing_ids=existing_ids,
                prefix=prefix,
                collision_policy=request.collision_policy,
            )
            warnings.extend(rename_warnings)
            _rewrite_references_in_subtree(cloned_act, id_map)
            merged_body.append(cloned_act)

    merged_tree = etree.ElementTree(merged_root)
    merged_xml = etree.tostring(
        merged_tree,
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=True,
    ).decode("utf-8")

    written_output: Path | None = None
    if request.output_path is not None:
        written_output = request.output_path.resolve()
        written_output.parent.mkdir(parents=True, exist_ok=True)
        written_output.write_text(merged_xml, encoding="utf-8")

    return DramaticTeiMergeResult(
        merged_xml=merged_xml,
        merged_act_count=merged_act_count,
        warnings=tuple(warnings),
        output_path=written_output,
    )
