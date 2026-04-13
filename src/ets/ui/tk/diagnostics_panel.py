from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from ets.application import AppDiagnostic


class DiagnosticsPanel(ttk.Frame):
    """List of diagnostics with navigation callback."""

    def __init__(self, master: tk.Misc, on_navigate: Callable[[int], None]) -> None:
        super().__init__(master)
        self._on_navigate = on_navigate
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._items: list[AppDiagnostic] = []

        columns = ("level", "code", "line", "message")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=6)
        self.tree.heading("level", text="Niveau")
        self.tree.heading("code", text="Code")
        self.tree.heading("line", text="Ligne")
        self.tree.heading("message", text="Message")
        self.tree.column("level", width=80, stretch=False)
        self.tree.column("code", width=140, stretch=False)
        self.tree.column("line", width=80, stretch=False)
        self.tree.column("message", width=700, stretch=True)
        self.tree.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.bind("<Double-1>", self._handle_open, add="+")

    def _handle_open(self, _event: tk.Event[tk.Misc]) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        idx = int(selection[0])
        if idx >= len(self._items):
            return
        diag = self._items[idx]
        if diag.line_number is not None:
            self._on_navigate(diag.line_number)

    def set_diagnostics(self, diagnostics: list[AppDiagnostic]) -> None:
        self._items = diagnostics
        self.tree.delete(*self.tree.get_children())
        for idx, diag in enumerate(diagnostics):
            line_text = str(diag.line_number) if diag.line_number is not None else ""
            self.tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(diag.level, diag.code, line_text, diag.message),
            )
