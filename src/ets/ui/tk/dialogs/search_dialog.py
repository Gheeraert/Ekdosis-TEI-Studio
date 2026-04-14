from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class SearchReplaceDialog(tk.Toplevel):
    """Small search/replace dialog."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        on_find_next: Callable[[str], bool],
        on_replace: Callable[[str, str], bool],
        on_replace_all: Callable[[str, str], int],
    ) -> None:
        super().__init__(parent)
        self.title("Rechercher / Remplacer")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._on_find_next = on_find_next
        self._on_replace = on_replace
        self._on_replace_all = on_replace_all

        self.find_var = tk.StringVar()
        self.replace_var = tk.StringVar()
        self.status_var = tk.StringVar(value="")

        frame = ttk.Frame(self, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")
        ttk.Label(frame, text="Rechercher:").grid(row=0, column=0, sticky="e", padx=(0, 6), pady=2)

        self.find_entry = ttk.Entry(frame, textvariable=self.find_var, width=36)
        self.find_entry.grid(row=0, column=1, pady=2)

        ttk.Label(frame, text="Remplacer par:").grid(row=1, column=0, sticky="e", padx=(0, 6), pady=2)
        ttk.Entry(frame, textvariable=self.replace_var, width=36).grid(row=1, column=1, pady=2)

        actions = ttk.Frame(frame)
        actions.grid(row=2, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(actions, text="Trouver suivant", command=self._find_next).grid(row=0, column=0, padx=2)
        ttk.Button(actions, text="Remplacer", command=self._replace_one).grid(row=0, column=1, padx=2)
        ttk.Button(actions, text="Tout remplacer", command=self._replace_all).grid(row=0, column=2, padx=2)
        ttk.Button(actions, text="Fermer", command=self.destroy).grid(row=0, column=3, padx=2)

        ttk.Label(frame, textvariable=self.status_var, foreground="#555").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )

        self.after_idle(self._focus_find_entry)

    def _focus_find_entry(self) -> None:
        self.find_entry.focus_set()
        self.find_entry.select_range(0, "end")
        self.find_entry.icursor("end")

    def _find_next(self) -> None:
        needle = self.find_var.get()
        if not needle:
            self.status_var.set("Saisissez un texte à rechercher.")
            return
        found = self._on_find_next(needle)
        self.status_var.set("Occurrence trouvée." if found else "Aucune occurrence trouvée.")

    def _replace_one(self) -> None:
        needle = self.find_var.get()
        if not needle:
            self.status_var.set("Saisissez un texte à rechercher.")
            return
        replaced = self._on_replace(needle, self.replace_var.get())
        self.status_var.set("Occurrence remplacée." if replaced else "Aucune occurrence à remplacer.")

    def _replace_all(self) -> None:
        needle = self.find_var.get()
        if not needle:
            self.status_var.set("Saisissez un texte à rechercher.")
            return
        count = self._on_replace_all(needle, self.replace_var.get())
        self.status_var.set(f"{count} occurrence(s) remplacée(s).")