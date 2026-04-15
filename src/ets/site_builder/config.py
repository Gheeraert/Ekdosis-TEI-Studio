from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import AssetConfig, SiteConfig


def _resolve_path(value: str | Path, base_dir: Path | None = None) -> Path:
    path = Path(value)
    if not path.is_absolute() and base_dir is not None:
        path = base_dir / path
    return path.resolve()


def _coerce_path_list(
    values: list[str] | tuple[str, ...] | None,
    *,
    base_dir: Path | None = None,
) -> tuple[Path, ...]:
    if not values:
        return ()
    return tuple(_resolve_path(item, base_dir=base_dir) for item in values)


def site_config_from_dict(payload: dict[str, Any], *, base_dir: Path | None = None) -> SiteConfig:
    assets_raw = payload.get("assets", {})
    if not isinstance(assets_raw, dict):
        assets_raw = {}

    config = SiteConfig(
        site_title=str(payload.get("site_title", "ETS Site")),
        site_subtitle=str(payload.get("site_subtitle", "")),
        dramatic_xml_dir=_resolve_path(payload.get("dramatic_xml_dir", "."), base_dir=base_dir),
        notice_xml_dir=(
            _resolve_path(payload["notice_xml_dir"], base_dir=base_dir) if payload.get("notice_xml_dir") else None
        ),
        output_dir=_resolve_path(payload.get("output_dir", "out/site"), base_dir=base_dir),
        assets=AssetConfig(
            logo_files=_coerce_path_list(assets_raw.get("logos"), base_dir=base_dir),
            asset_directories=_coerce_path_list(assets_raw.get("directories"), base_dir=base_dir),
        ),
        show_xml_download=bool(payload.get("show_xml_download", False)),
        publish_notices=bool(payload.get("publish_notices", True)),
        include_metadata=bool(payload.get("include_metadata", True)),
        project_name=str(payload.get("project_name", "")),
        editor=str(payload.get("editor", "")),
        credits=str(payload.get("credits", "")),
    )
    return config


def load_site_config(source: SiteConfig | dict[str, Any] | str | Path) -> SiteConfig:
    if isinstance(source, SiteConfig):
        return source

    if isinstance(source, dict):
        return site_config_from_dict(source)

    path = Path(source).resolve()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Site configuration JSON must be an object.")
    return site_config_from_dict(payload, base_dir=path.parent)
