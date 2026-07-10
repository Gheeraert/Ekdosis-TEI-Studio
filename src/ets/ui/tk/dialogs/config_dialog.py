from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ets.domain import EditionConfig, Witness


def _split_name(value: str) -> tuple[str, str]:
    parts = value.strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _witnesses_to_lines(witnesses: list[Witness]) -> str:
    return "\n".join(f"{w.siglum}|{w.year}|{w.description}" for w in witnesses)


def _parse_witnesses(raw: str, existing: list[Witness] | None = None) -> list[Witness]:
    existing_by_siglum = {witness.siglum: witness for witness in existing or []}
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    witnesses: list[Witness] = []
    for line in lines:
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 3:
            raise ValueError(f"Ligne témoin invalide: {line}")
        siglum = parts[0]
        existing_witness = existing_by_siglum.get(siglum)
        kind = existing_witness.kind if existing_witness else ""
        witnesses.append(
            Witness(
                siglum=siglum,
                year=parts[1],
                description="|".join(parts[2:]).strip(),
                kind=kind,
            )
        )
    if not witnesses:
        raise ValueError("Au moins un témoin est requis.")
    return witnesses


@dataclass
class _ConfigVars:
    author_first: tk.StringVar
    author_last: tk.StringVar
    title: tk.StringVar
    editor_first: tk.StringVar
    editor_last: tk.StringVar
    transcriber_first: tk.StringVar
    transcriber_last: tk.StringVar
    transcription_path: tk.StringVar
    castlist_path: tk.StringVar


class ConfigDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, initial: EditionConfig | None) -> None:
        super().__init__(parent)
        self.title("Configuration")
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)
        self.result: EditionConfig | None = None
        self._initial = initial

        author_first, author_last = _split_name(initial.author if initial else "")
        editor_first, editor_last = _split_name(initial.editor if initial else "")
        transcriber_first, transcriber_last = _split_name(initial.transcriber if initial else "")
        self.vars = _ConfigVars(
            author_first=tk.StringVar(value=author_first),
            author_last=tk.StringVar(value=author_last),
            title=tk.StringVar(value=initial.title if initial else ""),
            editor_first=tk.StringVar(value=editor_first),
            editor_last=tk.StringVar(value=editor_last),
            transcriber_first=tk.StringVar(value=transcriber_first),
            transcriber_last=tk.StringVar(value=transcriber_last),
            transcription_path=tk.StringVar(value=initial.transcription_path if initial else ""),
            castlist_path=tk.StringVar(value=initial.castlist_path if initial else ""),
        )
        self._reference_witness = initial.reference_witness if initial else 0

        body = ttk.Frame(self, padding=10)
        body.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(9, weight=1)

        self._add_entry(body, 0, "Prénom de l'auteur", self.vars.author_first)
        self._add_entry(body, 1, "Nom de l'auteur", self.vars.author_last)
        self._add_entry(body, 2, "Titre de la pièce", self.vars.title)
        self._add_entry(body, 3, "Prénom de l'éditeur scientifique", self.vars.editor_first)
        self._add_entry(body, 4, "Nom de l'éditeur scientifique", self.vars.editor_last)
        self._add_entry(body, 5, "Prénom du transcripteur", self.vars.transcriber_first)
        self._add_entry(body, 6, "Nom du transcripteur", self.vars.transcriber_last)
        self._add_path_entry(body, 7, "Fichier de transcription", self.vars.transcription_path)
        self._add_path_entry(body, 8, "Fichier dramatis personae", self.vars.castlist_path)

        ttk.Label(body, text="Témoins (abbr|year|desc, un par ligne)").grid(row=9, column=0, sticky="nw", padx=(0, 8))
        self.witnesses = tk.Text(body, height=8, width=60, font=("Consolas", 10))
        self.witnesses.grid(row=9, column=1, sticky="nsew")
        self.witnesses.insert("1.0", _witnesses_to_lines(initial.witnesses if initial else []))

        buttons = ttk.Frame(body)
        buttons.grid(row=10, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(buttons, text="Annuler", command=self.destroy).grid(row=0, column=0, padx=4)
        ttk.Button(buttons, text="Valider", command=self._on_validate).grid(row=0, column=1, padx=4)

    @staticmethod
    def _add_entry(parent: ttk.Frame, row: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", pady=2)

    def _add_path_entry(self, parent: ttk.Frame, row: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
        field = ttk.Frame(parent)
        field.grid(row=row, column=1, sticky="ew", pady=2)
        field.columnconfigure(0, weight=1)
        ttk.Entry(field, textvariable=var).grid(row=0, column=0, sticky="ew")
        ttk.Button(field, text="Parcourir...", command=lambda: self._browse_path(var)).grid(
            row=0,
            column=1,
            padx=(6, 0),
        )

    def _browse_path(self, var: tk.StringVar) -> None:
        chosen = filedialog.askopenfilename(
            parent=self,
            title="Choisir un fichier",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if chosen:
            var.set(chosen)

    def _on_validate(self) -> None:
        try:
            witnesses = _parse_witnesses(
                self.witnesses.get("1.0", "end-1c"),
                self._initial.witnesses if self._initial else None,
            )
            reference = min(self._reference_witness, len(witnesses) - 1)
            self.result = EditionConfig(
                title=self.vars.title.get().strip(),
                author=f"{self.vars.author_first.get().strip()} {self.vars.author_last.get().strip()}".strip(),
                editor=f"{self.vars.editor_first.get().strip()} {self.vars.editor_last.get().strip()}".strip(),
                witnesses=witnesses,
                reference_witness=reference,
                transcriber=f"{self.vars.transcriber_first.get().strip()} {self.vars.transcriber_last.get().strip()}".strip(),
                characters=list(self._initial.characters) if self._initial else [],
                transcription_path=self.vars.transcription_path.get().strip(),
                castlist_path=self.vars.castlist_path.get().strip(),
            )
        except ValueError as exc:
            messagebox.showerror("Configuration invalide", str(exc), parent=self)
            return
        self.destroy()


def open_config_dialog(parent: tk.Misc, initial: EditionConfig | None) -> EditionConfig | None:
    dialog = ConfigDialog(parent, initial)
    parent.wait_window(dialog)
    return dialog.result
