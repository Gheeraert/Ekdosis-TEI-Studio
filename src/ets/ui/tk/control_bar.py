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
        self.columnconfigure(1, weight=1)

        self.config_status = tk.StringVar(value="Configuration: aucune")
        self.reference_var = tk.StringVar(value="")

        ttk.Label(self, textvariable=self.config_status).grid(row=0, column=0, sticky="w", padx=(0, 12))

        ttk.Label(self, text="Témoin de référence:").grid(row=0, column=1, sticky="e")
        self.reference_combo = ttk.Combobox(self, state="readonly", textvariable=self.reference_var, width=12)
        self.reference_combo.grid(row=0, column=2, sticky="w", padx=(6, 12))
        self.reference_combo.bind("<<ComboboxSelected>>", lambda _event: on_reference_change(), add="+")

        ttk.Button(self, text="Valider", command=on_validate).grid(row=0, column=3, padx=2)
        ttk.Button(self, text="Générer TEI", command=on_generate_tei).grid(row=0, column=4, padx=2)
        ttk.Button(self, text="Aperçu HTML", command=on_preview_html).grid(row=0, column=5, padx=2)
        ttk.Button(self, text="Exporter TEI", command=on_export_tei).grid(row=0, column=6, padx=2)
        ttk.Button(self, text="Exporter HTML", command=on_export_html).grid(row=0, column=7, padx=2)

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

