from __future__ import annotations

from pathlib import Path

from ets.site_builder import BuildResult, build_static_site, load_site_config

from .site_builder_models import SiteBuildRequest, SiteBuildServiceResult


class SiteBuilderService:
    """Thin application service wrapper for ETS Site Builder publication build."""

    def build(self, request: SiteBuildRequest) -> SiteBuildServiceResult:
        try:
            config = load_site_config(request.source)
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

        return _success_result(build_result)


def _success_result(build_result: BuildResult) -> SiteBuildServiceResult:
    output_dir = build_result.output_dir.resolve()
    relpaths = tuple(path.resolve().relative_to(output_dir).as_posix() for path in build_result.generated_pages)
    return SiteBuildServiceResult(
        ok=True,
        output_dir=output_dir,
        generated_pages=build_result.generated_pages,
        copied_assets=build_result.copied_assets,
        warnings=build_result.warnings,
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

