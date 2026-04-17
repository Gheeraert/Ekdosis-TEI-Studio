from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PUBLICATION_DIALOG_CONFIG_SCHEMA = "ets.site_publication_dialog_config"
PUBLICATION_DIALOG_CONFIG_VERSION = 1


@dataclass(frozen=True)
class SitePublicationDialogPlayConfig:
    play_slug: str
    document_paths: tuple[Path, ...] = ()


@dataclass(frozen=True)
class SitePublicationDialogConfig:
    site_title: str = ""
    site_subtitle: str = ""
    project_name: str = ""
    editor: str = ""
    credits: str = ""
    homepage_intro: str = ""
    output_dir: Path | None = None
    plays: tuple[SitePublicationDialogPlayConfig, ...] = ()
    play_order: tuple[str, ...] = ()
    master_notice: Path | None = None
    additional_notices: tuple[Path, ...] = ()
    logo_paths: tuple[Path, ...] = ()
    asset_directories: tuple[Path, ...] = ()
    play_notice_map: tuple[tuple[str, str], ...] = ()
    show_xml_download: bool = False
    publish_notices: bool = True
    include_metadata: bool = True
    resolve_notice_xincludes: bool = True


def _expect_object(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Invalid publication dialog config: '{field_name}' must be an object.")
    return value


def _expect_list(value: Any, *, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"Invalid publication dialog config: '{field_name}' must be a list.")
    return value


def _expect_text(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Invalid publication dialog config: '{field_name}' must be a string.")
    return value.strip()


def _expect_bool(value: Any, *, field_name: str, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError(f"Invalid publication dialog config: '{field_name}' must be a boolean.")
    return value


def _resolve_optional_path(value: Any, *, field_name: str, base_dir: Path) -> Path | None:
    if value is None:
        return None
    text = _expect_text(value, field_name=field_name)
    if not text:
        return None
    path = Path(text)
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def _resolve_path_list(value: Any, *, field_name: str, base_dir: Path) -> tuple[Path, ...]:
    items = _expect_list(value, field_name=field_name)
    resolved: list[Path] = []
    for index, item in enumerate(items):
        path = _resolve_optional_path(item, field_name=f"{field_name}[{index}]", base_dir=base_dir)
        if path is None:
            raise ValueError(f"Invalid publication dialog config: '{field_name}[{index}]' cannot be empty.")
        resolved.append(path)
    return tuple(resolved)


def _normalize_mapping(value: Any) -> tuple[tuple[str, str], ...]:
    entries = _expect_list(value, field_name="play_notice_map")
    normalized: list[tuple[str, str]] = []
    for index, item in enumerate(entries):
        entry = _expect_object(item, field_name=f"play_notice_map[{index}]")
        play_slug = _expect_text(entry.get("play_slug"), field_name=f"play_notice_map[{index}].play_slug")
        notice_slug = _expect_text(entry.get("notice_slug"), field_name=f"play_notice_map[{index}].notice_slug")
        if not play_slug or not notice_slug:
            raise ValueError("Invalid publication dialog config: play_notice_map entries require non-empty slugs.")
        normalized.append((play_slug, notice_slug))
    return tuple(normalized)


def _normalize_play_order(value: Any) -> tuple[str, ...]:
    entries = _expect_list(value, field_name="play_order")
    ordered: list[str] = []
    for index, item in enumerate(entries):
        slug = _expect_text(item, field_name=f"play_order[{index}]")
        if slug:
            ordered.append(slug)
    return tuple(ordered)


def _normalize_plays(value: Any, *, base_dir: Path) -> tuple[SitePublicationDialogPlayConfig, ...]:
    entries = _expect_list(value, field_name="plays")
    plays: list[SitePublicationDialogPlayConfig] = []
    seen: set[str] = set()
    for index, item in enumerate(entries):
        entry = _expect_object(item, field_name=f"plays[{index}]")
        play_slug = _expect_text(entry.get("play_slug"), field_name=f"plays[{index}].play_slug")
        if not play_slug:
            raise ValueError("Invalid publication dialog config: play_slug cannot be empty.")
        if play_slug in seen:
            raise ValueError(f"Invalid publication dialog config: duplicate play_slug '{play_slug}'.")
        seen.add(play_slug)
        document_paths = _resolve_path_list(
            entry.get("document_paths", []),
            field_name=f"plays[{index}].document_paths",
            base_dir=base_dir,
        )
        plays.append(SitePublicationDialogPlayConfig(play_slug=play_slug, document_paths=document_paths))
    return tuple(plays)


def site_publication_dialog_config_to_dict(config: SitePublicationDialogConfig) -> dict[str, Any]:
    return {
        "schema": PUBLICATION_DIALOG_CONFIG_SCHEMA,
        "version": PUBLICATION_DIALOG_CONFIG_VERSION,
        "identity": {
            "site_title": config.site_title,
            "site_subtitle": config.site_subtitle,
            "project_name": config.project_name,
            "editor": config.editor,
            "credits": config.credits,
            "homepage_intro": config.homepage_intro,
        },
        "plays": [
            {
                "play_slug": play.play_slug,
                "document_paths": [str(path.resolve()) for path in play.document_paths],
            }
            for play in config.plays
        ],
        "play_order": list(config.play_order),
        "notices": {
            "master_notice_path": str(config.master_notice.resolve()) if config.master_notice is not None else None,
            "additional_notice_paths": [str(path.resolve()) for path in config.additional_notices],
        },
        "output": {
            "output_dir": str(config.output_dir.resolve()) if config.output_dir is not None else None,
        },
        "assets": {
            "logo_paths": [str(path.resolve()) for path in config.logo_paths],
            "asset_directories": [str(path.resolve()) for path in config.asset_directories],
        },
        "play_notice_map": [
            {"play_slug": play_slug, "notice_slug": notice_slug}
            for play_slug, notice_slug in config.play_notice_map
        ],
        "options": {
            "show_xml_download": config.show_xml_download,
            "publish_notices": config.publish_notices,
            "include_metadata": config.include_metadata,
            "resolve_notice_xincludes": config.resolve_notice_xincludes,
        },
    }


def site_publication_dialog_config_from_dict(
    payload: dict[str, Any],
    *,
    base_dir: Path | None = None,
) -> SitePublicationDialogConfig:
    base = base_dir.resolve() if base_dir is not None else Path.cwd().resolve()

    schema = payload.get("schema")
    if schema != PUBLICATION_DIALOG_CONFIG_SCHEMA:
        raise ValueError(
            "Invalid publication dialog config: unsupported schema. "
            f"Expected '{PUBLICATION_DIALOG_CONFIG_SCHEMA}'."
        )
    version = payload.get("version")
    if version != PUBLICATION_DIALOG_CONFIG_VERSION:
        raise ValueError(
            "Invalid publication dialog config: unsupported version. "
            f"Expected {PUBLICATION_DIALOG_CONFIG_VERSION}."
        )

    identity = _expect_object(payload.get("identity", {}), field_name="identity")
    plays = _normalize_plays(payload.get("plays", []), base_dir=base)
    play_order = _normalize_play_order(payload.get("play_order", []))

    notices = _expect_object(payload.get("notices", {}), field_name="notices")
    master_notice = _resolve_optional_path(
        notices.get("master_notice_path"),
        field_name="notices.master_notice_path",
        base_dir=base,
    )
    additional_notices = _resolve_path_list(
        notices.get("additional_notice_paths", []),
        field_name="notices.additional_notice_paths",
        base_dir=base,
    )

    assets = _expect_object(payload.get("assets", {}), field_name="assets")
    asset_directories = _resolve_path_list(
        assets.get("asset_directories", []),
        field_name="assets.asset_directories",
        base_dir=base,
    )
    if len(asset_directories) > 1:
        raise ValueError("Invalid publication dialog config: only one asset directory is supported by this dialog.")

    output = _expect_object(payload.get("output", {}), field_name="output")
    output_dir = _resolve_optional_path(output.get("output_dir"), field_name="output.output_dir", base_dir=base)

    options = _expect_object(payload.get("options", {}), field_name="options")

    return SitePublicationDialogConfig(
        site_title=_expect_text(identity.get("site_title", ""), field_name="identity.site_title"),
        site_subtitle=_expect_text(identity.get("site_subtitle", ""), field_name="identity.site_subtitle"),
        project_name=_expect_text(identity.get("project_name", ""), field_name="identity.project_name"),
        editor=_expect_text(identity.get("editor", ""), field_name="identity.editor"),
        credits=_expect_text(identity.get("credits", ""), field_name="identity.credits"),
        homepage_intro=_expect_text(identity.get("homepage_intro", ""), field_name="identity.homepage_intro"),
        output_dir=output_dir,
        plays=plays,
        play_order=play_order,
        master_notice=master_notice,
        additional_notices=additional_notices,
        logo_paths=_resolve_path_list(assets.get("logo_paths", []), field_name="assets.logo_paths", base_dir=base),
        asset_directories=asset_directories,
        play_notice_map=_normalize_mapping(payload.get("play_notice_map", [])),
        show_xml_download=_expect_bool(
            options.get("show_xml_download"),
            field_name="options.show_xml_download",
            default=False,
        ),
        publish_notices=_expect_bool(
            options.get("publish_notices"),
            field_name="options.publish_notices",
            default=True,
        ),
        include_metadata=_expect_bool(
            options.get("include_metadata"),
            field_name="options.include_metadata",
            default=True,
        ),
        resolve_notice_xincludes=_expect_bool(
            options.get("resolve_notice_xincludes"),
            field_name="options.resolve_notice_xincludes",
            default=True,
        ),
    )


def save_site_publication_dialog_config(config: SitePublicationDialogConfig, output_path: str | Path) -> Path:
    path = Path(output_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = site_publication_dialog_config_to_dict(config)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_site_publication_dialog_config(config_path: str | Path) -> SitePublicationDialogConfig:
    path = Path(config_path).resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid publication dialog configuration JSON: {exc.msg}.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Invalid publication dialog config: root JSON value must be an object.")
    return site_publication_dialog_config_from_dict(payload, base_dir=path.parent)
