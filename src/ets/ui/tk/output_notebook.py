from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from ets.annotations import AnnotationCollection

from .annotation_panel import AnnotationPanel


class OutputNotebook(ttk.Frame):
    """Output tabs with editable TEI and read-only rendered outputs."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_tei_edited: Callable[[], None] | None = None,
        on_annotation_add: Callable[[], None] | None = None,
        on_annotation_edit: Callable[[], None] | None = None,
        on_annotation_delete: Callable[[], None] | None = None,
        on_annotation_select: Callable[[str | None], None] | None = None,
    ) -> None:
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._on_tei_edited = on_tei_edited
        self._suspend_tei_edit_event = False
        self._tei_orig_command = ""

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self.tei_text = self._create_tab("TEI", editable=True)
        self.html_text = self._create_tab("HTML", editable=False)
        self.ekdosis_text = self._create_tab("Ekdosis", editable=False)
        self.annotations_panel = self._create_annotations_tab(
            "Annotations",
            on_add=on_annotation_add,
            on_edit=on_annotation_edit,
            on_delete=on_annotation_delete,
            on_select=on_annotation_select,
        )
        self._install_tei_proxy()
        self.tei_text.bind("<<Modified>>", self._on_tei_modified, add="+")

    def _install_tei_proxy(self) -> None:
        self._tei_orig_command = f"{self.tei_text._w}_orig"
        self.tei_text.tk.call("rename", self.tei_text._w, self._tei_orig_command)
        self.tei_text.tk.createcommand(self.tei_text._w, self._tei_proxy)

    def _tei_proxy(self, *args: object) -> object:
        result = self.tei_text.tk.call(self._tei_orig_command, *args)
        if not self._suspend_tei_edit_event and args:
            command = str(args[0])
            if command in {"insert", "delete", "replace"} and self._on_tei_edited is not None:
                self._on_tei_edited()
        return result

    def _create_tab(self, title: str, *, editable: bool) -> tk.Text:
        frame = ttk.Frame(self.notebook)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        text = tk.Text(frame, wrap="none", state="normal" if editable else "disabled", font=("Consolas", 10), undo=editable)
        text.grid(row=0, column=0, sticky="nsew")
        y_scroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=text.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.notebook.add(frame, text=title)
        return text

    def _create_annotations_tab(
        self,
        title: str,
        *,
        on_add: Callable[[], None] | None,
        on_edit: Callable[[], None] | None,
        on_delete: Callable[[], None] | None,
        on_select: Callable[[str | None], None] | None,
    ) -> AnnotationPanel:
        frame = ttk.Frame(self.notebook)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        panel = AnnotationPanel(frame, on_add=on_add, on_edit=on_edit, on_delete=on_delete, on_select=on_select)
        panel.grid(row=0, column=0, sticky="nsew")
        self.notebook.add(frame, text=title)
        return panel

    @staticmethod
    def _set_text(widget: tk.Text, value: str, *, editable: bool) -> None:
        previous_state = str(widget.cget("state"))
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.edit_reset()
        widget.edit_modified(False)
        widget.configure(state="normal" if editable else "disabled")
        if previous_state == "disabled" and not editable:
            widget.configure(state="disabled")

    def _on_tei_modified(self, _event: tk.Event[tk.Misc]) -> None:
        if self._suspend_tei_edit_event:
            self.tei_text.edit_modified(False)
            return
        if not self.tei_text.edit_modified():
            return
        self.tei_text.edit_modified(False)
        if self._on_tei_edited is not None:
            self._on_tei_edited()

    def set_tei(self, value: str) -> None:
        self._suspend_tei_edit_event = True
        try:
            self._set_text(self.tei_text, value, editable=True)
        finally:
            self._suspend_tei_edit_event = False

    def set_html(self, value: str) -> None:
        self._set_text(self.html_text, value, editable=False)

    def set_ekdosis(self, value: str) -> None:
        self._set_text(self.ekdosis_text, value, editable=False)

    def get_tei(self) -> str:
        return self.tei_text.get("1.0", "end-1c")

    def get_ekdosis(self) -> str:
        return self.ekdosis_text.get("1.0", "end-1c")

    def set_annotations(self, collection: AnnotationCollection) -> None:
        self.annotations_panel.set_annotations(collection)

    def set_annotations_file_path(self, value: str | None) -> None:
        self.annotations_panel.set_file_path(value)

    def selected_annotation_id(self) -> str | None:
        return self.annotations_panel.selected_annotation_id()

    def annotation_row_count(self) -> int:
        return self.annotations_panel.row_count()
