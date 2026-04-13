from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from ets.application import (
    AppDiagnostic,
    export_html,
    export_tei,
    generate_html_preview_from_tei,
    generate_tei_from_text,
    load_config,
    validate_text,
)
from ets.domain import EditionConfig

from .control_bar import ControlBar
from .diagnostics_panel import DiagnosticsPanel
from .dialogs import SearchReplaceDialog, show_about_dialog, show_help_dialog
from .editor import TextEditor
from .helpers import diagnostic_line_numbers, format_config_status
from .menus import MenuCallbacks, install_menus
from .output_notebook import OutputNotebook


@dataclass
class UIState:
    current_file_path: Path | None = None
    config_path: Path | None = None
    config: EditionConfig | None = None
    tei_xml: str | None = None
    html_preview: str | None = None
    diagnostics: list[AppDiagnostic] = field(default_factory=list)
    outputs_stale: bool = False


class MainWindow(ttk.Frame):
    """Main Tkinter application window for local text workflows."""

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=6)
        self.master = master
        self.state = UIState()
        self._diagnostics_visible = True

        self.master.title("Ekdosis TEI Studio v2")
        self.master.geometry("1200x850")
        self.master.minsize(900, 650)

        self.grid(sticky="nsew")
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=3)
        self.rowconfigure(2, weight=2)

        self.editor = TextEditor(self)
        self.editor.grid(row=0, column=0, sticky="nsew")

        self.control = ControlBar(
            self,
            on_reference_change=self._on_reference_changed,
            on_validate=self.action_validate,
            on_generate_tei=self.action_generate_tei,
            on_preview_html=self.action_preview_html,
            on_export_tei=self.action_export_tei,
            on_export_html=self.action_export_html,
        )
        self.control.grid(row=1, column=0, sticky="ew")

        self.bottom = ttk.Frame(self)
        self.bottom.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
        self.bottom.columnconfigure(0, weight=1)
        self.bottom.rowconfigure(0, weight=1)

        self.outputs = OutputNotebook(self.bottom)
        self.outputs.grid(row=0, column=0, sticky="nsew")

        self.diagnostics = DiagnosticsPanel(self.bottom, on_navigate=self.editor.go_to_line)
        self.diagnostics.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

        self.editor.text.bind("<KeyRelease>", self._on_editor_content_changed, add="+")
        self.editor.text.bind("<<Paste>>", self._on_editor_content_changed, add="+")
        self.editor.text.bind("<<Cut>>", self._on_editor_content_changed, add="+")
        self.editor.text.bind("<Delete>", self._on_editor_content_changed, add="+")

        self._refresh_config_ui()
        self._install_menus()

    def _install_menus(self) -> None:
        install_menus(
            self.master,
            MenuCallbacks(
                new_file=self.action_new_file,
                open_file=self.action_open_file,
                save_file=self.action_save_file,
                save_file_as=self.action_save_file_as,
                load_config=self.action_load_config,
                quit_app=self.action_quit,
                undo=lambda: self.editor.text.event_generate("<<Undo>>"),
                redo=lambda: self.editor.text.event_generate("<<Redo>>"),
                cut=lambda: self.editor.text.event_generate("<<Cut>>"),
                copy=lambda: self.editor.text.event_generate("<<Copy>>"),
                paste=lambda: self.editor.text.event_generate("<<Paste>>"),
                select_all=self.action_select_all,
                find=self.action_find,
                replace=self.action_replace,
                validate=self.action_validate,
                generate_tei=self.action_generate_tei,
                preview_html=self.action_preview_html,
                export_tei=self.action_export_tei,
                export_html=self.action_export_html,
                toggle_diagnostics=self.action_toggle_diagnostics,
                show_about=lambda: show_about_dialog(self.master),
                show_help=lambda: show_help_dialog(self.master),
            ),
        )

    def _refresh_config_ui(self) -> None:
        self.control.set_config_status(
            format_config_status(
                self.state.config,
                str(self.state.config_path) if self.state.config_path is not None else None,
            )
        )
        if self.state.config is None:
            self.control.set_reference_choices([], -1)
            return
        self.control.set_reference_choices(
            [w.siglum for w in self.state.config.witnesses],
            self.state.config.reference_witness,
        )

    def _ensure_config(self) -> bool:
        if self.state.config is not None:
            return True
        messagebox.showerror("Configuration manquante", "Veuillez charger une configuration JSON.", parent=self.master)
        return False

    def _set_diagnostics(self, diagnostics: list[AppDiagnostic]) -> None:
        self.state.diagnostics = diagnostics
        self.diagnostics.set_diagnostics(diagnostics)
        self.editor.highlight_lines(diagnostic_line_numbers(diagnostics))

    def _current_text(self) -> str:
        return self.editor.get_text()

    def _write_current_file(self, target: Path) -> None:
        target.write_text(self._current_text(), encoding="utf-8")
        self.state.current_file_path = target
        self.master.title(f"Ekdosis TEI Studio v2 - {target.name}")

    def _on_editor_content_changed(self, _event: tk.Event[tk.Misc]) -> None:
        self.after_idle(lambda: self._invalidate_outputs(reason="text_changed"))

    def _invalidate_outputs(self, *, reason: str) -> None:
        if self.state.tei_xml is None and self.state.html_preview is None and not self.state.diagnostics:
            return
        self.state.tei_xml = None
        self.state.html_preview = None
        self.state.outputs_stale = True
        self.outputs.set_tei("")
        self.outputs.set_html("")
        if reason in {"text_changed", "new_file", "open_file", "config_changed", "reference_changed"}:
            self._set_diagnostics([])

    def _apply_tei_generation(self, *, show_error: bool = True) -> bool:
        if not self._ensure_config():
            return False
        assert self.state.config is not None
        result = generate_tei_from_text(self._current_text(), self.state.config)
        self._set_diagnostics(result.diagnostics)
        if not result.ok or result.tei_xml is None:
            self.state.tei_xml = None
            self.state.html_preview = None
            self.state.outputs_stale = True
            self.outputs.set_tei("")
            self.outputs.set_html("")
            if show_error:
                messagebox.showerror("Génération TEI", result.message or "Échec de génération TEI.", parent=self.master)
            return False

        self.state.tei_xml = result.tei_xml
        self.outputs.set_tei(result.tei_xml)
        self.state.html_preview = None
        self.outputs.set_html("")
        self.state.outputs_stale = False
        return True

    def _export_content(
        self,
        *,
        title: str,
        warning_message: str,
        default_extension: str,
        filetypes: list[tuple[str, str]],
        content: str | None,
        exporter: Callable[[str, str | Path], Path],
    ) -> None:
        if not content:
            messagebox.showwarning(title, warning_message, parent=self.master)
            return
        chosen = filedialog.asksaveasfilename(
            parent=self.master,
            title=title,
            defaultextension=default_extension,
            filetypes=filetypes,
        )
        if not chosen:
            return
        try:
            target = exporter(content, chosen)
        except OSError as exc:
            messagebox.showerror(title, str(exc), parent=self.master)
            return
        messagebox.showinfo(title, f"Fichier exporté:\n{target}", parent=self.master)

    def action_new_file(self) -> None:
        self.editor.clear()
        self._invalidate_outputs(reason="new_file")
        self.state.current_file_path = None
        self.master.title("Ekdosis TEI Studio v2")

    def action_open_file(self) -> None:
        chosen = filedialog.askopenfilename(
            parent=self.master,
            title="Ouvrir un fichier de transcription",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not chosen:
            return
        path = Path(chosen)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Erreur d'ouverture", str(exc), parent=self.master)
            return
        self.editor.set_text(text)
        self._invalidate_outputs(reason="open_file")
        self.state.current_file_path = path
        self.master.title(f"Ekdosis TEI Studio v2 - {path.name}")

    def action_save_file(self) -> None:
        if self.state.current_file_path is None:
            self.action_save_file_as()
            return
        try:
            self._write_current_file(self.state.current_file_path)
        except OSError as exc:
            messagebox.showerror("Erreur d'enregistrement", str(exc), parent=self.master)

    def action_save_file_as(self) -> None:
        chosen = filedialog.asksaveasfilename(
            parent=self.master,
            title="Enregistrer la transcription",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not chosen:
            return
        try:
            self._write_current_file(Path(chosen))
        except OSError as exc:
            messagebox.showerror("Erreur d'enregistrement", str(exc), parent=self.master)

    def action_load_config(self) -> None:
        chosen = filedialog.askopenfilename(
            parent=self.master,
            title="Charger une configuration JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not chosen:
            return
        try:
            config = load_config(chosen)
        except ValueError as exc:
            messagebox.showerror("Configuration invalide", str(exc), parent=self.master)
            return
        self.state.config_path = Path(chosen)
        self.state.config = config
        self._invalidate_outputs(reason="config_changed")
        self._refresh_config_ui()
        messagebox.showinfo("Configuration chargée", "Configuration chargée avec succès.", parent=self.master)

    def _on_reference_changed(self) -> None:
        if self.state.config is None:
            return
        selected = self.control.selected_reference()
        sigla = [w.siglum for w in self.state.config.witnesses]
        if selected not in sigla:
            return
        self.state.config = replace(self.state.config, reference_witness=sigla.index(selected))
        self._invalidate_outputs(reason="reference_changed")
        self._refresh_config_ui()

    def action_validate(self) -> None:
        if not self._ensure_config():
            return
        assert self.state.config is not None
        result = validate_text(self._current_text(), self.state.config)
        self._set_diagnostics(result.diagnostics)
        if result.ok:
            messagebox.showinfo("Validation", result.message or "Validation réussie.", parent=self.master)
        else:
            messagebox.showwarning("Validation", result.message or "Des erreurs ont été détectées.", parent=self.master)

    def action_generate_tei(self) -> None:
        self._apply_tei_generation(show_error=True)

    def action_preview_html(self) -> None:
        if not self._apply_tei_generation(show_error=False):
            messagebox.showerror("Aperçu HTML", "Échec de génération TEI.", parent=self.master)
            return
        if self.state.tei_xml is None:
            return

        html_result = generate_html_preview_from_tei(self.state.tei_xml)
        if not html_result.ok or html_result.html is None:
            if html_result.diagnostics:
                self._set_diagnostics(html_result.diagnostics)
            self.state.html_preview = None
            self.outputs.set_html("")
            self.state.outputs_stale = True
            messagebox.showerror("Aperçu HTML", html_result.message or "Échec de génération HTML.", parent=self.master)
            return

        self.state.html_preview = html_result.html
        self.outputs.set_html(html_result.html)
        self.state.outputs_stale = False

    def action_export_tei(self) -> None:
        self._export_content(
            title="Exporter le TEI",
            warning_message="Générez d'abord un TEI.",
            default_extension=".xml",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
            content=self.state.tei_xml,
            exporter=export_tei,
        )

    def action_export_html(self) -> None:
        self._export_content(
            title="Exporter le HTML",
            warning_message="Générez d'abord un aperçu HTML.",
            default_extension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            content=self.state.html_preview,
            exporter=export_html,
        )

    def action_select_all(self) -> None:
        self.editor.text.tag_add("sel", "1.0", "end-1c")
        self.editor.text.mark_set("insert", "1.0")
        self.editor.text.see("insert")

    def _search_next(self, needle: str) -> bool:
        text = self.editor.text
        start = text.index("insert +1c")
        idx = text.search(needle, start, stopindex="end")
        if not idx:
            idx = text.search(needle, "1.0", stopindex=start)
        if not idx:
            return False
        end = f"{idx}+{len(needle)}c"
        text.tag_remove("sel", "1.0", "end")
        text.tag_add("sel", idx, end)
        text.mark_set("insert", end)
        text.see(idx)
        text.focus_set()
        return True

    def _replace_one(self, needle: str, replacement: str) -> bool:
        text = self.editor.text
        ranges = text.tag_ranges("sel")
        if len(ranges) == 2 and text.get(ranges[0], ranges[1]) == needle:
            text.delete(ranges[0], ranges[1])
            text.insert(ranges[0], replacement)
            return True
        if not self._search_next(needle):
            return False
        return self._replace_one(needle, replacement)

    def _replace_all(self, needle: str, replacement: str) -> int:
        text = self.editor.text
        count = 0
        start = "1.0"
        while True:
            idx = text.search(needle, start, stopindex="end")
            if not idx:
                break
            end = f"{idx}+{len(needle)}c"
            text.delete(idx, end)
            text.insert(idx, replacement)
            start = f"{idx}+{len(replacement)}c"
            count += 1
        return count

    def action_find(self) -> None:
        SearchReplaceDialog(
            self.master,
            on_find_next=self._search_next,
            on_replace=self._replace_one,
            on_replace_all=self._replace_all,
        )

    def action_replace(self) -> None:
        self.action_find()

    def action_toggle_diagnostics(self) -> None:
        self._diagnostics_visible = not self._diagnostics_visible
        if self._diagnostics_visible:
            self.diagnostics.grid()
        else:
            self.diagnostics.grid_remove()

    def action_quit(self) -> None:
        self.master.destroy()
