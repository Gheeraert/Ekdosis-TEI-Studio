from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont

from .models import (
    BibliographyBlock,
    BoldRun,
    CapsRun,
    FootnoteRefRun,
    HeadingBlock,
    InlineRun,
    ItalicRun,
    LinkRun,
    ListBlock,
    MarkdownDocument,
    ParagraphBlock,
    QuoteBlock,
    RuleBlock,
    SmallCapsRun,
    SubRun,
    SupRun,
    TextRun,
    UnderlineRun,
)


class PreviewRenderer:
    def __init__(self) -> None:
        self._configured = False

    def _configure_tags(self, text: tk.Text) -> None:
        if self._configured:
            return
        font_name = str(text.cget("font"))
        try:
            base = tkfont.nametofont(font_name)
        except tk.TclError:
            base = tkfont.Font(font=text.cget("font"))
        base_size = int(base.cget("size"))
        if base_size < 0:
            base_size = abs(base_size)
        heading1 = tkfont.Font(font=base)
        heading1.configure(size=max(base_size + 8, 16), weight="bold")
        heading2 = tkfont.Font(font=base)
        heading2.configure(size=max(base_size + 6, 14), weight="bold")
        heading3 = tkfont.Font(font=base)
        heading3.configure(size=max(base_size + 4, 13), weight="bold")
        heading4 = tkfont.Font(font=base)
        heading4.configure(size=max(base_size + 2, 12), weight="bold")
        italic = tkfont.Font(font=base)
        italic.configure(slant="italic")
        bold = tkfont.Font(font=base)
        bold.configure(weight="bold")
        smallcaps = tkfont.Font(font=base)
        smallcaps.configure(size=max(base_size - 1, 8))

        text.tag_configure("h1", font=heading1, spacing1=8, spacing3=4)
        text.tag_configure("h2", font=heading2, spacing1=6, spacing3=3)
        text.tag_configure("h3", font=heading3, spacing1=5, spacing3=2)
        text.tag_configure("h4", font=heading4, spacing1=4, spacing3=2)
        text.tag_configure("italic", font=italic)
        text.tag_configure("bold", font=bold)
        text.tag_configure("underline", underline=True)
        text.tag_configure("sup", offset=6, font=smallcaps)
        text.tag_configure("sub", offset=-3, font=smallcaps)
        text.tag_configure("caps", font=bold)
        text.tag_configure("smallcaps", font=smallcaps)
        text.tag_configure("link", foreground="#1d4ed8", underline=True)
        text.tag_configure("quote", lmargin1=22, lmargin2=22, foreground="#3f3f46")
        text.tag_configure("rule", foreground="#6b7280")
        text.tag_configure("meta_title", font=heading3, spacing1=8, spacing3=4)
        text.tag_configure("footref", offset=6, font=smallcaps, foreground="#374151")
        text.tag_configure("bibl_title", font=heading3, spacing1=8, spacing3=4)
        self._configured = True

    def _insert_runs(
        self,
        text: tk.Text,
        runs: tuple[InlineRun, ...],
        *,
        base_tags: tuple[str, ...] = (),
        caps: bool = False,
        small_caps: bool = False,
        footnote_numbers: dict[str, int] | None = None,
    ) -> None:
        for run in runs:
            if isinstance(run, TextRun):
                value = run.text
                if caps or small_caps:
                    value = value.upper()
                text.insert("end", value, base_tags)
                continue

            if isinstance(run, ItalicRun):
                self._insert_runs(text, run.children, base_tags=base_tags + ("italic",), caps=caps, small_caps=small_caps, footnote_numbers=footnote_numbers)
                continue
            if isinstance(run, BoldRun):
                self._insert_runs(text, run.children, base_tags=base_tags + ("bold",), caps=caps, small_caps=small_caps, footnote_numbers=footnote_numbers)
                continue
            if isinstance(run, UnderlineRun):
                self._insert_runs(text, run.children, base_tags=base_tags + ("underline",), caps=caps, small_caps=small_caps, footnote_numbers=footnote_numbers)
                continue
            if isinstance(run, SupRun):
                self._insert_runs(text, run.children, base_tags=base_tags + ("sup",), caps=caps, small_caps=small_caps, footnote_numbers=footnote_numbers)
                continue
            if isinstance(run, SubRun):
                self._insert_runs(text, run.children, base_tags=base_tags + ("sub",), caps=caps, small_caps=small_caps, footnote_numbers=footnote_numbers)
                continue
            if isinstance(run, CapsRun):
                self._insert_runs(
                    text,
                    run.children,
                    base_tags=base_tags + ("caps",),
                    caps=True,
                    small_caps=False,
                    footnote_numbers=footnote_numbers,
                )
                continue
            if isinstance(run, SmallCapsRun):
                self._insert_runs(
                    text,
                    run.children,
                    base_tags=base_tags + ("smallcaps",),
                    caps=False,
                    small_caps=True,
                    footnote_numbers=footnote_numbers,
                )
                continue
            if isinstance(run, LinkRun):
                self._insert_runs(
                    text,
                    run.children,
                    base_tags=base_tags + ("link",),
                    caps=caps,
                    small_caps=small_caps,
                    footnote_numbers=footnote_numbers,
                )
                text.insert("end", f" ({run.target})", base_tags)
                continue
            if isinstance(run, FootnoteRefRun):
                number = run.identifier
                if footnote_numbers is not None and run.identifier in footnote_numbers:
                    number = str(footnote_numbers[run.identifier])
                text.insert("end", f"[{number}]", base_tags + ("footref",))

    def render(self, text: tk.Text, document: MarkdownDocument) -> None:
        self._configure_tags(text)
        text.configure(state="normal")
        text.delete("1.0", "end")

        footnote_numbers = {identifier: pos + 1 for pos, identifier in enumerate(document.footnote_reference_order)}

        for block in document.blocks:
            if isinstance(block, HeadingBlock):
                tag = f"h{min(max(block.level, 1), 4)}"
                self._insert_runs(text, block.runs, base_tags=(tag,), footnote_numbers=footnote_numbers)
                text.insert("end", "\n", (tag,))
                continue

            if isinstance(block, ParagraphBlock):
                self._insert_runs(text, block.runs, footnote_numbers=footnote_numbers)
                text.insert("end", "\n\n")
                continue

            if isinstance(block, ListBlock):
                for idx, item in enumerate(block.items, start=1):
                    bullet = f"{idx}. " if block.ordered else "• "
                    text.insert("end", bullet)
                    self._insert_runs(text, item, footnote_numbers=footnote_numbers)
                    text.insert("end", "\n")
                text.insert("end", "\n")
                continue

            if isinstance(block, QuoteBlock):
                for paragraph in block.paragraphs:
                    self._insert_runs(text, paragraph, base_tags=("quote",), footnote_numbers=footnote_numbers)
                    text.insert("end", "\n", ("quote",))
                text.insert("end", "\n")
                continue

            if isinstance(block, RuleBlock):
                text.insert("end", "────────────────────\n\n", ("rule",))
                continue

            if isinstance(block, BibliographyBlock):
                text.insert("end", "Bibliographie\n", ("bibl_title",))
                for entry in block.entries:
                    text.insert("end", f"• {entry.raw_text}\n")
                text.insert("end", "\n")
                continue

        referenced = [identifier for identifier in document.footnote_reference_order if identifier in document.footnotes]
        if referenced:
            text.insert("end", "Notes\n", ("meta_title",))
            for identifier in referenced:
                number = footnote_numbers.get(identifier, 0)
                definition = document.footnotes[identifier]
                text.insert("end", f"[{number}] ", ("footref",))
                self._insert_runs(text, definition.runs, footnote_numbers=footnote_numbers)
                text.insert("end", "\n")
            text.insert("end", "\n")

        text.configure(state="disabled")
