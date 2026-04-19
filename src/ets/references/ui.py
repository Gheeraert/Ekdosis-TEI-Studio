from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from .dialogs import open_add_reference_dialog, open_insert_citation_dialog, open_style_dialog
from .models import BibliographyState, ReferenceRecord
from .service import ReferencesService
from .styles import STYLES, get_style


class ReferencesPanel(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        service: ReferencesService | None = None,
        get_current_text: Callable[[], str],
        insert_citation_token: Callable[[str], bool],
    ) -> None:
        super().__init__(master, padding=8)
        self.service = service or ReferencesService()
        self._get_current_text = get_current_text
        self._insert_citation_token = insert_citation_token

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_actions()
        self._build_references_list()
        self._build_bibliography_preview()
        self._refresh_references()
        self.refresh_bibliography()

    def _build_actions(self) -> None:
        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for col in range(5):
            frame.columnconfigure(col, weight=0)
        frame.columnconfigure(5, weight=1)

        ttk.Button(frame, text="Ajouter une référence", command=self.action_add_reference).grid(row=0, column=0, padx=(0, 4))
        ttk.Button(frame, text="Importer des références", command=self.action_import_references).grid(row=0, column=1, padx=4)
        ttk.Button(frame, text="Insérer une citation", command=self.action_insert_citation).grid(row=0, column=2, padx=4)
        ttk.Button(frame, text="Bibliographie", command=self.action_show_bibliography).grid(row=0, column=3, padx=4)
        ttk.Button(frame, text="Style de publication", command=self.action_choose_style).grid(row=0, column=4, padx=4)

    def _build_references_list(self) -> None:
        group = ttk.LabelFrame(self, text="Catalogue des références", padding=8)
        group.grid(row=1, column=0, sticky="nsew")
        group.columnconfigure(0, weight=1)
        group.rowconfigure(1, weight=1)

        search_row = ttk.Frame(group)
        search_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        search_row.columnconfigure(1, weight=1)
        ttk.Label(search_row, text="Recherche").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_row, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew")
        search_entry.bind("<KeyRelease>", self._on_search_change, add="+")

        columns = ("author", "title", "date", "kind")
        self.references_table = ttk.Treeview(group, columns=columns, show="headings", height=10)
        self.references_table.heading("author", text="Auteur(s)")
        self.references_table.heading("title", text="Titre")
        self.references_table.heading("date", text="Date")
        self.references_table.heading("kind", text="Type")
        self.references_table.column("author", width=210, anchor="w")
        self.references_table.column("title", width=420, anchor="w")
        self.references_table.column("date", width=80, anchor="center")
        self.references_table.column("kind", width=90, anchor="center")
        self.references_table.grid(row=1, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(group, orient="vertical", command=self.references_table.yview)
        scroll.grid(row=1, column=1, sticky="ns")
        self.references_table.configure(yscrollcommand=scroll.set)
        self._row_to_reference: dict[str, str] = {}

    def _build_bibliography_preview(self) -> None:
        group = ttk.LabelFrame(self, text="Bibliographie générée", padding=8)
        group.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        group.columnconfigure(0, weight=1)
        group.rowconfigure(1, weight=1)

        top = ttk.Frame(group)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text="Style courant").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.style_label = tk.StringVar(value=get_style(self.service.style_id).label)
        ttk.Label(top, textvariable=self.style_label).grid(row=0, column=1, sticky="w")
        ttk.Button(top, text="Recalculer", command=self.refresh_bibliography).grid(row=0, column=2, sticky="e")

        self.bibliography_text = tk.Text(group, wrap="word", height=8, state="disabled")
        self.bibliography_text.grid(row=1, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(group, orient="vertical", command=self.bibliography_text.yview)
        scroll.grid(row=1, column=1, sticky="ns")
        self.bibliography_text.configure(yscrollcommand=scroll.set)

    def _on_search_change(self, _event: tk.Event[tk.Misc]) -> None:
        self._refresh_references()

    def _refresh_references(self) -> None:
        for item in self.references_table.get_children():
            self.references_table.delete(item)
        self._row_to_reference.clear()
        records = self.service.search_references(self.search_var.get())
        for index, ref in enumerate(records):
            row_id = f"ref{index}"
            self._row_to_reference[row_id] = ref.id
            author = ", ".join(ref.authors) if ref.authors else "Sans auteur"
            self.references_table.insert("", "end", iid=row_id, values=(author, ref.title, ref.date or "", ref.type))

    def refresh_bibliography(self) -> BibliographyState:
        state = self.service.bibliography_from_text(self._get_current_text(), target_context="active")
        self._set_bibliography_text(self.service.bibliography_to_text(state))
        self.style_label.set(get_style(self.service.style_id).label)
        return state

    def _set_bibliography_text(self, text: str) -> None:
        self.bibliography_text.configure(state="normal")
        self.bibliography_text.delete("1.0", "end")
        self.bibliography_text.insert("1.0", text)
        self.bibliography_text.configure(state="disabled")

    def action_add_reference(self) -> None:
        payload = open_add_reference_dialog(self)
        if payload is None:
            return
        authors = [chunk.strip() for chunk in payload.get("authors", "").split(";") if chunk.strip()]
        self.service.add_manual_reference(
            title=payload.get("title", ""),
            authors=authors,
            date=payload.get("date", ""),
            reference_type=payload.get("reference_type", "book"),
            publisher=payload.get("publisher", ""),
            container_title=payload.get("container_title", ""),
            place=payload.get("place", ""),
            volume=payload.get("volume", ""),
            issue=payload.get("issue", ""),
            pages=payload.get("pages", ""),
            url=payload.get("url", ""),
            doi=payload.get("doi", ""),
            source_key=payload.get("source_key", ""),
            editor=payload.get("editor", ""),
            translator=payload.get("translator", ""),
            note=payload.get("note", ""),
        )
        self._refresh_references()
        self.refresh_bibliography()

    def action_import_references(self) -> None:
        selected = filedialog.askopenfilename(
            title="Importer des références",
            filetypes=[
                ("Fichier de références", "*.json *.bib *.bibtex *.ris"),
                ("CSL JSON", "*.json"),
                ("Tous les fichiers", "*.*"),
            ],
        )
        if not selected:
            return
        result = self.service.import_from_file(Path(selected))
        self._refresh_references()
        self.refresh_bibliography()

        if result.diagnostics:
            messages = "\n".join(f"- {item.severity}: {item.message}" for item in result.diagnostics)
            messagebox.showinfo("Importer des références", f"Import terminé ({len(result.references)} entrées).\n\n{messages}", parent=self)
            return
        messagebox.showinfo("Importer des références", f"Import terminé ({len(result.references)} entrées).", parent=self)

    def action_insert_citation(self) -> None:
        references = self.service.all_references()
        if not references:
            messagebox.showinfo("Insérer une citation", "Aucune référence disponible. Ajoutez ou importez des références d'abord.", parent=self)
            return
        payload = open_insert_citation_dialog(self, references=references)
        if payload is None:
            return
        try:
            token = self.service.build_citation_token(
                payload["reference_id"],
                locator=payload.get("locator", ""),
                prefix=payload.get("prefix", ""),
                suffix=payload.get("suffix", ""),
                mode=payload.get("mode", "note"),
            )
        except KeyError:
            messagebox.showerror("Insérer une citation", "La référence sélectionnée n'est plus disponible.", parent=self)
            return
        inserted = self._insert_citation_token(token)
        if not inserted:
            messagebox.showwarning(
                "Insérer une citation",
                "Aucun contexte Markdown actif. Ouvrez l'éditeur Markdown pour insérer la citation.",
                parent=self,
            )
            return
        self.refresh_bibliography()

    def action_show_bibliography(self) -> None:
        state = self.refresh_bibliography()
        message = self.service.bibliography_to_text(state)
        messagebox.showinfo("Bibliographie", message, parent=self)

    def action_choose_style(self) -> None:
        selected = open_style_dialog(self, current_style_id=self.service.style_id)
        if not selected:
            return
        self.service.set_style(selected)
        self.refresh_bibliography()
