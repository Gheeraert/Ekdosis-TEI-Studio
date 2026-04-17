from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from ets.tools import TextTranscriptionMergeError, TextTranscriptionMergeRequest, merge_text_transcription_files


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = ROOT / "tests" / "_runtime"


def _runtime_dir(prefix: str) -> Path:
    target = RUNTIME_ROOT / f"{prefix}_{uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_merge_text_transcriptions_preserves_order_and_writes_output() -> None:
    base = _runtime_dir("tools_text_merge_order")
    first = base / "a.txt"
    second = base / "b.txt"
    output = base / "merged.txt"
    first.write_text("FIRST", encoding="utf-8")
    second.write_text("SECOND", encoding="utf-8")

    result = merge_text_transcription_files(
        TextTranscriptionMergeRequest(
            input_paths=(second, first),
            output_path=output,
        )
    )

    assert result.merged_file_count == 2
    assert result.output_path == output.resolve()
    assert result.merged_text == "SECONDFIRST"
    assert output.read_text(encoding="utf-8") == "SECONDFIRST"


def test_merge_text_transcriptions_supports_separator() -> None:
    base = _runtime_dir("tools_text_merge_separator")
    first = base / "a.txt"
    second = base / "b.txt"
    output = base / "merged.txt"
    first.write_text("A", encoding="utf-8")
    second.write_text("B", encoding="utf-8")

    result = merge_text_transcription_files(
        TextTranscriptionMergeRequest(
            input_paths=(first, second),
            output_path=output,
            separator="\n\n",
        )
    )

    assert result.merged_text == "A\n\nB"
    assert output.read_text(encoding="utf-8") == "A\n\nB"


def test_merge_text_transcriptions_requires_at_least_two_inputs() -> None:
    base = _runtime_dir("tools_text_merge_invalid")
    only = base / "single.txt"
    only.write_text("only", encoding="utf-8")

    with pytest.raises(TextTranscriptionMergeError):
        merge_text_transcription_files(
            TextTranscriptionMergeRequest(
                input_paths=(only,),
                output_path=base / "out.txt",
            )
        )
