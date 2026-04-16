from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ets.site_builder.dramatic_merge import (
    DramaticTeiMergeError,
    DramaticTeiMergeRequest,
    merge_dramatic_tei_acts,
)


@dataclass(frozen=True)
class DramaticTeiMergeServiceResult:
    ok: bool
    merged_xml: str | None = None
    output_path: Path | None = None
    warnings: tuple[str, ...] = ()
    merged_act_count: int = 0
    message: str | None = None
    error_code: str | None = None
    error_detail: str | None = None


class DramaticTeiMergeService:
    """Thin application wrapper around XML-aware dramatic TEI act merge."""

    def merge(self, request: DramaticTeiMergeRequest) -> DramaticTeiMergeServiceResult:
        try:
            merged = merge_dramatic_tei_acts(request)
        except DramaticTeiMergeError as exc:
            return DramaticTeiMergeServiceResult(
                ok=False,
                message="Dramatic TEI merge failed.",
                error_code="E_DRAMATIC_TEI_MERGE",
                error_detail=str(exc),
            )
        except OSError as exc:
            return DramaticTeiMergeServiceResult(
                ok=False,
                message="Dramatic TEI merge I/O failed.",
                error_code="E_DRAMATIC_TEI_MERGE_IO",
                error_detail=str(exc),
            )

        return DramaticTeiMergeServiceResult(
            ok=True,
            merged_xml=merged.merged_xml,
            output_path=merged.output_path,
            warnings=merged.warnings,
            merged_act_count=merged.merged_act_count,
            message="Dramatic TEI merge successful.",
        )


def merge_dramatic_tei_files(request: DramaticTeiMergeRequest) -> DramaticTeiMergeServiceResult:
    service = DramaticTeiMergeService()
    return service.merge(request)
