from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .models import ReferenceRecord
from .styles import STYLES, get_style


def open_add_reference_dialog(parent: tk.Misc) -> dict[str, str] | None:
    dialog = AddReferenceDialog(parent)
    parent.wait_window(dialog)
    return dialog.result


def open_insert_citation_dialog(parent: tk.Misc, references: tuple[ReferenceRecord, ...]) -> dict[str, str] | None:
    dialog = InsertCitationDialog(parent, references=references)
    parent.wait_window(dialog)
    return dialog.result


def open_style_dialog(parent: tk.Misc, current_style_id: str) -> str | None:
    dialog = PublicationStyleDialog(parent, current_style_id=current_style_id)
    parent.wait_window(dialog)
    return dialog.result


class AddReferenceDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.title("Ajouter une référence")
        self.resizable(False, False)
        self.result: dict[str, str] | None = None
        self.transient(parent.winfo_toplevel())

        self.columnconfigure(0, weight=1)
        body = ttk.Frame(self, padding=10)
        body.grid(row=0, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)

        self._vars: dict[str, tk.StringVar] = {
            "authors": tk.StringVar(),
            "title": tk.StringVar(),
            "date": tk.StringVar(),
            "reference_type": tk.StringVar(value="book"),
            "publisher": tk.StringVar(),
            "container_title": tk.StringVar(),
            "place": tk.StringVar(),
            "editor": tk.StringVar(),
            "translator": tk.StringVar(),
            "volume": tk.StringVar(),
            "issue": tk.StringVar(),
            "pages": tk.StringVar(),
            "url": tk.StringVar(),
            "doi": tk.StringVar(),
            "source_key": tk.StringVar(),
            "note": tk.StringVar(),
        }

        self._entries: dict[str, ttk.Entry] = {}
        minimum_fields = [
            ("Auteur(s)", "authors"),
            ("Titre", "title"),
            ("Date", "date"),
            ("Type", "reference_type"),
            ("Éditeur", "publisher"),
            ("Lieu", "place"),
        ]
        for row, (label, key) in enumerate(minimum_fields):
            ttk.Label(body, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
            entry = ttk.Entry(body, textvariable=self._vars[key], width=44)
            entry.grid(row=row, column=1, sticky="ew", pady=2)
            self._entries[key] = entry

        self._advanced_visible = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            body,
            text="Afficher les champs avancés",
            variable=self._advanced_visible,
            command=self._toggle_advanced,
        ).grid(row=len(minimum_fields), column=0, columnspan=2, sticky="w", pady=(8, 4))

        self._advanced = ttk.Frame(body)
        self._advanced.columnconfigure(1, weight=1)
        self._advanced.grid(row=len(minimum_fields) + 1, column=0, columnspan=2, sticky="ew")
        self._advanced.grid_remove()

        advanced_fields = [
            ("Contenant", "container_title"),
            ("Directeur", "editor"),
            ("Traducteur", "translator"),
            ("Volume", "volume"),
            ("Numéro", "issue"),
            ("Pages", "pages"),
            ("Revue / Contenant", "container_title"),
            ("URL", "url"),
            ("DOI", "doi"),
            ("Clé source", "source_key"),
            ("Note interne", "note"),
        ]
        for row, (label, key) in enumerate(advanced_fields):
            ttk.Label(self._advanced, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
            ttk.Entry(self._advanced, textvariable=self._vars[key], width=44).grid(row=row, column=1, sticky="ew", pady=2)

        actions = ttk.Frame(self, padding=(10, 0, 10, 10))
        actions.grid(row=1, column=0, sticky="e")
        ttk.Button(actions, text="Annuler", command=self.destroy).grid(row=0, column=0, padx=4)
        ttk.Button(actions, text="Ajouter", command=self._submit).grid(row=0, column=1, padx=4)

        self.bind("<Escape>", lambda _event: self.destroy(), add="+")
        self.bind("<Return>", lambda _event: self._submit(), add="+")
        self.after(20, self.lift)
        self.after(40, self.grab_set)

    def _toggle_advanced(self) -> None:
        if self._advanced_visible.get():
            self._advanced.grid()
        else:
            self._advanced.grid_remove()

    def _submit(self) -> None:
        title = self._vars["title"].get().strip()
        if not title:
            messagebox.showwarning("Ajouter une référence", "Le titre est obligatoire.", parent=self)
            title_entry = self._entries.get("title")
            if title_entry is not None:
                title_entry.focus_set()
            return
        self.result = {key: var.get().strip() for key, var in self._vars.items()}
        self.destroy()


class InsertCitationDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, *, references: tuple[ReferenceRecord, ...]) -> None:
        super().__init__(parent)
        self.title("Insérer une citation")
        self.resizable(True, True)
        self.minsize(640, 420)
        self.result: dict[str, str] | None = None
        self._references = references
        self._filtered = list(references)
        self.transient(parent.winfo_toplevel())

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        top = ttk.Frame(self, padding=10)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text="Rechercher").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.query = tk.StringVar()
        query_entry = ttk.Entry(top, textvariable=self.query)
        query_entry.grid(row=0, column=1, sticky="ew")
        query_entry.bind("<KeyRelease>", self._filter, add="+")

        center = ttk.Frame(self, padding=(10, 0, 10, 0))
        center.grid(row=1, column=0, sticky="nsew")
        center.columnconfigure(0, weight=1)
        center.rowconfigure(0, weight=1)

        columns = ("author", "title", "date")
        self.table = ttk.Treeview(center, columns=columns, show="headings", selectmode="browse", height=10)
        self.table.heading("author", text="Auteur(s)")
        self.table.heading("title", text="Titre")
        self.table.heading("date", text="Date")
        self.table.column("author", width=180, anchor="w")
        self.table.column("title", width=320, anchor="w")
        self.table.column("date", width=80, anchor="center")
        self.table.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(center, orient="vertical", command=self.table.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.table.configure(yscrollcommand=scroll.set)

        self._row_to_reference: dict[str, str] = {}
        self._fill_table(self._filtered)
        self.table.bind("<Double-1>", lambda _event: self._submit(), add="+")

        details = ttk.LabelFrame(self, text="Précisions facultatives", padding=10)
        details.grid(row=2, column=0, sticky="ew", padx=10, pady=(8, 0))
        details.columnconfigure(1, weight=1)
        details.columnconfigure(3, weight=1)
        self.locator = tk.StringVar()
        self.prefix = tk.StringVar()
        self.suffix = tk.StringVar()
        self.mode = tk.StringVar(value="note")
        ttk.Label(details, text="Page / Folio / Tome / Scène").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Entry(details, textvariable=self.locator).grid(row=0, column=1, sticky="ew", padx=(0, 12))
        ttk.Label(details, text="Préfixe").grid(row=0, column=2, sticky="w", padx=(0, 6))
        ttk.Entry(details, textvariable=self.prefix).grid(row=0, column=3, sticky="ew")
        ttk.Label(details, text="Suffixe").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=(6, 0))
        ttk.Entry(details, textvariable=self.suffix).grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=(6, 0))
        ttk.Label(details, text="Mode").grid(row=1, column=2, sticky="w", padx=(0, 6), pady=(6, 0))
        ttk.Combobox(details, textvariable=self.mode, values=("note", "author-date"), state="readonly", width=16).grid(
            row=1, column=3, sticky="w", pady=(6, 0)
        )

        actions = ttk.Frame(self, padding=10)
        actions.grid(row=3, column=0, sticky="e")
        ttk.Button(actions, text="Annuler", command=self.destroy).grid(row=0, column=0, padx=4)
        ttk.Button(actions, text="Insérer", command=self._submit).grid(row=0, column=1, padx=4)

        self.bind("<Escape>", lambda _event: self.destroy(), add="+")
        self.after(20, self.lift)
        self.after(40, self.grab_set)

    def _fill_table(self, references: list[ReferenceRecord]) -> None:
        for item in self.table.get_children():
            self.table.delete(item)
        self._row_to_reference.clear()
        for index, ref in enumerate(references):
            row_id = f"r{index}"
            self._row_to_reference[row_id] = ref.id
            author_text = ", ".join(ref.authors) if ref.authors else "Sans auteur"
            self.table.insert("", "end", iid=row_id, values=(author_text, ref.title, ref.date or ""))
        if references:
            first = self.table.get_children()[0]
            self.table.selection_set(first)
            self.table.focus(first)

    def _filter(self, _event: tk.Event[tk.Misc]) -> None:
        query = self.query.get().strip().lower()
        if not query:
            self._filtered = list(self._references)
        else:
            self._filtered = [
                ref
                for ref in self._references
                if query in " ".join((ref.title, " ".join(ref.authors), ref.date or "")).lower()
            ]
        self._fill_table(self._filtered)

    def _submit(self) -> None:
        selected = self.table.selection()
        if not selected:
            return
        row = selected[0]
        reference_id = self._row_to_reference.get(row)
        if not reference_id:
            return
        self.result = {
            "reference_id": reference_id,
            "locator": self.locator.get().strip(),
            "prefix": self.prefix.get().strip(),
            "suffix": self.suffix.get().strip(),
            "mode": self.mode.get().strip() or "note",
        }
        self.destroy()


class PublicationStyleDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, *, current_style_id: str) -> None:
        super().__init__(parent)
        self.title("Style de publication")
        self.resizable(False, False)
        self.result: str | None = None
        self.transient(parent.winfo_toplevel())

        body = ttk.Frame(self, padding=10)
        body.grid(row=0, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        ttk.Label(body, text="Choisir un style").grid(row=0, column=0, sticky="w")

        self.style_var = tk.StringVar(value=current_style_id)
        values = [style.style_id for style in STYLES]
        combo = ttk.Combobox(body, textvariable=self.style_var, values=values, state="readonly", width=26)
        combo.grid(row=1, column=0, sticky="ew", pady=(4, 6))

        current = get_style(current_style_id)
        self.preview_var = tk.StringVar(value=current.description)
        ttk.Label(body, textvariable=self.preview_var, wraplength=360).grid(row=2, column=0, sticky="w")
        combo.bind("<<ComboboxSelected>>", self._refresh_help, add="+")

        actions = ttk.Frame(self, padding=(10, 0, 10, 10))
        actions.grid(row=1, column=0, sticky="e")
        ttk.Button(actions, text="Annuler", command=self.destroy).grid(row=0, column=0, padx=4)
        ttk.Button(actions, text="Appliquer", command=self._submit).grid(row=0, column=1, padx=4)

        self.bind("<Escape>", lambda _event: self.destroy(), add="+")
        self.bind("<Return>", lambda _event: self._submit(), add="+")
        self.after(20, self.lift)
        self.after(40, self.grab_set)

    def _refresh_help(self, _event: tk.Event[tk.Misc]) -> None:
        style = get_style(self.style_var.get())
        self.preview_var.set(style.description)

    def _submit(self) -> None:
        self.result = self.style_var.get().strip()
        self.destroy()
