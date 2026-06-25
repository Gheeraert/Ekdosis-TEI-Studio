from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import quote

from .models import DTSNavNode, DTSTeiIndex

DTS_CONTEXT = "https://dtsapi.org/context/v1.0.json"
DTS_VERSION = "1.0"


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


def _resource_links(index: DTSTeiIndex, *, prefix: str) -> dict[str, object]:
    slug = index.resource.slug
    return {
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


def resource(index: DTSTeiIndex) -> dict[str, object]:
    data = {
        "@context": DTS_CONTEXT,
        "dtsVersion": DTS_VERSION,
        **_resource_links(index, prefix="../"),
    }
    if index.resource.author:
        data["dublinCore"] = {"creator": [index.resource.author]}
    return data


def root_collection(indexes: Iterable[DTSTeiIndex], *, title: str) -> dict[str, object]:
    ordered = sorted(indexes, key=lambda item: item.resource.slug)
    members = []
    for index in ordered:
        member = _resource_links(index, prefix="../")
        if index.resource.author:
            member["dublinCore"] = {"creator": [index.resource.author]}
        members.append(member)
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


def _citable_unit(node: DTSNavNode) -> dict[str, object]:
    return {
        "identifier": node.identifier,
        "@type": "CitableUnit",
        "level": node.level,
        "parent": node.parent,
        "citeType": node.cite_type,
        "dublinCore": {
            "title": [
                {
                    "lang": "fr",
                    "value": node.label,
                }
            ]
        },
    }


def navigation(index: DTSTeiIndex, *, ref: str | None = None) -> dict[str, object]:
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
        "@id": f"{quote(ref, safe='-._~')}.json" if ref else "index.json",
        "@type": "Navigation",
        "resource": _resource_links(index, prefix="../../"),
        "member": [_citable_unit(node) for node in selected_nodes],
    }
    if selected_ref is not None:
        data["ref"] = _citable_unit(selected_ref)
    return data
