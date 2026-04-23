from __future__ import annotations

import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any
from uuid import uuid4

from ets.site_builder import BuildResult, build_static_site, load_site_config
from ets.site_builder.extractors import SiteBuilderExtractionError, extract_notice_entry, extract_play_entry

from .site_builder_models import (
    SiteBuildRequest,
    SiteBuildServiceResult,
    SitePublicationRequest,
)


class SiteBuilderService:
    """Thin application service wrapper for ETS Site Builder publication build."""

    def build(self, request: SiteBuildRequest) -> SiteBuildServiceResult:
        return self._build_from_source(request.source, normalization_warnings=())

    def build_from_publication_request(self, request: SitePublicationRequest) -> SiteBuildServiceResult:
        temp_dir_path: Path | None = None
        try:
            _validate_publication_request_shape(request)
            staging_parent = request.output_dir.resolve().parent
            staging_parent.mkdir(parents=True, exist_ok=True)
            temp_dir_path = (staging_parent / f"ets_site_builder_{uuid4().hex}").resolve()
            temp_dir_path.mkdir(parents=True, exist_ok=False)
            payload, normalization_warnings = _normalize_publication_request(request, temp_dir_path)
            return self._build_from_source(payload, normalization_warnings=normalization_warnings)
        except (ValueError, OSError) as exc:
            return SiteBuildServiceResult(
                ok=False,
                message="Site publication request normalization failed.",
                error_code="E_SITE_REQUEST",
                error_detail=str(exc),
            )
        finally:
            if temp_dir_path is not None:
                shutil.rmtree(temp_dir_path, ignore_errors=True)

    def _build_from_source(
        self,
        source: dict[str, Any] | str | Path,
        *,
        normalization_warnings: tuple[str, ...],
    ) -> SiteBuildServiceResult:
        try:
            config = load_site_config(source)
        except (ValueError, OSError) as exc:
            return SiteBuildServiceResult(
                ok=False,
                message="Site build configuration failed.",
                error_code="E_SITE_CONFIG",
                error_detail=str(exc),
            )

        try:
            build_result = build_static_site(config)
        except (ValueError, OSError) as exc:
            return SiteBuildServiceResult(
                ok=False,
                message="Site build execution failed.",
                error_code="E_SITE_BUILD",
                error_detail=str(exc),
            )

        return _success_result(build_result, normalization_warnings=normalization_warnings)


def _success_result(
    build_result: BuildResult,
    *,
    normalization_warnings: tuple[str, ...],
) -> SiteBuildServiceResult:
    output_dir = build_result.output_dir.resolve()
    relpaths = tuple(path.resolve().relative_to(output_dir).as_posix() for path in build_result.generated_pages)
    combined_warnings = tuple(normalization_warnings) + tuple(build_result.warnings)
    return SiteBuildServiceResult(
        ok=True,
        output_dir=output_dir,
        generated_pages=build_result.generated_pages,
        copied_assets=build_result.copied_assets,
        warnings=combined_warnings,
        play_count=build_result.play_count,
        notice_count=build_result.notice_count,
        message="Site build successful.",
        generated_page_relpaths=relpaths,
    )


def build_site_from_config_dict(payload: dict[str, object]) -> SiteBuildServiceResult:
    service = SiteBuilderService()
    return service.build(SiteBuildRequest(source=payload))


def build_site_from_config_file(config_path: str | Path) -> SiteBuildServiceResult:
    service = SiteBuilderService()
    return service.build(SiteBuildRequest(source=config_path))


def build_site_from_publication_request(request: SitePublicationRequest) -> SiteBuildServiceResult:
    service = SiteBuilderService()
    return service.build_from_publication_request(request)


def _normalize_identifier(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip())
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    ascii_only = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    return ascii_only


def _require_existing_file(path: Path, *, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.exists() or not resolved.is_file():
        raise ValueError(f"Invalid publication request: {label} '{path}' does not exist or is not a file.")
    return resolved


def _copy_notice_source(
    source: Path,
    destination_dir: Path,
    used_names: set[str],
    *,
    resolve_xincludes: bool,
) -> str:
    try:
        notice_entry = extract_notice_entry(source, resolve_xincludes=resolve_xincludes)
    except SiteBuilderExtractionError as exc:
        raise ValueError(f"Invalid publication request: notice file '{source}' could not be analyzed: {exc}") from exc

    stem = _normalize_identifier(notice_entry.slug) or _normalize_identifier(source.stem) or "notice"
    candidate = f"{stem}.xml"
    counter = 2
    while candidate in used_names:
        candidate = f"{stem}-{counter}.xml"
        counter += 1
    used_names.add(candidate)
    shutil.copy2(source, destination_dir / candidate)
    return stem


def _copy_aux_xml_source(
    source: Path,
    destination_dir: Path,
    used_names: set[str],
    *,
    fallback_slug: str,
) -> str:
    stem = _normalize_identifier(source.stem) or fallback_slug
    candidate = f"{stem}.xml"
    counter = 2
    while candidate in used_names:
        candidate = f"{stem}-{counter}.xml"
        counter += 1
    used_names.add(candidate)
    shutil.copy2(source, destination_dir / candidate)
    return stem


def _normalize_publication_request(
    request: SitePublicationRequest,
    staging_root: Path,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    site_title = request.identity.site_title.strip()

    warnings: list[str] = []
    dramatic_dir = (staging_root / "dramatic").resolve()
    notices_dir = (staging_root / "notices").resolve()
    dramatis_dir = (staging_root / "dramatis").resolve()
    dramatic_dir.mkdir(parents=True, exist_ok=True)

    play_slugs: list[str] = []
    seen_play_slugs: set[str] = set()
    notice_mapping_pairs: list[tuple[str, str]] = list(request.play_notice_map)
    preface_mapping_pairs: list[tuple[str, tuple[str, ...]]] = list(request.play_preface_map)
    dramatis_mapping_pairs: list[tuple[str, str]] = list(request.play_dramatis_map)
    play_notice_sources: list[tuple[str, Path]] = []
    play_preface_sources: list[tuple[str, Path]] = []
    play_dramatis_sources: list[tuple[str, Path]] = []

    for play in request.plays:
        dramatic_source = _require_existing_file(
            play.document.source_path,
            label="dramatic file",
        )
        try:
            extracted_play = extract_play_entry(dramatic_source)
        except SiteBuilderExtractionError as exc:
            raise ValueError(f"Invalid publication request: dramatic file '{dramatic_source}' could not be analyzed: {exc}") from exc

        play_slug = _normalize_identifier(extracted_play.title) or extracted_play.slug or _normalize_identifier(play.play_slug)
        if not play_slug:
            raise ValueError("Invalid publication request: each play must define a non-empty slug.")
        if play_slug in seen_play_slugs:
            raise ValueError(f"Invalid publication request: duplicate play slug '{play_slug}'.")
        seen_play_slugs.add(play_slug)
        play_slugs.append(play_slug)

        play_output = dramatic_dir / f"{play_slug}.xml"
        shutil.copy2(dramatic_source, play_output)

        if play.related_notice_slug:
            notice_mapping_pairs.append((play_slug, play.related_notice_slug))
        if play.related_preface_slug:
            preface_mapping_pairs.append((play_slug, (play.related_preface_slug,)))

        notice_path = play.notice_xml_path if play.notice_xml_path is not None else play.related_notice_path
        if notice_path is not None:
            notice_source = _require_existing_file(
                notice_path,
                label=f"notice file for play '{play_slug}'",
            )
            play_notice_sources.append((play_slug, notice_source))
        if play.preface_xml_path is not None:
            preface_source = _require_existing_file(
                play.preface_xml_path,
                label=f"preface file for play '{play_slug}'",
            )
            play_preface_sources.append((play_slug, preface_source))
        if play.dramatis_xml_path is not None:
            dramatis_source = _require_existing_file(
                play.dramatis_xml_path,
                label=f"dramatis file for play '{play_slug}'",
            )
            play_dramatis_sources.append((play_slug, dramatis_source))

    notice_dir_value: str | None = None
    if request.notices or play_notice_sources or play_preface_sources:
        notices_dir.mkdir(parents=True, exist_ok=True)
        notice_dir_value = str(notices_dir)
        used_notice_names: set[str] = set()
        notice_slug_by_source: dict[Path, str] = {}
        notice_like_sources: list[Path] = []

        def _push_notice_source(source: Path) -> None:
            if source not in notice_like_sources:
                notice_like_sources.append(source)

        for notice in request.notices:
            source = _require_existing_file(notice.source_path, label="notice file")
            _push_notice_source(source)
        for _play_slug, source in play_notice_sources:
            _push_notice_source(source)
        for _play_slug, source in play_preface_sources:
            _push_notice_source(source)

        for source in notice_like_sources:
            notice_slug_by_source[source] = _copy_notice_source(
                source,
                notices_dir,
                used_notice_names,
                resolve_xincludes=request.resolve_notice_xincludes,
            )

        for play_slug, source in play_notice_sources:
            notice_slug = notice_slug_by_source.get(source)
            if not notice_slug:
                raise ValueError(
                    f"Invalid publication request: unable to derive notice slug for play '{play_slug}'."
                )
            notice_mapping_pairs.append((play_slug, notice_slug))
        for play_slug, source in play_preface_sources:
            preface_slug = notice_slug_by_source.get(source)
            if not preface_slug:
                raise ValueError(
                    f"Invalid publication request: unable to derive preface slug for play '{play_slug}'."
                )
            preface_mapping_pairs.append((play_slug, (preface_slug,)))

    dramatis_dir_value: str | None = None
    if play_dramatis_sources:
        dramatis_dir.mkdir(parents=True, exist_ok=True)
        dramatis_dir_value = str(dramatis_dir)
        used_dramatis_names: set[str] = set()
        dramatis_slug_by_source: dict[Path, str] = {}
        unique_sources: list[Path] = []

        def _push_dramatis_source(source: Path) -> None:
            if source not in unique_sources:
                unique_sources.append(source)

        for _play_slug, source in play_dramatis_sources:
            _push_dramatis_source(source)

        for source in unique_sources:
            dramatis_slug_by_source[source] = _copy_aux_xml_source(
                source,
                dramatis_dir,
                used_dramatis_names,
                fallback_slug="dramatis",
            )

        for play_slug, source in play_dramatis_sources:
            dramatis_slug = dramatis_slug_by_source.get(source)
            if not dramatis_slug:
                raise ValueError(
                    f"Invalid publication request: unable to derive dramatis slug for play '{play_slug}'."
                )
            dramatis_mapping_pairs.append((play_slug, dramatis_slug))

    normalized_order = tuple(_normalize_identifier(item) for item in (request.play_order or tuple(play_slugs)))
    normalized_order = tuple(item for item in normalized_order if item)

    notice_mapping_dict: dict[str, str] = {}
    for raw_play, raw_notice in notice_mapping_pairs:
        play_slug = _normalize_identifier(raw_play)
        notice_slug = _normalize_identifier(raw_notice)
        if not play_slug or not notice_slug:
            raise ValueError("Invalid publication request: play_notice_map entries must use non-empty identifiers.")
        notice_mapping_dict[play_slug] = notice_slug

    preface_mapping_dict: dict[str, list[str]] = {}
    for raw_play, raw_prefaces in preface_mapping_pairs:
        play_slug = _normalize_identifier(raw_play)
        if not play_slug:
            raise ValueError("Invalid publication request: play_preface_map keys must use non-empty identifiers.")
        normalized_prefaces: list[str] = []
        seen_preface_slugs: set[str] = set()
        for raw_preface in raw_prefaces:
            preface_slug = _normalize_identifier(raw_preface)
            if not preface_slug or preface_slug in seen_preface_slugs:
                continue
            seen_preface_slugs.add(preface_slug)
            normalized_prefaces.append(preface_slug)
        if not normalized_prefaces:
            continue
        existing = preface_mapping_dict.setdefault(play_slug, [])
        for slug in normalized_prefaces:
            if slug not in existing:
                existing.append(slug)

    dramatis_mapping_dict: dict[str, str] = {}
    for raw_play, raw_dramatis in dramatis_mapping_pairs:
        play_slug = _normalize_identifier(raw_play)
        dramatis_slug = _normalize_identifier(raw_dramatis)
        if not play_slug or not dramatis_slug:
            raise ValueError("Invalid publication request: play_dramatis_map entries must use non-empty identifiers.")
        dramatis_mapping_dict[play_slug] = dramatis_slug

    payload: dict[str, Any] = {
        "site_title": site_title,
        "site_subtitle": request.identity.site_subtitle,
        "project_name": request.identity.project_name,
        "editor": request.identity.editor,
        "credits": request.identity.credits,
        "homepage_intro": request.identity.homepage_intro,
        "homepage_sections": [
            {
                "title": section.title,
                "paragraphs": [paragraph for paragraph in section.paragraphs],
            }
            for section in request.identity.homepage_sections
            if section.title.strip()
        ],
        "dramatic_xml_dir": str(dramatic_dir),
        "notice_xml_dir": notice_dir_value,
        "dramatis_xml_dir": dramatis_dir_value,
        "output_dir": str(request.output_dir),
        "show_xml_download": request.show_xml_download,
        "publish_notices": request.publish_notices,
        "publish_prefaces": request.publish_prefaces,
        "include_metadata": request.include_metadata,
        "resolve_notice_xincludes": request.resolve_notice_xincludes,
        "play_notice_map": notice_mapping_dict,
        "play_preface_map": preface_mapping_dict,
        "play_dramatis_map": dramatis_mapping_dict,
        "general_notice_slug": _normalize_identifier(request.general_notice_slug),
        "home_page_notice_slug": _normalize_identifier(request.home_page_notice_slug),
        "play_order": list(normalized_order),
        "assets": {
            "logos": [str(path) for path in request.assets.logo_files],
            "directories": [str(path) for path in request.assets.asset_directories],
        },
    }
    return payload, tuple(warnings)


def _validate_publication_request_shape(request: SitePublicationRequest) -> None:
    if not request.identity.site_title.strip():
        raise ValueError("Invalid publication request: site title is required.")
    if not request.plays:
        raise ValueError("Invalid publication request: at least one dramatic play input is required.")
