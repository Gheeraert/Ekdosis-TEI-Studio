from __future__ import annotations

from collections.abc import Iterable

from .document_fragments import encoded_reference
from .models import DTSNavNode, DTSTeiIndex

DTS_CONTEXT = "https://dtsapi.org/context/v1.0.json"
DTS_VERSION = "1.0"

# Mirrors ets.seo.schema_reference.ODD_RELPATH (the published site-root path
# of the TEI ODD schema). Duplicated as a literal rather than imported to
# keep the DTS static export independent from the SEO layer. The ODD
# describes the TEI *documents*, not the DTS service itself, so it is
# attached to each Resource's dublinCore.conformsTo rather than to the
# top-level EntryPoint.
_ODD_RELPATH_SEGMENT = "tei-profile/ets-racine.odd"


def _odd_conforms_to(prefix: str) -> str:
    # `prefix` is _resource_links' own "distance to api/dts/" (e.g. "../"
    # from api/dts/collection/<slug>.json); api/dts/ itself is two levels
    # below the site root, so two more "../" reach it from there.
    return f"{prefix}../../{_ODD_RELPATH_SEGMENT}"


def _citation_trees() -> list[dict[str, object]]:
    return [
        {
            "@type": "CitationTree",
            "citeStructure": [
                {
                    "@type": "CiteStructure",
                    "citeType": "act",
                    "citeStructure": [
                        {
                            "@type": "CiteStructure",
                            "citeType": "scene",
                            "citeStructure": [
                                {
                                    "@type": "CiteStructure",
                                    "citeType": "line",
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    ]


def entry_point() -> dict[str, object]:
    return {
        "@context": DTS_CONTEXT,
        "dtsVersion": DTS_VERSION,
        "@id": "index.json",
        "@type": "EntryPoint",
        "collection": "collection/index.json",
        "navigation": "navigation/{resource}/index.json",
        "document": "document/{resource}/full.xml",
    }


def _resource_links(
    index: DTSTeiIndex, *, prefix: str, include_odd_reference: bool = False
) -> dict[str, object]:
    slug = index.resource.slug
    data: dict[str, object] = {
        "@id": slug,
        "@type": "Resource",
        "title": index.resource.title,
        "totalParents": 1,
        "totalChildren": 0,
        "collection": f"{prefix}collection/{slug}.json",
        "navigation": f"{prefix}navigation/{slug}/index.json",
        "document": f"{prefix}document/{slug}/full.xml",
        "download": f"{prefix}document/{slug}/full.xml",
        "mediaTypes": ["application/tei+xml", "application/xml"],
        "citationTrees": _citation_trees(),
    }
    dublin_core: dict[str, object] = {}
    if index.resource.author:
        dublin_core["creator"] = [index.resource.author]
    if include_odd_reference:
        dublin_core["conformsTo"] = [_odd_conforms_to(prefix)]
    if dublin_core:
        data["dublinCore"] = dublin_core
    return data


def resource(index: DTSTeiIndex, *, include_odd_reference: bool = False) -> dict[str, object]:
    return {
        "@context": DTS_CONTEXT,
        "dtsVersion": DTS_VERSION,
        **_resource_links(index, prefix="../", include_odd_reference=include_odd_reference),
    }


def root_collection(
    indexes: Iterable[DTSTeiIndex], *, title: str, include_odd_reference: bool = False
) -> dict[str, object]:
    ordered = sorted(indexes, key=lambda item: item.resource.slug)
    members = [
        _resource_links(index, prefix="../", include_odd_reference=include_odd_reference)
        for index in ordered
    ]
    return {
        "@context": DTS_CONTEXT,
        "dtsVersion": DTS_VERSION,
        "@id": "index.json",
        "@type": "Collection",
        "title": title,
        "totalParents": 0,
        "totalChildren": len(members),
        "collection": "index.json",
        "member": members,
    }


def _flatten(nodes: Iterable[DTSNavNode]) -> list[DTSNavNode]:
    flattened: list[DTSNavNode] = []
    for node in nodes:
        flattened.append(node)
        flattened.extend(_flatten(node.children))
    return flattened


def _citable_unit(node: DTSNavNode, *, slug: str) -> dict[str, object]:
    return {
        "identifier": node.identifier,
        "@type": "CitableUnit",
        "level": node.level,
        "parent": node.parent,
        "citeType": node.cite_type,
        "document": f"../../document/{slug}/{encoded_reference(node.identifier)}.xml",
        "dublinCore": {
            "title": [
                {
                    "lang": "fr",
                    "value": node.label,
                }
            ]
        },
    }


def navigation(
    index: DTSTeiIndex, *, ref: str | None = None, include_odd_reference: bool = False
) -> dict[str, object]:
    all_nodes = _flatten(index.navigation)
    selected_nodes = all_nodes
    selected_ref: DTSNavNode | None = None
    if ref is not None:
        selected_ref = next((node for node in all_nodes if node.identifier == ref), None)
        if selected_ref is None:
            raise ValueError(f"unknown navigation reference '{ref}'")
        selected_nodes = [selected_ref, *_flatten(selected_ref.children)]

    slug = index.resource.slug
    data: dict[str, object] = {
        "@context": DTS_CONTEXT,
        "dtsVersion": DTS_VERSION,
        "@id": f"{encoded_reference(ref)}.json" if ref else "index.json",
        "@type": "Navigation",
        "resource": _resource_links(
            index, prefix="../../", include_odd_reference=include_odd_reference
        ),
        "member": [_citable_unit(node, slug=slug) for node in selected_nodes],
    }
    if selected_ref is not None:
        data["ref"] = _citable_unit(selected_ref, slug=slug)
    return data
