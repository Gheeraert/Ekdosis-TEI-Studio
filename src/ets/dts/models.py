from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DTSNavNode:
    identifier: str
    cite_type: str
    level: int
    parent: str | None
    label: str
    children: tuple["DTSNavNode", ...] = ()


@dataclass(frozen=True)
class DTSResource:
    slug: str
    title: str
    author: str | None
    source_path: Path


@dataclass(frozen=True)
class DTSTeiIndex:
    resource: DTSResource
    navigation: tuple[DTSNavNode, ...] = ()
