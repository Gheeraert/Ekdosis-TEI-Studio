from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
from typing import Callable


@dataclass(frozen=True)
class SourceSearchOptions:
    pattern: str
    replacement: str
    case_sensitive: bool
    whole_word: bool
    regex: bool
    in_selection: bool


class SourceSearchReplaceDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        *,
        on_find: Callable[[SourceSearchOptions, bool], bool],
        on_replace: Callable[[SourceSearchOptions], bool],
        on_replace_all: Callable[[SourceSearchOptions], int],
    ) -> None:
        super().__init__(parent)
        self.title("Rechercher / Remplacer (source)")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._on_find = on_find
        self._on_replace = on_replace
        self._on_replace_all = on_replace_all

        self.pattern_var = tk.StringVar()
        self.replacement_var = tk.StringVar()
        self.case_var = tk.BooleanVar(value=False)
        self.whole_word_var = tk.BooleanVar(value=False)
        self.regex_var = tk.BooleanVar(value=False)
        self.selection_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="")

        frame = ttk.Frame(self, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Rechercher:").grid(row=0, column=0, sticky="e", padx=(0, 6), pady=2)
        self.pattern_entry = ttk.Entry(frame, textvariable=self.pattern_var, width=40)
        self.pattern_entry.grid(row=0, column=1, columnspan=3, sticky="ew", pady=2)

        ttk.Label(frame, text="Remplacer par:").grid(row=1, column=0, sticky="e", padx=(0, 6), pady=2)
        ttk.Entry(frame, textvariable=self.replacement_var, width=40).grid(row=1, column=1, columnspan=3, sticky="ew", pady=2)

        options = ttk.LabelFrame(frame, text="Options", padding=8)
        options.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(8, 6))
        ttk.Checkbutton(options, text="Casse sensible", variable=self.case_var).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(options, text="Mot entier", variable=self.whole_word_var).grid(row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Checkbutton(options, text="Regex", variable=self.regex_var).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(options, text="Portée: sélection", variable=self.selection_var).grid(row=1, column=1, sticky="w", padx=(8, 0))

        actions = ttk.Frame(frame)
        actions.grid(row=3, column=0, columnspan=4, sticky="e", pady=(4, 0))
        ttk.Button(actions, text="Précédent", command=lambda: self._find(backward=True)).grid(row=0, column=0, padx=2)
        ttk.Button(actions, text="Suivant", command=lambda: self._find(backward=False)).grid(row=0, column=1, padx=2)
        ttk.Button(actions, text="Remplacer", command=self._replace).grid(row=0, column=2, padx=2)
        ttk.Button(actions, text="Tout remplacer", command=self._replace_all).grid(row=0, column=3, padx=2)
        ttk.Button(actions, text="Fermer", command=self.destroy).grid(row=0, column=4, padx=2)

        ttk.Label(frame, textvariable=self.status_var, foreground="#4b5563").grid(
            row=4, column=0, columnspan=4, sticky="w", pady=(8, 0)
        )

        self.after_idle(self._focus)

    def _focus(self) -> None:
        self.pattern_entry.focus_set()
        self.pattern_entry.select_range(0, "end")
        self.pattern_entry.icursor("end")

    def _current_options(self) -> SourceSearchOptions:
        return SourceSearchOptions(
            pattern=self.pattern_var.get(),
            replacement=self.replacement_var.get(),
            case_sensitive=self.case_var.get(),
            whole_word=self.whole_word_var.get(),
            regex=self.regex_var.get(),
            in_selection=self.selection_var.get(),
        )

    def _find(self, *, backward: bool) -> None:
        options = self._current_options()
        if not options.pattern:
            self.status_var.set("Saisissez un motif de recherche.")
            return
        found = self._on_find(options, backward)
        self.status_var.set("Occurrence trouvée." if found else "Aucune occurrence.")

    def _replace(self) -> None:
        options = self._current_options()
        if not options.pattern:
            self.status_var.set("Saisissez un motif de recherche.")
            return
        replaced = self._on_replace(options)
        self.status_var.set("Occurrence remplacée." if replaced else "Aucune occurrence à remplacer.")

    def _replace_all(self) -> None:
        options = self._current_options()
        if not options.pattern:
            self.status_var.set("Saisissez un motif de recherche.")
            return
        count = self._on_replace_all(options)
        self.status_var.set(f"{count} occurrence(s) remplacée(s).")


class PreviewSearchDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        *,
        on_find_next: Callable[[str, bool], bool],
    ) -> None:
        super().__init__(parent)
        self.title("Rechercher dans l’aperçu")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._on_find_next = on_find_next
        self.query_var = tk.StringVar()
        self.status_var = tk.StringVar(value="")

        frame = ttk.Frame(self, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Texte:").grid(row=0, column=0, sticky="e", padx=(0, 6))
        self.entry = ttk.Entry(frame, textvariable=self.query_var, width=36)
        self.entry.grid(row=0, column=1, columnspan=2, sticky="ew")

        ttk.Button(frame, text="Précédent", command=lambda: self._search(backward=True)).grid(row=1, column=1, sticky="e", pady=(8, 0), padx=2)
        ttk.Button(frame, text="Suivant", command=lambda: self._search(backward=False)).grid(row=1, column=2, sticky="w", pady=(8, 0), padx=2)
        ttk.Button(frame, text="Fermer", command=self.destroy).grid(row=1, column=3, sticky="w", pady=(8, 0), padx=2)

        ttk.Label(frame, textvariable=self.status_var, foreground="#4b5563").grid(
            row=2, column=0, columnspan=4, sticky="w", pady=(8, 0)
        )

        self.after_idle(self._focus)

    def _focus(self) -> None:
        self.entry.focus_set()
        self.entry.select_range(0, "end")
        self.entry.icursor("end")

    def _search(self, *, backward: bool) -> None:
        query = self.query_var.get()
        if not query:
            self.status_var.set("Saisissez un texte à rechercher.")
            return
        found = self._on_find_next(query, backward)
        self.status_var.set("Occurrence trouvée." if found else "Aucune occurrence.")
