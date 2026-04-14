from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class AnnotationDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, initial: dict[str, object] | None = None, *, id_readonly: bool = False) -> None:
        super().__init__(parent)
        self.title("Annotation")
        self.transient(parent.winfo_toplevel())
        self.resizable(True, True)
        self.result: dict[str, object] | None = None
        self._initial = initial or {}

        frame = ttk.Frame(self, padding=8)
        frame.grid(sticky="nsew")
        self.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        self.id_var = tk.StringVar(value=str(self._initial.get("id", "")))
        self.type_var = tk.StringVar(value=str(self._initial.get("type", "explicative")))
        self.kind_var = tk.StringVar(value=str(self._anchor_value("kind", "line")))
        self.act_var = tk.StringVar(value=str(self._anchor_value("act", "1")))
        self.scene_var = tk.StringVar(value=str(self._anchor_value("scene", "1")))
        self.line_var = tk.StringVar(value=str(self._anchor_value("line", "")))
        self.start_line_var = tk.StringVar(value=str(self._anchor_value("start_line", "")))
        self.end_line_var = tk.StringVar(value=str(self._anchor_value("end_line", "")))
        self.stage_index_var = tk.StringVar(value=str(self._anchor_value("stage_index", "")))
        self.resp_var = tk.StringVar(value=str(self._initial.get("resp", "")))
        self.status_var = tk.StringVar(value=str(self._initial.get("status", "draft")))
        self.keywords_var = tk.StringVar(value=", ".join(self._initial.get("keywords", [])))  # type: ignore[arg-type]

        row = 0
        ttk.Label(frame, text="ID").grid(row=row, column=0, sticky="w", padx=(0, 6), pady=2)
        self.id_entry = ttk.Entry(frame, textvariable=self.id_var, state="readonly" if id_readonly else "normal")
        self.id_entry.grid(row=row, column=1, sticky="ew", pady=2)
        row += 1
        row = self._add_combo(
            frame,
            row,
            "Type",
            self.type_var,
            ["explicative", "lexicale", "intertextuelle", "dramaturgique", "textuelle", "bibliographique"],
        )
        row = self._add_combo(frame, row, "Ancre", self.kind_var, ["line", "line_range", "stage"])
        row = self._add_entry(frame, row, "Acte", self.act_var)
        row = self._add_entry(frame, row, "Scène", self.scene_var)
        row = self._add_entry(frame, row, "Ligne", self.line_var)
        row = self._add_entry(frame, row, "Ligne début", self.start_line_var)
        row = self._add_entry(frame, row, "Ligne fin", self.end_line_var)
        row = self._add_entry(frame, row, "Index didascalie", self.stage_index_var)

        ttk.Label(frame, text="Contenu").grid(row=row, column=0, sticky="nw", padx=(0, 6), pady=2)
        self.content_text = tk.Text(frame, height=5, wrap="word")
        self.content_text.grid(row=row, column=1, sticky="nsew", pady=2)
        self.content_text.insert("1.0", str(self._initial.get("content", "")))
        row += 1

        row = self._add_entry(frame, row, "Resp", self.resp_var)
        row = self._add_combo(frame, row, "Statut", self.status_var, ["draft", "reviewed", "validated"])
        row = self._add_entry(frame, row, "Mots-clés (,)", self.keywords_var)

        buttons = ttk.Frame(frame)
        buttons.grid(row=row, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(buttons, text="Annuler", command=self._on_cancel).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(buttons, text="Valider", command=self._on_ok).grid(row=0, column=1)

        self.kind_var.trace_add("write", lambda *_args: self._refresh_kind_fields())
        self._refresh_kind_fields()
        self.grab_set()
        self.wait_visibility()
        self.focus_set()

    def _anchor_value(self, key: str, default: object) -> object:
        anchor = self._initial.get("anchor")
        if isinstance(anchor, dict) and key in anchor:
            return anchor[key]
        return default

    @staticmethod
    def _add_entry(frame: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> int:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=(0, 6), pady=2)
        ttk.Entry(frame, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=2)
        return row + 1

    @staticmethod
    def _add_combo(frame: ttk.Frame, row: int, label: str, variable: tk.StringVar, values: list[str]) -> int:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=(0, 6), pady=2)
        ttk.Combobox(frame, textvariable=variable, state="readonly", values=values).grid(row=row, column=1, sticky="ew", pady=2)
        return row + 1

    def _refresh_kind_fields(self) -> None:
        kind = self.kind_var.get()
        if kind == "line":
            self.start_line_var.set("")
            self.end_line_var.set("")
            self.stage_index_var.set("")
        elif kind == "line_range":
            self.line_var.set("")
            self.stage_index_var.set("")
        elif kind == "stage":
            self.line_var.set("")
            self.start_line_var.set("")
            self.end_line_var.set("")

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()

    def _on_ok(self) -> None:
        kind = self.kind_var.get().strip()
        anchor: dict[str, object] = {
            "kind": kind,
            "act": self.act_var.get().strip(),
            "scene": self.scene_var.get().strip(),
        }
        if kind == "line":
            anchor["line"] = self.line_var.get().strip()
        elif kind == "line_range":
            anchor["start_line"] = self.start_line_var.get().strip()
            anchor["end_line"] = self.end_line_var.get().strip()
        elif kind == "stage":
            raw_stage = self.stage_index_var.get().strip()
            anchor["stage_index"] = int(raw_stage) if raw_stage.isdigit() else raw_stage

        raw_keywords = [part.strip() for part in self.keywords_var.get().split(",")]
        keywords = [item for item in raw_keywords if item]

        payload: dict[str, object] = {
            "id": self.id_var.get().strip(),
            "type": self.type_var.get().strip(),
            "anchor": anchor,
            "content": self.content_text.get("1.0", "end-1c").strip(),
            "status": self.status_var.get().strip(),
            "keywords": keywords,
        }
        resp = self.resp_var.get().strip()
        if resp:
            payload["resp"] = resp
        self.result = payload
        self.destroy()


def open_annotation_dialog(
    parent: tk.Misc, initial: dict[str, object] | None = None, *, id_readonly: bool = False
) -> dict[str, object] | None:
    dialog = AnnotationDialog(parent, initial=initial, id_readonly=id_readonly)
    parent.wait_window(dialog)
    return dialog.result
