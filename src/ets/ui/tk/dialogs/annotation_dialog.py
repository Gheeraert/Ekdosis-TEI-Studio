from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk


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

        row, self.type_combo = self._add_combo(
            frame,
            row,
            "Type",
            self.type_var,
            ["explicative", "lexicale", "intertextuelle", "dramaturgique", "textuelle", "bibliographique"],
        )
        row, self.kind_combo = self._add_combo(frame, row, "Ancre", self.kind_var, ["line", "line_range", "stage"])
        row, self.act_entry = self._add_entry(frame, row, "Acte", self.act_var)
        row, self.scene_entry = self._add_entry(frame, row, "Scene", self.scene_var)
        row, self.line_entry = self._add_entry(frame, row, "Ligne", self.line_var)
        row, self.start_line_entry = self._add_entry(frame, row, "Ligne debut", self.start_line_var)
        row, self.end_line_entry = self._add_entry(frame, row, "Ligne fin", self.end_line_var)
        row, self.stage_index_entry = self._add_entry(frame, row, "Index didascalie", self.stage_index_var)

        ttk.Label(frame, text="Contenu").grid(row=row, column=0, sticky="nw", padx=(0, 6), pady=2)
        self.content_text = tk.Text(frame, height=5, wrap="word")
        self.content_text.grid(row=row, column=1, sticky="nsew", pady=2)
        self.content_text.insert("1.0", str(self._initial.get("content", "")))
        row += 1

        row, self.resp_entry = self._add_entry(frame, row, "Resp", self.resp_var)
        row, self.status_combo = self._add_combo(frame, row, "Statut", self.status_var, ["draft", "reviewed", "validated"])
        row, self.keywords_entry = self._add_entry(frame, row, "Mots-cles (,)", self.keywords_var)

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
    def _add_entry(frame: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> tuple[int, ttk.Entry]:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=(0, 6), pady=2)
        entry = ttk.Entry(frame, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", pady=2)
        return row + 1, entry

    @staticmethod
    def _add_combo(
        frame: ttk.Frame, row: int, label: str, variable: tk.StringVar, values: list[str]
    ) -> tuple[int, ttk.Combobox]:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=(0, 6), pady=2)
        combo = ttk.Combobox(frame, textvariable=variable, state="readonly", values=values)
        combo.grid(row=row, column=1, sticky="ew", pady=2)
        return row + 1, combo

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

    @staticmethod
    def _validate_form_values(
        *,
        annotation_id: str,
        ann_type: str,
        kind: str,
        act: str,
        scene: str,
        line: str,
        start_line: str,
        end_line: str,
        stage_index: str,
        content: str,
        status: str,
    ) -> tuple[bool, str | None, str | None]:
        if not annotation_id.strip():
            return False, "L'identifiant de note est requis.", "id"
        if not ann_type.strip():
            return False, "Le type d'annotation est requis.", "type"
        if not act.strip():
            return False, "Le numero d'acte est requis.", "act"
        if not scene.strip():
            return False, "Le numero de scene est requis.", "scene"
        if not content.strip():
            return False, "Le contenu de la note est requis.", "content"
        if not status.strip():
            return False, "Le statut est requis.", "status"

        if kind == "line":
            if not line.strip():
                return False, "Le numero de ligne est requis pour une ancre de type 'line'.", "line"
        elif kind == "line_range":
            if not start_line.strip():
                return False, "La ligne de debut est requise pour une ancre de type 'line_range'.", "start_line"
            if not end_line.strip():
                return False, "La ligne de fin est requise pour une ancre de type 'line_range'.", "end_line"
            if start_line.strip().isdigit() and end_line.strip().isdigit():
                if int(start_line.strip()) > int(end_line.strip()):
                    return False, "La ligne de debut doit etre inferieure ou egale a la ligne de fin.", "start_line"
        elif kind == "stage":
            if not stage_index.strip():
                return False, "L'index de didascalie est requis pour une ancre de type 'stage'.", "stage_index"
            if not stage_index.strip().isdigit() or int(stage_index.strip()) <= 0:
                return False, "L'index de didascalie doit etre un entier positif.", "stage_index"
        return True, None, None

    def _validate_form(self) -> tuple[bool, str | None, tk.Widget | None]:
        ok, message, field = self._validate_form_values(
            annotation_id=self.id_var.get(),
            ann_type=self.type_var.get(),
            kind=self.kind_var.get(),
            act=self.act_var.get(),
            scene=self.scene_var.get(),
            line=self.line_var.get(),
            start_line=self.start_line_var.get(),
            end_line=self.end_line_var.get(),
            stage_index=self.stage_index_var.get(),
            content=self.content_text.get("1.0", "end-1c"),
            status=self.status_var.get(),
        )
        if ok:
            return True, None, None
        widget_map: dict[str, tk.Widget] = {
            "id": self.id_entry,
            "type": self.type_combo,
            "act": self.act_entry,
            "scene": self.scene_entry,
            "line": self.line_entry,
            "start_line": self.start_line_entry,
            "end_line": self.end_line_entry,
            "stage_index": self.stage_index_entry,
            "content": self.content_text,
            "status": self.status_combo,
        }
        return False, message, widget_map.get(field)

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()

    def _on_ok(self) -> None:
        valid, error_message, focus_widget = self._validate_form()
        if not valid:
            messagebox.showerror("Annotation", error_message or "Formulaire invalide.", parent=self)
            if focus_widget is not None:
                focus_widget.focus_set()
            return

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
