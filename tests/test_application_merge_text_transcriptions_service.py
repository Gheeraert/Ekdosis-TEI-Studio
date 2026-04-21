from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from ets.application import (
    TextTranscriptionMergeRequest,
    TextTranscriptionMergeService,
    merge_text_transcription_files,
)


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = ROOT / "tests" / "_runtime"


def _runtime_dir(prefix: str) -> Path:
    target = RUNTIME_ROOT / f"{prefix}_{uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_text_transcription_merge_service_merges_with_blank_line_and_final_newline() -> None:
    base = _runtime_dir("app_text_merge_ok")
    first = base / "a.txt"
    second = base / "b.txt"
    output = base / "merged.txt"
    first.write_text("A", encoding="utf-8")
    second.write_text("B", encoding="utf-8")

    service = TextTranscriptionMergeService()
    result = service.merge(
        TextTranscriptionMergeRequest(
            input_paths=(first, second),
            output_path=output,
        )
    )

    assert result.ok is True
    assert result.merged_file_count == 2
    assert result.output_path == output.resolve()
    # blank line between merged transcription files; final trailing newline is intentional
    assert output.read_text(encoding="utf-8") == "A\n\nB\n"


def test_text_transcription_merge_service_fails_cleanly_on_invalid_request() -> None:
    base = _runtime_dir("app_text_merge_invalid")
    only = base / "single.txt"
    only.write_text("only", encoding="utf-8")

    result = merge_text_transcription_files(
        TextTranscriptionMergeRequest(
            input_paths=(only,),
            output_path=base / "out.txt",
        )
    )

    assert result.ok is False
    assert result.error_code == "E_TEXT_TRANSCRIPTION_MERGE"
    assert result.error_detail is not None
    assert "At least two input transcription files are required." in result.error_detail
