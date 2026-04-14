from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from ets.annotations import AnnotationCollection


def _anchor_summary(annotation: object) -> str:
    anchor = getattr(annotation, "anchor")
    if anchor.kind == "line":
        return f"{anchor.kind} A{anchor.act} S{anchor.scene} L{anchor.line}"
    if anchor.kind == "line_range":
        return f"{anchor.kind} A{anchor.act} S{anchor.scene} L{anchor.start_line}-{anchor.end_line}"
    if anchor.kind == "stage":
        return f"{anchor.kind} A{anchor.act} S{anchor.scene} ST{anchor.stage_index}"
    return anchor.kind


class AnnotationPanel(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        on_add: Callable[[], None] | None = None,
        on_edit: Callable[[], None] | None = None,
        on_delete: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.path_var = tk.StringVar(value="Aucun fichier d'annotations chargé")
        ttk.Label(self, textvariable=self.path_var).grid(row=0, column=0, sticky="ew", pady=(0, 6))

        columns = ("id", "type", "anchor", "preview")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=8)
        self.tree.heading("id", text="ID")
        self.tree.heading("type", text="Type")
        self.tree.heading("anchor", text="Ancre")
        self.tree.heading("preview", text="Contenu")
        self.tree.column("id", width=90, anchor="w")
        self.tree.column("type", width=120, anchor="w")
        self.tree.column("anchor", width=220, anchor="w")
        self.tree.column("preview", width=480, anchor="w")
        self.tree.grid(row=1, column=0, sticky="nsew")

        y_scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        y_scroll.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=y_scroll.set)

        buttons = ttk.Frame(self)
        buttons.grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Button(buttons, text="Ajouter", command=on_add).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(buttons, text="Modifier", command=on_edit).grid(row=0, column=1, padx=(0, 6))
        ttk.Button(buttons, text="Supprimer", command=on_delete).grid(row=0, column=2)

        if on_edit is not None:
            self.tree.bind("<Double-1>", lambda _event: on_edit(), add="+")

    def set_file_path(self, value: str | None) -> None:
        if value:
            self.path_var.set(f"Fichier: {value}")
        else:
            self.path_var.set("Aucun fichier d'annotations chargé")

    def set_annotations(self, collection: AnnotationCollection) -> None:
        self.tree.delete(*self.tree.get_children())
        for annotation in collection.annotations:
            preview = annotation.content.strip().replace("\n", " ")
            if len(preview) > 80:
                preview = preview[:77] + "..."
            self.tree.insert(
                "",
                "end",
                iid=annotation.id,
                values=(annotation.id, annotation.type, _anchor_summary(annotation), preview),
            )

    def selected_annotation_id(self) -> str | None:
        selected = self.tree.selection()
        if not selected:
            return None
        return str(selected[0])

    def row_count(self) -> int:
        return len(self.tree.get_children())
