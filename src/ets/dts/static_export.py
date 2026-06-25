from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from .document_fragments import encoded_reference, export_document_fragments
from .jsonld import entry_point, navigation, resource, root_collection
from .models import DTSTeiIndex
from .tei_index import index_tei

_SAFE_SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _safe_target(output_root: Path, relative_path: Path) -> Path:
    root = output_root.resolve()
    target = (root / relative_path).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"output path escapes publication directory: {relative_path}") from exc
    return target


def _write_json(output_root: Path, relative_path: Path, payload: dict[str, object]) -> None:
    target = _safe_target(output_root, relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    target.write_text(f"{serialized}\n", encoding="utf-8")


def _export_resource(output_root: Path, index: DTSTeiIndex) -> tuple[str, ...]:
    slug = index.resource.slug
    if not _SAFE_SLUG.fullmatch(slug):
        raise ValueError("slug is not a safe static path segment")

    dts_root = Path("api") / "dts"
    _write_json(output_root, dts_root / "collection" / f"{slug}.json", resource(index))
    _write_json(output_root, dts_root / "navigation" / slug / "index.json", navigation(index))
    for node in _flatten(index):
        _write_json(
            output_root,
            dts_root / "navigation" / slug / f"{encoded_reference(node.identifier)}.json",
            navigation(index, ref=node.identifier),
        )

    document_target = _safe_target(output_root, dts_root / "document" / slug / "full.xml")
    document_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(index.resource.source_path, document_target)
    return export_document_fragments(output_root, index, safe_target=_safe_target)


def _flatten(index: DTSTeiIndex):
    pending = list(reversed(index.navigation))
    while pending:
        node = pending.pop()
        yield node
        pending.extend(reversed(node.children))


def export_dts_static(
    output_root: Path,
    plays: tuple[object, ...],
    *,
    collection_title: str,
) -> tuple[str, ...]:
    resolved_root = output_root.resolve()
    warnings: list[str] = []
    indexes: list[DTSTeiIndex] = []

    for play in sorted(plays, key=lambda item: str(getattr(item, "slug", ""))):
        slug = str(getattr(play, "slug", "")).strip() or "unknown"
        try:
            index = index_tei(
                Path(getattr(play, "source_path")),
                slug=slug,
                title=str(getattr(play, "title", "") or ""),
                author=getattr(play, "author", None),
            )
            warnings.extend(_export_resource(resolved_root, index))
            indexes.append(index)
        except Exception as exc:
            warnings.append(f"DTS export skipped for {slug}: {exc}")

    dts_root = Path("api") / "dts"
    _write_json(resolved_root, dts_root / "index.json", entry_point())
    _write_json(
        resolved_root,
        dts_root / "collection" / "index.json",
        root_collection(indexes, title=collection_title),
    )
    return tuple(warnings)
