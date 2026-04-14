from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class ControlBar(ttk.Frame):
    """Middle control bar for config, witness and generation actions."""

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

        # Ligne 1 : infos de configuration
        self.meta_row = ttk.Frame(self)
        self.meta_row.grid(row=0, column=0, sticky="ew")
        self.meta_row.columnconfigure(0, weight=1)

        # Ligne 2 : témoin + boutons
        self.actions_row = ttk.Frame(self)
        self.actions_row.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self.actions_row.columnconfigure(2, weight=1)

        self.status_label = ttk.Label(self.meta_row, textvariable=self.config_status, anchor="w")
        self.status_label.grid(row=0, column=0, sticky="ew")

        self.reference_label = ttk.Label(self.actions_row, text="Témoin de référence :")
        self.reference_label.grid(row=0, column=0, sticky="w")

        self.reference_combo = ttk.Combobox(
            self.actions_row,
            state="readonly",
            textvariable=self.reference_var,
            width=8,
        )
        self.reference_combo.grid(row=0, column=1, sticky="w", padx=(6, 12))
        self.reference_combo.bind("<<ComboboxSelected>>", lambda _event: on_reference_change(), add="+")

        self.buttons_frame = ttk.Frame(self.actions_row)
        self.buttons_frame.grid(row=0, column=2, sticky="e")
        # Compatibility alias kept for existing tests and lightweight responsive relayout.
        self.buttons_row = self.buttons_frame
        for i in range(5):
            self.buttons_frame.columnconfigure(i, weight=0)

        self.validate_button = ttk.Button(self.buttons_frame, text="Valider", command=on_validate)
        self.generate_tei_button = ttk.Button(self.buttons_frame, text="Générer TEI", command=on_generate_tei)
        self.preview_html_button = ttk.Button(self.buttons_frame, text="Aperçu HTML", command=on_preview_html)
        self.export_tei_button = ttk.Button(self.buttons_frame, text="Exporter TEI", command=on_export_tei)
        self.export_html_button = ttk.Button(self.buttons_frame, text="Exporter HTML", command=on_export_html)

        buttons = [
            self.validate_button,
            self.generate_tei_button,
            self.preview_html_button,
            self.export_tei_button,
            self.export_html_button,
        ]
        for index, button in enumerate(buttons):
            button.grid(row=0, column=index, padx=2)

    def _relayout(self, width: int) -> None:
        if width < 1000:
            self.buttons_frame.grid_configure(row=1, column=0, columnspan=3, sticky="w", pady=(6, 0))
        else:
            self.buttons_frame.grid_configure(row=0, column=2, columnspan=1, sticky="e", pady=0)

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
