from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ets.application import DramaticTeiMergeRequest


@dataclass
class _MergeVars:
    output_path: tk.StringVar


class DramaticMergeDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.title("Fusion XML dramatiques")
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.resizable(True, True)
        self.geometry("840x420")
        self.minsize(700, 360)
        self.result: DramaticTeiMergeRequest | None = None

        self.vars = _MergeVars(output_path=tk.StringVar(value=""))
        self._act_paths: list[Path] = []

        body = ttk.Frame(self, padding=10)
        body.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        ttk.Label(
            body,
            text="Selectionnez les XML d'acte, puis confirmez explicitement l'ordre de fusion.",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        list_frame = ttk.Frame(body)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.acts_list = tk.Listbox(list_frame, selectmode=tk.SINGLE, height=10, exportselection=False)
        self.acts_list.grid(row=0, column=0, sticky="nsew")

        list_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.acts_list.yview)
        list_scroll.grid(row=0, column=1, sticky="ns")
        self.acts_list.configure(yscrollcommand=list_scroll.set)

        controls = ttk.Frame(body)
        controls.grid(row=1, column=1, sticky="ns", padx=(8, 0))
        ttk.Button(controls, text="Ajouter XML…", command=self._add_files).grid(row=0, column=0, pady=(0, 4), sticky="ew")
        ttk.Button(controls, text="Retirer", command=self._remove_selected).grid(row=1, column=0, pady=(0, 16), sticky="ew")
        ttk.Button(controls, text="Monter", command=self._move_up).grid(row=2, column=0, pady=(0, 4), sticky="ew")
        ttk.Button(controls, text="Descendre", command=self._move_down).grid(row=3, column=0, sticky="ew")

        output = ttk.LabelFrame(body, text="Fichier XML de sortie")
        output.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        output.columnconfigure(0, weight=1)
        ttk.Entry(output, textvariable=self.vars.output_path).grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=6)
        ttk.Button(output, text="Choisir…", command=self._choose_output).grid(row=0, column=1, pady=6)

        buttons = ttk.Frame(body)
        buttons.grid(row=3, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(buttons, text="Annuler", command=self._on_cancel).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(buttons, text="Fusionner", command=self._on_validate).grid(row=0, column=1)

    def _sync_list(self) -> None:
        self.acts_list.delete(0, tk.END)
        for item in self._act_paths:
            self.acts_list.insert(tk.END, str(item))

    def _add_files(self) -> None:
        chosen = filedialog.askopenfilenames(
            parent=self,
            title="Selectionner les XML dramatiques a fusionner",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if not chosen:
            return
        for item in chosen:
            path = Path(item).resolve()
            if path in self._act_paths:
                continue
            self._act_paths.append(path)
        self._sync_list()

    def _remove_selected(self) -> None:
        selection = self.acts_list.curselection()
        if not selection:
            return
        index = selection[0]
        del self._act_paths[index]
        self._sync_list()
        if self._act_paths:
            self.acts_list.selection_set(max(0, index - 1))

    def _move_up(self) -> None:
        selection = self.acts_list.curselection()
        if not selection:
            return
        index = selection[0]
        if index <= 0:
            return
        self._act_paths[index - 1], self._act_paths[index] = self._act_paths[index], self._act_paths[index - 1]
        self._sync_list()
        self.acts_list.selection_set(index - 1)

    def _move_down(self) -> None:
        selection = self.acts_list.curselection()
        if not selection:
            return
        index = selection[0]
        if index >= len(self._act_paths) - 1:
            return
        self._act_paths[index + 1], self._act_paths[index] = self._act_paths[index], self._act_paths[index + 1]
        self._sync_list()
        self.acts_list.selection_set(index + 1)

    def _choose_output(self) -> None:
        chosen = filedialog.asksaveasfilename(
            parent=self,
            title="Enregistrer le XML dramatique fusionne",
            defaultextension=".xml",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
            initialfile="piece_fusionnee.xml",
        )
        if chosen:
            self.vars.output_path.set(chosen)

    def _on_validate(self) -> None:
        if len(self._act_paths) < 2:
            messagebox.showerror("Fusion XML dramatiques", "Selectionnez au moins deux fichiers XML d'acte.", parent=self)
            return
        output_raw = self.vars.output_path.get().strip()
        if not output_raw:
            messagebox.showerror("Fusion XML dramatiques", "Le fichier de sortie est requis.", parent=self)
            return

        self.result = DramaticTeiMergeRequest(
            act_xml_paths=tuple(self._act_paths),
            output_path=Path(output_raw).resolve(),
        )
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()


def open_dramatic_merge_dialog(parent: tk.Misc) -> DramaticTeiMergeRequest | None:
    dialog = DramaticMergeDialog(parent)
    parent.wait_window(dialog)
    return dialog.result
