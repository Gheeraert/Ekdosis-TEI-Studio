from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import messagebox, ttk

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


def _parse_witnesses(raw: str) -> list[Witness]:
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    witnesses: list[Witness] = []
    for line in lines:
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 3:
            raise ValueError(f"Ligne témoin invalide: {line}")
        witnesses.append(Witness(siglum=parts[0], year=parts[1], description="|".join(parts[2:]).strip()))
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


class ConfigDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, initial: EditionConfig | None) -> None:
        super().__init__(parent)
        self.title("Configuration")
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)
        self.result: EditionConfig | None = None

        author_first, author_last = _split_name(initial.author if initial else "")
        editor_first, editor_last = _split_name(initial.editor if initial else "")
        self.vars = _ConfigVars(
            author_first=tk.StringVar(value=author_first),
            author_last=tk.StringVar(value=author_last),
            title=tk.StringVar(value=initial.title if initial else ""),
            editor_first=tk.StringVar(value=editor_first),
            editor_last=tk.StringVar(value=editor_last),
        )
        self._reference_witness = initial.reference_witness if initial else 0

        body = ttk.Frame(self, padding=10)
        body.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(5, weight=1)

        self._add_entry(body, 0, "Prénom de l'auteur", self.vars.author_first)
        self._add_entry(body, 1, "Nom de l'auteur", self.vars.author_last)
        self._add_entry(body, 2, "Titre de la pièce", self.vars.title)
        self._add_entry(body, 3, "Prénom de l'éditeur", self.vars.editor_first)
        self._add_entry(body, 4, "Nom de l'éditeur (vous)", self.vars.editor_last)

        ttk.Label(body, text="Témoins (abbr|year|desc, un par ligne)").grid(row=5, column=0, sticky="nw", padx=(0, 8))
        self.witnesses = tk.Text(body, height=8, width=60, font=("Consolas", 10))
        self.witnesses.grid(row=5, column=1, sticky="nsew")
        self.witnesses.insert("1.0", _witnesses_to_lines(initial.witnesses if initial else []))

        buttons = ttk.Frame(body)
        buttons.grid(row=6, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(buttons, text="Annuler", command=self.destroy).grid(row=0, column=0, padx=4)
        ttk.Button(buttons, text="Valider", command=self._on_validate).grid(row=0, column=1, padx=4)

    @staticmethod
    def _add_entry(parent: ttk.Frame, row: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", pady=2)

    def _on_validate(self) -> None:
        try:
            witnesses = _parse_witnesses(self.witnesses.get("1.0", "end-1c"))
            reference = min(self._reference_witness, len(witnesses) - 1)
            self.result = EditionConfig(
                title=self.vars.title.get().strip(),
                author=f"{self.vars.author_first.get().strip()} {self.vars.author_last.get().strip()}".strip(),
                editor=f"{self.vars.editor_first.get().strip()} {self.vars.editor_last.get().strip()}".strip(),
                witnesses=witnesses,
                reference_witness=reference,
            )
        except ValueError as exc:
            messagebox.showerror("Configuration invalide", str(exc), parent=self)
            return
        self.destroy()


def open_config_dialog(parent: tk.Misc, initial: EditionConfig | None) -> EditionConfig | None:
    dialog = ConfigDialog(parent, initial)
    parent.wait_window(dialog)
    return dialog.result
