from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .site_builder_models import (
    DramaticDocumentInput,
    DramaticPlayInput,
    NoticeInput,
    SiteAssetsInput,
    SiteIdentityInput,
    SitePublicationRequest,
)


PUBLICATION_DIALOG_CONFIG_SCHEMA = "ets.site_publication_dialog_config"
PUBLICATION_DIALOG_CONFIG_VERSION = 2


@dataclass(frozen=True)
class SitePublicationDialogPlayConfig:
    play_slug: str
    dramatic_xml_path: Path
    notice_xml_path: Path | None = None


@dataclass(frozen=True)
class SitePublicationDialogConfig:
    author_name: str = ""
    corpus_title: str = ""
    scientific_editor: str = ""
    home_page_tei: Path | None = None
    general_intro_tei: Path | None = None
    output_dir: Path | None = None
    plays: tuple[SitePublicationDialogPlayConfig, ...] = ()
    play_order: tuple[str, ...] = ()
    logo_paths: tuple[Path, ...] = ()
    asset_directories: tuple[Path, ...] = ()
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


def _normalize_play_order(value: Any) -> tuple[str, ...]:
    entries = _expect_list(value, field_name="play_order")
    ordered: list[str] = []
    for index, item in enumerate(entries):
        slug = _expect_text(item, field_name=f"play_order[{index}]")
        if slug:
            ordered.append(slug)
    return tuple(ordered)


def _normalize_identifier(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip())
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")


def normalize_publication_identifier(value: str) -> str:
    return _normalize_identifier(value)


def derive_corpus_slug(author_name: str, corpus_title: str) -> str:
    author = _normalize_identifier(author_name)
    words = [item for item in re.split(r"\s+", corpus_title.strip()) if item]
    first_two = " ".join(words[:2])
    title_part = _normalize_identifier(first_two)
    parts = [item for item in (author, title_part) if item]
    return "-".join(parts)


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

        dramatic_xml_path = _resolve_optional_path(
            entry.get("dramatic_xml_path"),
            field_name=f"plays[{index}].dramatic_xml_path",
            base_dir=base_dir,
        )
        if dramatic_xml_path is None:
            document_path = _resolve_optional_path(
                entry.get("document_path"),
                field_name=f"plays[{index}].document_path",
                base_dir=base_dir,
            )
            if document_path is None:
                document_paths = _resolve_path_list(
                    entry.get("document_paths", []),
                    field_name=f"plays[{index}].document_paths",
                    base_dir=base_dir,
                )
                if len(document_paths) != 1:
                    raise ValueError(
                        "Invalid publication dialog config: a play must reference exactly one dramatic XML file. "
                        "Merge fragments upstream before publication."
                    )
                dramatic_xml_path = document_paths[0]
            else:
                dramatic_xml_path = document_path

        notice_xml_path = _resolve_optional_path(
            entry.get("notice_xml_path"),
            field_name=f"plays[{index}].notice_xml_path",
            base_dir=base_dir,
        )

        plays.append(
            SitePublicationDialogPlayConfig(
                play_slug=play_slug,
                dramatic_xml_path=dramatic_xml_path,
                notice_xml_path=notice_xml_path,
            )
        )
    return tuple(plays)


def site_publication_dialog_config_to_dict(config: SitePublicationDialogConfig) -> dict[str, Any]:
    return {
        "schema": PUBLICATION_DIALOG_CONFIG_SCHEMA,
        "version": PUBLICATION_DIALOG_CONFIG_VERSION,
        "metadata": {
            "author_name": config.author_name,
            "corpus_title": config.corpus_title,
            "scientific_editor": config.scientific_editor,
        },
        "xml_sources": {
            "home_page_tei_path": str(config.home_page_tei.resolve()) if config.home_page_tei is not None else None,
            "general_intro_tei_path": (
                str(config.general_intro_tei.resolve()) if config.general_intro_tei is not None else None
            ),
        },
        "plays": [
            {
                "play_slug": play.play_slug,
                "dramatic_xml_path": str(play.dramatic_xml_path.resolve()),
                "notice_xml_path": str(play.notice_xml_path.resolve()) if play.notice_xml_path is not None else None,
            }
            for play in config.plays
        ],
        "play_order": list(config.play_order),
        "output": {
            "output_dir": str(config.output_dir.resolve()) if config.output_dir is not None else None,
        },
        "assets": {
            "logo_paths": [str(path.resolve()) for path in config.logo_paths],
            "asset_directories": [str(path.resolve()) for path in config.asset_directories],
        },
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
    if version not in {1, PUBLICATION_DIALOG_CONFIG_VERSION}:
        raise ValueError(
            "Invalid publication dialog config: unsupported version. "
            f"Expected {PUBLICATION_DIALOG_CONFIG_VERSION}."
        )

    if version == 1:
        identity = _expect_object(payload.get("identity", {}), field_name="identity")
        notices = _expect_object(payload.get("notices", {}), field_name="notices")
        metadata = {
            "author_name": identity.get("site_subtitle", ""),
            "corpus_title": identity.get("site_title", ""),
            "scientific_editor": identity.get("editor", ""),
        }
        xml_sources = {
            "home_page_tei_path": notices.get("master_notice_path"),
            "general_intro_tei_path": None,
        }
    else:
        metadata = _expect_object(payload.get("metadata", {}), field_name="metadata")
        xml_sources = _expect_object(payload.get("xml_sources", {}), field_name="xml_sources")

    plays = _normalize_plays(payload.get("plays", []), base_dir=base)
    play_order = _normalize_play_order(payload.get("play_order", []))

    home_page_tei = _resolve_optional_path(
        xml_sources.get("home_page_tei_path"),
        field_name="xml_sources.home_page_tei_path",
        base_dir=base,
    )
    general_intro_tei = _resolve_optional_path(
        xml_sources.get("general_intro_tei_path"),
        field_name="xml_sources.general_intro_tei_path",
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
        author_name=_expect_text(metadata.get("author_name", ""), field_name="metadata.author_name"),
        corpus_title=_expect_text(metadata.get("corpus_title", ""), field_name="metadata.corpus_title"),
        scientific_editor=_expect_text(
            metadata.get("scientific_editor", ""),
            field_name="metadata.scientific_editor",
        ),
        home_page_tei=home_page_tei,
        general_intro_tei=general_intro_tei,
        output_dir=output_dir,
        plays=plays,
        play_order=play_order,
        logo_paths=_resolve_path_list(assets.get("logo_paths", []), field_name="assets.logo_paths", base_dir=base),
        asset_directories=asset_directories,
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


def site_publication_request_from_dialog_config(config: SitePublicationDialogConfig) -> SitePublicationRequest:
    corpus_title = config.corpus_title.strip()
    if not corpus_title:
        raise ValueError("Le titre de l'œuvre/corpus est requis.")
    if config.output_dir is None:
        raise ValueError("Le dossier de sortie est requis.")
    if not config.plays:
        raise ValueError("Ajoutez au moins une pièce XML complète.")

    seen_play_slugs: set[str] = set()
    plays: list[DramaticPlayInput] = []
    for play in config.plays:
        play_slug = play.play_slug.strip()
        if not play_slug:
            raise ValueError("Chaque pièce doit avoir un slug non vide.")
        if play_slug in seen_play_slugs:
            raise ValueError(f"Slug de pièce dupliqué: '{play_slug}'.")
        seen_play_slugs.add(play_slug)

        plays.append(
            DramaticPlayInput(
                play_slug=play_slug,
                document=DramaticDocumentInput(source_path=play.dramatic_xml_path),
                related_notice_path=play.notice_xml_path,
            )
        )

    play_order = tuple(item for item in config.play_order if item in seen_play_slugs)
    if not play_order:
        play_order = tuple(play.play_slug for play in config.plays)
    else:
        missing = [play.play_slug for play in config.plays if play.play_slug not in play_order]
        play_order = tuple((*play_order, *missing))

    play_by_slug = {play.play_slug: play for play in plays}
    ordered_plays: list[DramaticPlayInput] = [play_by_slug[slug] for slug in play_order if slug in play_by_slug]
    ordered_slugs = {play.play_slug for play in ordered_plays}
    for play in plays:
        if play.play_slug not in ordered_slugs:
            ordered_plays.append(play)
            ordered_slugs.add(play.play_slug)

    notices: list[NoticeInput] = []
    seen_notice_paths: set[Path] = set()

    def _push_notice(path: Path | None) -> None:
        if path is None:
            return
        resolved = path.resolve()
        if resolved in seen_notice_paths:
            return
        seen_notice_paths.add(resolved)
        notices.append(NoticeInput(source_path=resolved))

    _push_notice(config.home_page_tei)
    _push_notice(config.general_intro_tei)
    for play in config.plays:
        _push_notice(play.notice_xml_path)

    general_notice_slug = ""
    if config.general_intro_tei is not None:
        general_notice_slug = _normalize_identifier(config.general_intro_tei.stem)

    identity = SiteIdentityInput(
        site_title=corpus_title,
        site_subtitle=config.author_name.strip(),
        project_name=derive_corpus_slug(config.author_name, corpus_title),
        editor=config.scientific_editor.strip(),
    )

    assets = SiteAssetsInput(
        logo_files=tuple(path.resolve() for path in config.logo_paths),
        asset_directories=tuple(path.resolve() for path in config.asset_directories),
    )

    return SitePublicationRequest(
        identity=identity,
        output_dir=config.output_dir.resolve(),
        plays=tuple(ordered_plays),
        play_order=play_order,
        notices=tuple(notices),
        assets=assets,
        show_xml_download=config.show_xml_download,
        publish_notices=config.publish_notices,
        include_metadata=config.include_metadata,
        resolve_notice_xincludes=config.resolve_notice_xincludes,
        general_notice_slug=general_notice_slug,
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
