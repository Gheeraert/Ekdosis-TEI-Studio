from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .models import MarkdownDiagnostic, MarkdownDocument, MarkdownParseResult
from .parser import parse_markdown
from .tei_export import export_tei_document, export_tei_fragment


@dataclass(frozen=True)
class MarkdownTeiExportResult:
    tei_xml: str
    diagnostics: tuple[MarkdownDiagnostic, ...] = field(default_factory=tuple)


class MarkdownEditorService:
    def parse(self, text: str) -> MarkdownParseResult:
        return parse_markdown(text)

    def validate(self, text: str) -> tuple[MarkdownDiagnostic, ...]:
        result = self.parse(text)
        return result.diagnostics

    def export_document(
        self,
        text: str,
        *,
        title: str = "Notice éditoriale",
        author: str = "",
        editor: str = "",
        notice_type: str = "notice",
    ) -> MarkdownTeiExportResult:
        parsed = self.parse(text)
        xml = export_tei_document(
            parsed.document,
            title=title,
            author=author,
            editor=editor,
            notice_type=notice_type,
        )
        return MarkdownTeiExportResult(tei_xml=xml, diagnostics=parsed.diagnostics)

    def export_fragment(
        self,
        text: str,
        *,
        notice_type: str = "notice",
    ) -> MarkdownTeiExportResult:
        parsed = self.parse(text)
        xml = export_tei_fragment(parsed.document, notice_type=notice_type)
        return MarkdownTeiExportResult(tei_xml=xml, diagnostics=parsed.diagnostics)

    @staticmethod
    def save_markdown(text: str, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path.resolve()

    @staticmethod
    def load_markdown(input_path: str | Path) -> str:
        path = Path(input_path)
        return path.read_text(encoding="utf-8")

    @staticmethod
    def save_tei(tei_xml: str, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(tei_xml, encoding="utf-8")
        return path.resolve()

    @staticmethod
    def document_title(document: MarkdownDocument) -> str:
        for block in document.blocks:
            heading_level = getattr(block, "level", None)
            heading_runs = getattr(block, "runs", None)
            if heading_level == 1 and isinstance(heading_runs, tuple):
                text_chunks = []
                for run in heading_runs:
                    if hasattr(run, "text"):
                        text_chunks.append(getattr(run, "text", ""))
                candidate = "".join(text_chunks).strip()
                if candidate:
                    return candidate
        return "Notice éditoriale"
