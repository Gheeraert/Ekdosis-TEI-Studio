from __future__ import annotations

import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any
from uuid import uuid4

from ets.site_builder import BuildResult, build_static_site, load_site_config

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


def _copy_notice_source(source: Path, destination_dir: Path, used_names: set[str]) -> None:
    stem = _normalize_identifier(source.stem) or "notice"
    candidate = f"{stem}.xml"
    counter = 2
    while candidate in used_names:
        candidate = f"{stem}-{counter}.xml"
        counter += 1
    used_names.add(candidate)
    shutil.copy2(source, destination_dir / candidate)


def _normalize_publication_request(
    request: SitePublicationRequest,
    staging_root: Path,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    site_title = request.identity.site_title.strip()

    warnings: list[str] = []
    dramatic_dir = (staging_root / "dramatic").resolve()
    notices_dir = (staging_root / "notices").resolve()
    dramatic_dir.mkdir(parents=True, exist_ok=True)

    play_slugs: list[str] = []
    seen_play_slugs: set[str] = set()
    mapping_pairs: list[tuple[str, str]] = list(request.play_notice_map)

    for play in request.plays:
        play_slug = _normalize_identifier(play.play_slug)
        if not play_slug:
            raise ValueError("Invalid publication request: each play must define a non-empty slug.")
        if play_slug in seen_play_slugs:
            raise ValueError(f"Invalid publication request: duplicate play slug '{play_slug}'.")
        seen_play_slugs.add(play_slug)
        play_slugs.append(play_slug)

        if not play.documents:
            raise ValueError(f"Invalid publication request: play '{play_slug}' has no dramatic XML files.")

        primary_document = _require_existing_file(play.documents[0].source_path, label=f"dramatic file for play '{play_slug}'")
        shutil.copy2(primary_document, dramatic_dir / f"{play_slug}.xml")
        if len(play.documents) > 1:
            warnings.append(
                f"Play '{play_slug}' provided {len(play.documents)} dramatic XML files; only the first file is used in current builder scope."
            )
            for extra in play.documents[1:]:
                _require_existing_file(extra.source_path, label=f"dramatic file for play '{play_slug}'")

        if play.related_notice_slug:
            mapping_pairs.append((play_slug, play.related_notice_slug))

    notice_dir_value: str | None = None
    if request.notices:
        notices_dir.mkdir(parents=True, exist_ok=True)
        notice_dir_value = str(notices_dir)
        used_notice_names: set[str] = set()
        for notice in request.notices:
            source = _require_existing_file(notice.source_path, label="notice file")
            _copy_notice_source(source, notices_dir, used_notice_names)

    normalized_order = tuple(_normalize_identifier(item) for item in (request.play_order or tuple(play_slugs)))
    normalized_order = tuple(item for item in normalized_order if item)

    mapping_dict: dict[str, str] = {}
    for raw_play, raw_notice in mapping_pairs:
        play_slug = _normalize_identifier(raw_play)
        notice_slug = _normalize_identifier(raw_notice)
        if not play_slug or not notice_slug:
            raise ValueError("Invalid publication request: play_notice_map entries must use non-empty identifiers.")
        mapping_dict[play_slug] = notice_slug

    payload: dict[str, Any] = {
        "site_title": site_title,
        "site_subtitle": request.identity.site_subtitle,
        "project_name": request.identity.project_name,
        "editor": request.identity.editor,
        "credits": request.identity.credits,
        "homepage_intro": request.identity.homepage_intro,
        "dramatic_xml_dir": str(dramatic_dir),
        "notice_xml_dir": notice_dir_value,
        "output_dir": str(request.output_dir),
        "show_xml_download": request.show_xml_download,
        "publish_notices": request.publish_notices,
        "include_metadata": request.include_metadata,
        "resolve_notice_xincludes": request.resolve_notice_xincludes,
        "play_notice_map": mapping_dict,
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
