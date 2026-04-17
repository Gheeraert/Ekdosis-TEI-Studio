from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ets.tools import (
    TextTranscriptionMergeError,
    TextTranscriptionMergeRequest,
    merge_text_transcription_files as _merge_text_transcription_files,
)


@dataclass(frozen=True)
class TextTranscriptionMergeServiceResult:
    ok: bool
    output_path: Path | None = None
    merged_file_count: int = 0
    warnings: tuple[str, ...] = ()
    message: str | None = None
    error_code: str | None = None
    error_detail: str | None = None


class TextTranscriptionMergeService:
    """Thin application wrapper around plain-text transcription merge."""

    def merge(self, request: TextTranscriptionMergeRequest) -> TextTranscriptionMergeServiceResult:
        try:
            merged = _merge_text_transcription_files(request)
        except TextTranscriptionMergeError as exc:
            return TextTranscriptionMergeServiceResult(
                ok=False,
                message="Text transcription merge failed.",
                error_code="E_TEXT_TRANSCRIPTION_MERGE",
                error_detail=str(exc),
            )
        except (OSError, UnicodeError) as exc:
            return TextTranscriptionMergeServiceResult(
                ok=False,
                message="Text transcription merge I/O failed.",
                error_code="E_TEXT_TRANSCRIPTION_MERGE_IO",
                error_detail=str(exc),
            )

        return TextTranscriptionMergeServiceResult(
            ok=True,
            output_path=merged.output_path,
            merged_file_count=merged.merged_file_count,
            message="Text transcription merge successful.",
        )


def merge_text_transcription_files(request: TextTranscriptionMergeRequest) -> TextTranscriptionMergeServiceResult:
    service = TextTranscriptionMergeService()
    return service.merge(request)
