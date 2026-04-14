from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class ControlBar(ttk.Frame):
    """Middle control bar for config, witness and generation actions."""

    _WRAP_THRESHOLD = 1030

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_reference_change: Callable[[], None],
        on_validate: Callable[[], None],
        on_generate_tei: Callable[[], None],
        on_preview_html: Callable[[], None],
        on_export_tei: Callable[[], None],
        on_export_html: Callable[[], None],
    ) -> None:
        super().__init__(master, padding=(6, 6))
        self.columnconfigure(0, weight=1)

        self.config_status = tk.StringVar(value="Configuration: aucune")
        self.reference_var = tk.StringVar(value="")

        self.meta_row = ttk.Frame(self)
        self.meta_row.grid(row=0, column=0, sticky="ew")
        self.meta_row.columnconfigure(1, weight=1)

        self.buttons_row = ttk.Frame(self)
        self.buttons_row.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        self.status_label = ttk.Label(self.meta_row, textvariable=self.config_status)
        self.reference_label = ttk.Label(self.meta_row, text="Témoin de référence:")
        self.reference_combo = ttk.Combobox(self.meta_row, state="readonly", textvariable=self.reference_var, width=12)
        self.reference_combo.bind("<<ComboboxSelected>>", lambda _event: on_reference_change(), add="+")

        self.validate_button = ttk.Button(self.buttons_row, text="Valider", command=on_validate)
        self.generate_tei_button = ttk.Button(self.buttons_row, text="Générer TEI", command=on_generate_tei)
        self.preview_html_button = ttk.Button(self.buttons_row, text="Aperçu HTML", command=on_preview_html)
        self.export_tei_button = ttk.Button(self.buttons_row, text="Exporter TEI", command=on_export_tei)
        self.export_html_button = ttk.Button(self.buttons_row, text="Exporter HTML", command=on_export_html)

        self._layout_wrapped = True
        self.bind("<Configure>", self._on_configure, add="+")
        self.after_idle(lambda: self._relayout(self.winfo_width()))

    def _on_configure(self, _event: tk.Event[tk.Misc]) -> None:
        self._relayout(self.winfo_width())

    def _clear_grid(self, frame: ttk.Frame) -> None:
        for child in frame.winfo_children():
            child.grid_forget()

    def _relayout(self, width: int) -> None:
        wrapped = width < self._WRAP_THRESHOLD
        if wrapped == self._layout_wrapped and self.status_label.winfo_manager():
            return

        self._clear_grid(self.meta_row)
        self._clear_grid(self.buttons_row)

        self.status_label.grid(row=0, column=0, sticky="w", padx=(0, 12))
        self.reference_label.grid(row=0, column=2, sticky="e")
        self.reference_combo.grid(row=0, column=3, sticky="w", padx=(6, 0))

        buttons = [
            self.validate_button,
            self.generate_tei_button,
            self.preview_html_button,
            self.export_tei_button,
            self.export_html_button,
        ]

        if wrapped:
            for index, button in enumerate(buttons):
                button.grid(row=0, column=index, padx=2, pady=1, sticky="ew")
                self.buttons_row.columnconfigure(index, weight=1)
            self.buttons_row.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        else:
            for index in range(len(buttons)):
                self.buttons_row.columnconfigure(index, weight=0)
            for index, button in enumerate(buttons):
                button.grid(row=0, column=index, padx=2)
            self.buttons_row.grid(row=0, column=1, sticky="e")

        self._layout_wrapped = wrapped

    def set_config_status(self, value: str) -> None:
        self.config_status.set(value)

    def set_reference_choices(self, witness_sigla: list[str], selected_index: int) -> None:
        self.reference_combo["values"] = witness_sigla
        if witness_sigla and 0 <= selected_index < len(witness_sigla):
            self.reference_var.set(witness_sigla[selected_index])
            self.reference_combo.configure(state="readonly")
        else:
            self.reference_var.set("")
            self.reference_combo.configure(state="disabled")

    def selected_reference(self) -> str:
        return self.reference_var.get().strip()
