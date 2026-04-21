from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from .models import AssetConfig, HomePageSection, SiteConfig


def _resolve_path(value: str | Path, base_dir: Path | None = None) -> Path:
    path = Path(str(value).strip())
    if not path.is_absolute() and base_dir is not None:
        path = base_dir / path
    return path.resolve()


def _normalize_text(value: Any, *, field_name: str, required: bool = False) -> str:
    if value is None:
        text = ""
    else:
        text = str(value).strip()
    if required and not text:
        raise ValueError(f"Invalid site configuration: '{field_name}' is required.")
    return text


def _normalize_identifier(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip())
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    ascii_only = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    return ascii_only


def _coerce_path_list(
    values: list[str] | tuple[str, ...] | None,
    *,
    base_dir: Path | None = None,
) -> tuple[Path, ...]:
    if not values:
        return ()
    normalized: list[Path] = []
    for item in values:
        if not str(item).strip():
            continue
        normalized.append(_resolve_path(item, base_dir=base_dir))
    return tuple(normalized)


def _coerce_play_notice_map(raw_mapping: Any) -> tuple[tuple[str, str], ...]:
    if raw_mapping is None:
        return ()
    if not isinstance(raw_mapping, dict):
        raise ValueError("Invalid site configuration: 'play_notice_map' must be an object.")

    pairs: list[tuple[str, str]] = []
    for raw_play, raw_notice in raw_mapping.items():
        play = _normalize_identifier(str(raw_play))
        notice = _normalize_identifier(str(raw_notice))
        if not play or not notice:
            raise ValueError(
                "Invalid site configuration: play_notice_map keys and values must be non-empty identifiers."
            )
        pairs.append((play, notice))
    return tuple(sorted(pairs, key=lambda item: item[0]))


def _coerce_play_preface_map(raw_mapping: Any) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if raw_mapping is None:
        return ()
    if not isinstance(raw_mapping, dict):
        raise ValueError("Invalid site configuration: 'play_preface_map' must be an object.")

    pairs: list[tuple[str, tuple[str, ...]]] = []
    for raw_play, raw_prefaces in raw_mapping.items():
        play = _normalize_identifier(str(raw_play))
        if not play:
            raise ValueError("Invalid site configuration: play_preface_map keys must be non-empty identifiers.")

        if isinstance(raw_prefaces, str):
            raw_values: list[Any] = [raw_prefaces]
        elif isinstance(raw_prefaces, (list, tuple)):
            raw_values = list(raw_prefaces)
        else:
            raise ValueError(
                "Invalid site configuration: play_preface_map values must be a string or a list of strings."
            )

        normalized_values: list[str] = []
        seen: set[str] = set()
        for raw_value in raw_values:
            slug = _normalize_identifier(str(raw_value))
            if not slug or slug in seen:
                continue
            seen.add(slug)
            normalized_values.append(slug)
        if not normalized_values:
            raise ValueError(
                "Invalid site configuration: play_preface_map values must contain at least one non-empty identifier."
            )
        pairs.append((play, tuple(normalized_values)))

    return tuple(sorted(pairs, key=lambda item: item[0]))


def _coerce_play_dramatis_map(raw_mapping: Any) -> tuple[tuple[str, str], ...]:
    if raw_mapping is None:
        return ()
    if not isinstance(raw_mapping, dict):
        raise ValueError("Invalid site configuration: 'play_dramatis_map' must be an object.")

    pairs: list[tuple[str, str]] = []
    for raw_play, raw_dramatis in raw_mapping.items():
        play = _normalize_identifier(str(raw_play))
        dramatis = _normalize_identifier(str(raw_dramatis))
        if not play or not dramatis:
            raise ValueError(
                "Invalid site configuration: play_dramatis_map keys and values must be non-empty identifiers."
            )
        pairs.append((play, dramatis))
    return tuple(sorted(pairs, key=lambda item: item[0]))


def _coerce_play_order(raw_order: Any) -> tuple[str, ...]:
    if raw_order is None:
        return ()
    if not isinstance(raw_order, (list, tuple)):
        raise ValueError("Invalid site configuration: 'play_order' must be a list.")

    ordered: list[str] = []
    seen: set[str] = set()
    for value in raw_order:
        slug = _normalize_identifier(str(value))
        if not slug or slug in seen:
            continue
        seen.add(slug)
        ordered.append(slug)
    return tuple(ordered)


def _coerce_homepage_sections(raw_sections: Any) -> tuple[HomePageSection, ...]:
    if raw_sections is None:
        return ()
    if not isinstance(raw_sections, (list, tuple)):
        raise ValueError("Invalid site configuration: 'homepage_sections' must be a list.")

    sections: list[HomePageSection] = []
    for index, item in enumerate(raw_sections):
        if not isinstance(item, dict):
            raise ValueError(
                f"Invalid site configuration: homepage_sections[{index}] must be an object."
            )
        title = _normalize_text(item.get("title", ""), field_name=f"homepage_sections[{index}].title")
        if not title:
            raise ValueError(
                f"Invalid site configuration: homepage_sections[{index}].title is required."
            )
        raw_paragraphs = item.get("paragraphs", [])
        if not isinstance(raw_paragraphs, (list, tuple)):
            raise ValueError(
                f"Invalid site configuration: homepage_sections[{index}].paragraphs must be a list."
            )
        paragraphs: list[str] = []
        for paragraph_index, paragraph in enumerate(raw_paragraphs):
            text = _normalize_text(
                paragraph,
                field_name=f"homepage_sections[{index}].paragraphs[{paragraph_index}]",
            )
            if text:
                paragraphs.append(text)
        sections.append(HomePageSection(title=title, paragraphs=tuple(paragraphs)))
    return tuple(sections)


def site_config_from_dict(payload: dict[str, Any], *, base_dir: Path | None = None) -> SiteConfig:
    assets_raw = payload.get("assets", {})
    if not isinstance(assets_raw, dict):
        assets_raw = {}

    site_title = _normalize_text(payload.get("site_title"), field_name="site_title", required=True)
    dramatic_value = payload.get("dramatic_xml_dir", ".")
    dramatic_text = _normalize_text(dramatic_value, field_name="dramatic_xml_dir", required=True)
    output_value = payload.get("output_dir", "out/site")
    output_text = _normalize_text(output_value, field_name="output_dir", required=True)

    config = SiteConfig(
        site_title=site_title,
        site_subtitle=_normalize_text(payload.get("site_subtitle", ""), field_name="site_subtitle"),
        dramatic_xml_dir=_resolve_path(dramatic_text, base_dir=base_dir),
        notice_xml_dir=(
            _resolve_path(payload["notice_xml_dir"], base_dir=base_dir) if payload.get("notice_xml_dir") else None
        ),
        dramatis_xml_dir=(
            _resolve_path(payload["dramatis_xml_dir"], base_dir=base_dir) if payload.get("dramatis_xml_dir") else None
        ),
        output_dir=_resolve_path(output_text, base_dir=base_dir),
        assets=AssetConfig(
            logo_files=_coerce_path_list(
                assets_raw.get("logos") or assets_raw.get("logo_files"),
                base_dir=base_dir,
            ),
            asset_directories=_coerce_path_list(
                assets_raw.get("directories") or assets_raw.get("asset_directories"),
                base_dir=base_dir,
            ),
        ),
        show_xml_download=bool(payload.get("show_xml_download", False)),
        publish_notices=bool(payload.get("publish_notices", True)),
        publish_prefaces=bool(payload.get("publish_prefaces", True)),
        include_metadata=bool(payload.get("include_metadata", True)),
        resolve_notice_xincludes=bool(payload.get("resolve_notice_xincludes", True)),
        project_name=_normalize_text(payload.get("project_name", ""), field_name="project_name"),
        editor=_normalize_text(payload.get("editor", ""), field_name="editor"),
        credits=_normalize_text(payload.get("credits", ""), field_name="credits"),
        homepage_intro=_normalize_text(payload.get("homepage_intro", ""), field_name="homepage_intro"),
        homepage_sections=_coerce_homepage_sections(payload.get("homepage_sections")),
        general_notice_slug=_normalize_identifier(
            _normalize_text(payload.get("general_notice_slug", ""), field_name="general_notice_slug")
        ),
        play_notice_map=_coerce_play_notice_map(payload.get("play_notice_map")),
        play_preface_map=_coerce_play_preface_map(payload.get("play_preface_map")),
        play_dramatis_map=_coerce_play_dramatis_map(payload.get("play_dramatis_map")),
        play_order=_coerce_play_order(payload.get("play_order")),
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
