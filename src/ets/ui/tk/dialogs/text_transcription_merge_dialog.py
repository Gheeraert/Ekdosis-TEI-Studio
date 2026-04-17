from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ets.application import TextTranscriptionMergeRequest


SEPARATOR_NONE = "Aucun separateur"
SEPARATOR_ONE_BLANK_LINE = "Une ligne vide"
SEPARATOR_TWO_BLANK_LINES = "Deux lignes vides"
SEPARATOR_CUSTOM = "Separateur personnalise"


@dataclass
class _MergeVars:
    output_path: tk.StringVar
    separator_mode: tk.StringVar
    custom_separator: tk.StringVar


class TextTranscriptionMergeDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.title("Fusion transcriptions texte")
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.resizable(True, True)
        self.geometry("860x480")
        self.minsize(720, 380)
        self.result: TextTranscriptionMergeRequest | None = None

        self.vars = _MergeVars(
            output_path=tk.StringVar(value=""),
            separator_mode=tk.StringVar(value=SEPARATOR_NONE),
            custom_separator=tk.StringVar(value=""),
        )
        self._input_paths: list[Path] = []

        body = ttk.Frame(self, padding=10)
        body.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        ttk.Label(
            body,
            text="Selectionnez des transcriptions texte puis fixez explicitement l'ordre.",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        list_frame = ttk.Frame(body)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.files_list = tk.Listbox(list_frame, selectmode=tk.SINGLE, height=12, exportselection=False)
        self.files_list.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.files_list.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.files_list.configure(yscrollcommand=scroll.set)

        controls = ttk.Frame(body)
        controls.grid(row=1, column=1, sticky="ns", padx=(8, 0))
        ttk.Button(controls, text="Ajouter textes...", command=self._add_files).grid(row=0, column=0, pady=(0, 4), sticky="ew")
        ttk.Button(controls, text="Retirer", command=self._remove_selected).grid(row=1, column=0, pady=(0, 16), sticky="ew")
        ttk.Button(controls, text="Monter", command=self._move_up).grid(row=2, column=0, pady=(0, 4), sticky="ew")
        ttk.Button(controls, text="Descendre", command=self._move_down).grid(row=3, column=0, sticky="ew")

        separator_frame = ttk.LabelFrame(body, text="Separateur entre fichiers")
        separator_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        separator_frame.columnconfigure(1, weight=1)
        ttk.Label(separator_frame, text="Mode").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=6)
        self.separator_combo = ttk.Combobox(
            separator_frame,
            textvariable=self.vars.separator_mode,
            values=[
                SEPARATOR_NONE,
                SEPARATOR_ONE_BLANK_LINE,
                SEPARATOR_TWO_BLANK_LINES,
                SEPARATOR_CUSTOM,
            ],
            state="readonly",
        )
        self.separator_combo.grid(row=0, column=1, sticky="ew", pady=6)
        self.separator_combo.bind("<<ComboboxSelected>>", self._on_separator_mode_changed, add="+")

        ttk.Label(separator_frame, text="Texte personnalise").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=(0, 6))
        self.custom_separator_entry = ttk.Entry(separator_frame, textvariable=self.vars.custom_separator, state="disabled")
        self.custom_separator_entry.grid(row=1, column=1, sticky="ew", pady=(0, 6))

        output_frame = ttk.LabelFrame(body, text="Fichier texte de sortie")
        output_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        output_frame.columnconfigure(0, weight=1)
        ttk.Entry(output_frame, textvariable=self.vars.output_path).grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=6)
        ttk.Button(output_frame, text="Choisir...", command=self._choose_output).grid(row=0, column=1, pady=6)

        buttons = ttk.Frame(body)
        buttons.grid(row=4, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(buttons, text="Annuler", command=self._on_cancel).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(buttons, text="Fusionner", command=self._on_validate).grid(row=0, column=1)

    def _on_separator_mode_changed(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        is_custom = self.vars.separator_mode.get() == SEPARATOR_CUSTOM
        self.custom_separator_entry.configure(state="normal" if is_custom else "disabled")

    def _sync_list(self) -> None:
        self.files_list.delete(0, tk.END)
        for path in self._input_paths:
            self.files_list.insert(tk.END, str(path))

    def _add_files(self) -> None:
        chosen = filedialog.askopenfilenames(
            parent=self,
            title="Selectionner les transcriptions a fusionner",
            filetypes=[
                ("Text files", "*.txt"),
                ("Markdown files", "*.md"),
                ("All files", "*.*"),
            ],
        )
        if not chosen:
            return
        for item in chosen:
            path = Path(item).resolve()
            if path in self._input_paths:
                continue
            self._input_paths.append(path)
        self._sync_list()

    def _remove_selected(self) -> None:
        selection = self.files_list.curselection()
        if not selection:
            return
        index = selection[0]
        del self._input_paths[index]
        self._sync_list()
        if self._input_paths:
            self.files_list.selection_set(max(0, index - 1))

    def _move_up(self) -> None:
        selection = self.files_list.curselection()
        if not selection:
            return
        index = selection[0]
        if index <= 0:
            return
        self._input_paths[index - 1], self._input_paths[index] = self._input_paths[index], self._input_paths[index - 1]
        self._sync_list()
        self.files_list.selection_set(index - 1)

    def _move_down(self) -> None:
        selection = self.files_list.curselection()
        if not selection:
            return
        index = selection[0]
        if index >= len(self._input_paths) - 1:
            return
        self._input_paths[index + 1], self._input_paths[index] = self._input_paths[index], self._input_paths[index + 1]
        self._sync_list()
        self.files_list.selection_set(index + 1)

    def _choose_output(self) -> None:
        chosen = filedialog.asksaveasfilename(
            parent=self,
            title="Enregistrer la transcription fusionnee",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Markdown files", "*.md"),
                ("All files", "*.*"),
            ],
            initialfile="transcription_fusionnee.txt",
        )
        if chosen:
            self.vars.output_path.set(chosen)

    def _selected_separator(self) -> str:
        mode = self.vars.separator_mode.get()
        if mode == SEPARATOR_ONE_BLANK_LINE:
            return "\n\n"
        if mode == SEPARATOR_TWO_BLANK_LINES:
            return "\n\n\n"
        if mode == SEPARATOR_CUSTOM:
            return self.vars.custom_separator.get()
        return ""

    def _on_validate(self) -> None:
        if len(self._input_paths) < 2:
            messagebox.showerror(
                "Fusion transcriptions texte",
                "Selectionnez au moins deux fichiers texte.",
                parent=self,
            )
            return
        output_raw = self.vars.output_path.get().strip()
        if not output_raw:
            messagebox.showerror("Fusion transcriptions texte", "Le fichier de sortie est requis.", parent=self)
            return

        self.result = TextTranscriptionMergeRequest(
            input_paths=tuple(self._input_paths),
            output_path=Path(output_raw).resolve(),
            separator=self._selected_separator(),
        )
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()


def open_text_transcription_merge_dialog(parent: tk.Misc) -> TextTranscriptionMergeRequest | None:
    dialog = TextTranscriptionMergeDialog(parent)
    parent.wait_window(dialog)
    return dialog.result
