from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class OutputNotebook(ttk.Frame):
    """Read-only output tabs for TEI and HTML."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self.tei_text = self._create_tab("TEI")
        self.html_text = self._create_tab("HTML")

    def _create_tab(self, title: str) -> tk.Text:
        frame = ttk.Frame(self.notebook)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        text = tk.Text(frame, wrap="none", state="disabled", font=("Consolas", 10))
        text.grid(row=0, column=0, sticky="nsew")
        y_scroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=text.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.notebook.add(frame, text=title)
        return text

    @staticmethod
    def _set_text(widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def set_tei(self, value: str) -> None:
        self._set_text(self.tei_text, value)

    def set_html(self, value: str) -> None:
        self._set_text(self.html_text, value)

