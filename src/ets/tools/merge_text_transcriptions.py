from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TextTranscriptionMergeRequest:
    input_paths: tuple[Path, ...]
    output_path: Path
    separator: str = ""


@dataclass(frozen=True)
class TextTranscriptionMergeOutcome:
    merged_text: str
    output_path: Path
    merged_file_count: int


class TextTranscriptionMergeError(ValueError):
    """Raised when a text transcription merge request is invalid."""


from pathlib import Path

def merge_text_transcription_files(request: TextTranscriptionMergeRequest) -> TextTranscriptionMergeOutcome:
    if len(request.input_paths) < 2:
        raise TextTranscriptionMergeError("At least two input transcription files are required.")

    resolved_inputs = tuple(Path(path).resolve() for path in request.input_paths)
    output_path = Path(request.output_path).resolve()

    chunks = [path.read_text(encoding="utf-8").rstrip("\n\r") for path in resolved_inputs]

    boundary = request.separator if request.separator else "\n"
    merged_text = boundary.join(chunks) + "\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(merged_text, encoding="utf-8")

    return TextTranscriptionMergeOutcome(
        merged_text=merged_text,
        output_path=output_path,
        merged_file_count=len(resolved_inputs),
    )
