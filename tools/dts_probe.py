from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lxml import etree


@dataclass
class ResourceReport:
    slug: str
    title: str
    resource_ok: bool = False
    navigation_ok: bool = False
    full_tei_ok: bool = False
    citable_units: int = 0
    fragments_ok: int = 0


@dataclass
class ProbeReport:
    site_name: str
    entrypoint_ok: bool = False
    collection_title: str = ""
    collection_ok: bool = False
    resources: list[ResourceReport] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def citable_units(self) -> int:
        return sum(resource.citable_units for resource in self.resources)

    @property
    def fragments_ok(self) -> int:
        return sum(resource.fragments_ok for resource in self.resources)


def _json_load(path: Path, report: ProbeReport, site_root: Path, label: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        report.errors.append(f"ERROR: missing {_display_path(path, site_root)}")
        return None
    except json.JSONDecodeError as exc:
        report.errors.append(f"ERROR: invalid JSON {label}: {exc}")
        return None
    if not isinstance(payload, dict):
        report.errors.append(f"ERROR: invalid JSON {label}: root value is not an object")
        return None
    return payload


def _display_path(path: Path, site_root: Path) -> str:
    try:
        return path.resolve().relative_to(site_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _missing(path: Path, report: ProbeReport, site_root: Path) -> bool:
    if path.exists():
        return False
    report.errors.append(f"ERROR: missing {_display_path(path, site_root)}")
    return True


def _resolve_link(base_file: Path, href: str, site_root: Path) -> Path | None:
    target = (base_file.parent / href).resolve()
    try:
        target.relative_to(site_root.resolve())
    except ValueError:
        return None
    return target


def _parse_xml(path: Path, report: ProbeReport, site_root: Path) -> bool:
    try:
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        etree.parse(str(path), parser)
    except Exception as exc:
        report.errors.append(f"ERROR: invalid XML fragment {_display_path(path, site_root)}: {exc}")
        return False
    return True


def _probe_citable_unit(
    unit: Any,
    *,
    navigation_path: Path,
    report: ProbeReport,
    resource_report: ResourceReport,
    site_root: Path,
) -> None:
    resource_report.citable_units += 1
    if not isinstance(unit, dict):
        report.errors.append(f"ERROR: invalid CitableUnit for {resource_report.slug}: not an object")
        return

    identifier = unit.get("identifier")
    for key in ("identifier", "citeType", "level", "document"):
        if key not in unit:
            label = identifier if isinstance(identifier, str) and identifier else "unknown"
            report.errors.append(f"ERROR: CitableUnit {resource_report.slug}/{label} missing {key}")

    document_href = unit.get("document")
    if not isinstance(document_href, str) or not document_href:
        return

    fragment_path = _resolve_link(navigation_path, document_href, site_root)
    if fragment_path is None:
        report.errors.append(
            f"ERROR: fragment link escapes site root for {resource_report.slug}: {document_href}"
        )
        return
    if _missing(fragment_path, report, site_root):
        return
    if _parse_xml(fragment_path, report, site_root):
        resource_report.fragments_ok += 1


def probe_site(site_root: Path) -> ProbeReport:
    root = site_root.resolve()
    report = ProbeReport(site_name=site_root.name or str(site_root))

    entrypoint_path = root / "api" / "dts" / "index.json"
    collection_path = root / "api" / "dts" / "collection" / "index.json"

    report.entrypoint_ok = not _missing(entrypoint_path, report, root)
    if report.entrypoint_ok:
        _json_load(entrypoint_path, report, root, "api/dts/index.json")

    report.collection_ok = not _missing(collection_path, report, root)
    collection = (
        _json_load(collection_path, report, root, "api/dts/collection/index.json")
        if report.collection_ok
        else None
    )
    if collection is None:
        return report

    title = collection.get("title")
    report.collection_title = title if isinstance(title, str) else ""

    members = collection.get("member")
    if not isinstance(members, list):
        report.errors.append("ERROR: collection member is not a list")
        return report

    for member in members:
        if not isinstance(member, dict):
            report.errors.append("ERROR: collection member is not an object")
            continue
        slug = member.get("@id")
        if not isinstance(slug, str) or not slug:
            report.errors.append("ERROR: collection member missing @id slug")
            continue
        title = member.get("title")
        resource_report = ResourceReport(slug=slug, title=title if isinstance(title, str) else "")
        report.resources.append(resource_report)

        resource_path = root / "api" / "dts" / "collection" / f"{slug}.json"
        navigation_path = root / "api" / "dts" / "navigation" / slug / "index.json"
        full_tei_path = root / "api" / "dts" / "document" / slug / "full.xml"

        resource_report.resource_ok = not _missing(resource_path, report, root)
        if resource_report.resource_ok:
            _json_load(resource_path, report, root, f"api/dts/collection/{slug}.json")

        resource_report.navigation_ok = not _missing(navigation_path, report, root)
        resource_report.full_tei_ok = not _missing(full_tei_path, report, root)

        navigation = (
            _json_load(navigation_path, report, root, f"api/dts/navigation/{slug}/index.json")
            if resource_report.navigation_ok
            else None
        )
        if navigation is None:
            continue

        units = navigation.get("member")
        if not isinstance(units, list):
            report.errors.append(f"ERROR: navigation member is not a list for {slug}")
            continue
        for unit in units:
            _probe_citable_unit(
                unit,
                navigation_path=navigation_path,
                report=report,
                resource_report=resource_report,
                site_root=root,
            )

    return report


def _text_report(report: ProbeReport) -> str:
    lines = [
        f"DTS probe: {report.site_name}",
        f"EntryPoint: {'OK' if report.entrypoint_ok else 'MISSING'}",
        f"Collection: {report.collection_title or ('OK' if report.collection_ok else 'MISSING')}",
        f"Resources: {len(report.resources)}",
        "",
    ]
    for resource in report.resources:
        title = resource.title or "(sans titre)"
        lines.extend(
            [
                f"- {resource.slug} — {title}",
                f"  Resource: {'OK' if resource.resource_ok else 'MISSING'}",
                f"  Navigation: {'OK' if resource.navigation_ok else 'MISSING'}",
                f"  Full TEI: {'OK' if resource.full_tei_ok else 'MISSING'}",
                f"  Citable units: {resource.citable_units}",
                f"  Fragments XML: {resource.fragments_ok} OK",
            ]
        )
    if report.errors:
        lines.append("")
        lines.extend(report.errors)
    lines.extend(["", f"Result: {'OK' if report.ok else 'ERROR'}"])
    return "\n".join(lines)


def _json_report(report: ProbeReport) -> str:
    payload = {
        "ok": report.ok,
        "resources": len(report.resources),
        "citable_units": report.citable_units,
        "fragments_ok": report.fragments_ok,
        "errors": report.errors,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vérifie un export DTS statique généré par ETS.")
    parser.add_argument("site", type=Path, help="Chemin vers le site statique généré.")
    parser.add_argument("--json", action="store_true", help="Produit un diagnostic JSON.")
    args = parser.parse_args(argv)

    report = probe_site(args.site)
    output = _json_report(report) if args.json else _text_report(report)
    print(output)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
