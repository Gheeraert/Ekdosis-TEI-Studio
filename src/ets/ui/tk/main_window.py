from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable
import webbrowser

from ets.annotations import Annotation, AnnotationCollection, AnnotationValidationError
from ets.application import (
    AppDiagnostic,
    build_site_from_config_file,
    create_annotation,
    delete_annotation,
    enrich_tei_with_annotations,
    parse_annotation,
    export_html,
    export_tei,
    generate_html_preview_from_tei,
    generate_tei_from_text,
    load_annotations,
    load_config,
    save_annotations,
    save_config,
    suggest_output_basename,
    update_annotation,
    validate_text,
)
from ets.domain import EditionConfig
from ets.infrastructure import AutosavePayload, AutosaveStore, LocalPreviewServer
from ets.parser import parse_play
from ets.validation import validate_tei_xml

from .control_bar import ControlBar
from .diagnostics_panel import DiagnosticsPanel
from .dialogs import SearchReplaceDialog, open_annotation_dialog, open_config_dialog, show_about_dialog, show_help_dialog
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
    tei_dirty_by_user: bool = False
    diagnostics: list[AppDiagnostic] = field(default_factory=list)
    outputs_stale: bool = False
    annotations: AnnotationCollection = field(default_factory=lambda: AnnotationCollection(version=1, annotations=[]))
    annotations_path: Path | None = None


def suggest_next_annotation_id(collection: AnnotationCollection) -> str:
    numeric_suffixes: list[int] = []
    existing = {annotation.id for annotation in collection.annotations}
    for annotation_id in existing:
        if len(annotation_id) >= 2 and annotation_id.startswith("n") and annotation_id[1:].isdigit():
            numeric_suffixes.append(int(annotation_id[1:]))
    candidate = max(numeric_suffixes, default=0) + 1
    while f"n{candidate}" in existing:
        candidate += 1
    return f"n{candidate}"


def _numeric_equivalents(token: str) -> set[str]:
    value = token.strip()
    if not value:
        return set()
    if value.isdigit():
        return {value, str(int(value))}
    roman_map = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    text = value.upper()
    if any(char not in roman_map for char in text):
        return {value}
    total = 0
    prev = 0
    for char in reversed(text):
        current = roman_map[char]
        if current < prev:
            total -= current
        else:
            total += current
            prev = current
    return {value, text, str(total)}


class MainWindow(ttk.Frame):
    """Main Tkinter application window for local text workflows."""

    AUTOSAVE_DELAY_MS = 2000

    def __init__(
        self,
        master: tk.Tk,
        *,
        preview_server: LocalPreviewServer | None = None,
        autosave_store: AutosaveStore | None = None,
        open_browser: Callable[[str], bool] | None = None,
    ) -> None:
        super().__init__(master, padding=6)
        self.master = master
        self.state = UIState()
        self._diagnostics_visible = True
        self._preview_server = preview_server or LocalPreviewServer()
        self._autosave_store = autosave_store or AutosaveStore()
        self._open_browser = open_browser or webbrowser.open_new_tab
        self._autosave_after_id: str | None = None

        self.master.title("Ekdosis TEI Studio v2")
        self.master.geometry("1200x850")
        self.master.minsize(900, 650)

        self.grid(sticky="nsew")
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        self.vertical_pane = ttk.Panedwindow(self, orient=tk.VERTICAL)
        self.vertical_pane.grid(row=0, column=0, sticky="nsew")

        self.top = ttk.Frame(self.vertical_pane)
        self.top.columnconfigure(0, weight=1)
        self.top.rowconfigure(0, weight=1)

        self.editor = TextEditor(self.top)
        self.editor.grid(row=0, column=0, sticky="nsew")

        self.bottom = ttk.Frame(self.vertical_pane)
        self.bottom.columnconfigure(0, weight=1)
        self.bottom.rowconfigure(0, weight=1)

        self.outputs = OutputNotebook(
            self.bottom,
            on_tei_edited=self._on_tei_widget_edited,
            on_annotation_add=self.action_add_annotation,
            on_annotation_edit=self.action_edit_annotation,
            on_annotation_delete=self.action_delete_annotation,
            on_annotation_select=self._on_annotation_selected,
        )
        self.outputs.grid(row=0, column=0, sticky="nsew")
        self.outputs.set_annotations(self.state.annotations)
        self.outputs.set_annotations_file_path(None)

        self.diagnostics = DiagnosticsPanel(self.bottom, on_navigate=self.editor.go_to_line)
        self.diagnostics.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

        self.vertical_pane.add(self.top, weight=3)
        self.vertical_pane.add(self.bottom, weight=2)

        self.control = ControlBar(
            self,
            on_reference_change=self._on_reference_changed,
            on_validate=self.action_validate,
            on_generate_tei=self.action_generate_tei,
            on_preview_html=self.action_preview_html,
            on_export_tei=self.action_export_tei,
            on_export_html=self.action_export_html,
        )
        self.control.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        self.editor.text.bind("<KeyRelease>", self._on_editor_content_changed, add="+")
        self.editor.text.bind("<<Paste>>", self._on_editor_content_changed, add="+")
        self.editor.text.bind("<<Cut>>", self._on_editor_content_changed, add="+")
        self.editor.text.bind("<Delete>", self._on_editor_content_changed, add="+")

        self._refresh_config_ui()
        self._install_menus()
        self._install_shortcuts()

    def _install_menus(self) -> None:
        install_menus(
            self.master,
            MenuCallbacks(
                new_file=self.action_new_file,
                open_file=self.action_open_file,
                save_file=self.action_save_file,
                save_file_as=self.action_save_file_as,
                restore_autosave=self.action_restore_autosave,
                new_config=self.action_new_config,
                edit_config=self.action_edit_config,
                save_config_as=self.action_save_config_as,
                load_config=self.action_load_config,
                load_annotations=self.action_load_annotations,
                save_annotations=self.action_save_annotations,
                quit_app=self.action_quit,
                undo=self.action_undo,
                redo=self.action_redo,
                cut=self.action_cut,
                copy=self.action_copy,
                paste=self.action_paste,
                select_all=self.action_select_all,
                find=self.action_find,
                replace=self.action_replace,
                validate=self.action_validate,
                validate_generated_tei=self.action_validate_generated_tei,
                generate_tei=self.action_generate_tei,
                preview_html=self.action_preview_html,
                export_tei=self.action_export_tei,
                export_html=self.action_export_html,
                build_publication_site=self.action_build_publication_site,
                add_annotation=self.action_add_annotation,
                edit_annotation=self.action_edit_annotation,
                delete_annotation=self.action_delete_annotation,
                toggle_diagnostics=self.action_toggle_diagnostics,
                show_about=lambda: show_about_dialog(self.master),
                show_help=lambda: show_help_dialog(self.master),
            ),
        )

    def _install_shortcuts(self) -> None:
        self.master.bind_all("<Control-f>", self._shortcut_find, add="+")
        self.master.bind_all("<Control-F>", self._shortcut_find, add="+")
        self.master.bind_all("<Control-a>", self._shortcut_select_all, add="+")
        self.master.bind_all("<Control-A>", self._shortcut_select_all, add="+")
        self.master.bind_all("<Control-x>", self._shortcut_cut, add="+")
        self.master.bind_all("<Control-X>", self._shortcut_cut, add="+")
        self.master.bind_all("<Control-c>", self._shortcut_copy, add="+")
        self.master.bind_all("<Control-C>", self._shortcut_copy, add="+")
        self.master.bind_all("<Control-v>", self._shortcut_paste, add="+")
        self.master.bind_all("<Control-V>", self._shortcut_paste, add="+")

    def _active_text_widget(self) -> tk.Text | None:
        focused = self.master.focus_get()
        if isinstance(focused, tk.Text):
            return focused
        return None

    def _shortcut_find(self, _event: tk.Event[tk.Misc]) -> str:
        self.action_find()
        return "break"

    def _shortcut_select_all(self, _event: tk.Event[tk.Misc]) -> str:
        self.action_select_all()
        return "break"

    def _shortcut_cut(self, _event: tk.Event[tk.Misc]) -> str:
        self.action_cut()
        return "break"

    def _shortcut_copy(self, _event: tk.Event[tk.Misc]) -> str:
        self.action_copy()
        return "break"

    def _shortcut_paste(self, _event: tk.Event[tk.Misc]) -> str:
        self.action_paste()
        return "break"

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
        messagebox.showerror("Configuration manquante", "Veuillez charger ou créer une configuration JSON.", parent=self.master)
        return False

    def _set_diagnostics(self, diagnostics: list[AppDiagnostic]) -> None:
        self.state.diagnostics = diagnostics
        self.diagnostics.set_diagnostics(diagnostics)
        self.editor.highlight_lines(diagnostic_line_numbers(diagnostics))

    @staticmethod
    def _format_annotation_error(exc: AnnotationValidationError) -> str:
        lines: list[str] = []
        for item in exc.diagnostics:
            suffix = ""
            if item.annotation_id:
                suffix += f" [id={item.annotation_id}]"
            if item.field:
                suffix += f" [champ={item.field}]"
            lines.append(f"- {item.code}: {item.message}{suffix}")
        return "\n".join(lines) if lines else str(exc)

    def _set_annotations(self, collection: AnnotationCollection, path: Path | None) -> None:
        self.state.annotations = collection
        self.state.annotations_path = path
        self.outputs.set_annotations(collection)
        self.outputs.set_annotations_file_path(str(path) if path is not None else None)
        self._refresh_annotation_highlights()

    @staticmethod
    def _split_parallel_blocks_with_start_lines(text: str, witness_count: int) -> dict[int, int]:
        starts: dict[int, int] = {}
        current_count = 0
        current_start_line = 1
        block_index = 0
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            if raw_line.strip() == "":
                if current_count:
                    if current_count == witness_count:
                        starts[block_index] = current_start_line
                    block_index += 1
                    current_count = 0
                current_start_line = line_number + 1
                continue
            if current_count == 0:
                current_start_line = line_number
            current_count += 1
        if current_count:
            if current_count == witness_count:
                starts[block_index] = current_start_line
        return starts

    def _build_annotation_indices(
        self, text: str
    ) -> tuple[dict[tuple[str, str, str], int], dict[tuple[str, str, int], int], dict[int, int]]:
        assert self.state.config is not None
        play = parse_play(text, self.state.config)
        block_start_lines = self._split_parallel_blocks_with_start_lines(text, len(self.state.config.witnesses))
        verse_index: dict[tuple[str, str, str], int] = {}
        stage_index: dict[tuple[str, str, int], int] = {}

        for act_pos, act in enumerate(play.acts, start=1):
            act_label = self.state.config.act_number if len(play.acts) == 1 else str(act_pos)
            for scene_pos, scene in enumerate(act.scenes, start=1):
                scene_label = self.state.config.scene_number if len(act.scenes) == 1 else str(scene_pos)
                stage_counter = 0
                for stage in scene.stage_directions:
                    stage_counter += 1
                    stage_index[(act_label, scene_label, stage_counter)] = stage.block_index
                for speech in scene.speeches:
                    for element in speech.elements:
                        if hasattr(element, "number") and hasattr(element, "block_index"):
                            verse_index[(act_label, scene_label, element.number)] = element.block_index
                        elif hasattr(element, "lines"):
                            for verse in element.lines:
                                verse_index[(act_label, scene_label, verse.number)] = verse.block_index
                        elif hasattr(element, "block_index"):
                            stage_counter += 1
                            stage_index[(act_label, scene_label, stage_counter)] = element.block_index
        return verse_index, stage_index, block_start_lines

    def resolve_current_editor_position_to_annotation_anchor(self) -> dict[str, object] | None:
        if self.state.config is None:
            return None
        text = self._current_text()
        if not text.strip():
            return None
        try:
            verse_index, stage_index, block_start_lines = self._build_annotation_indices(text)
        except ValueError:
            return None
        if not block_start_lines:
            return None

        cursor_line = self.editor.current_line_number()
        line_count = max(1, len(text.splitlines()))
        sorted_starts = sorted(block_start_lines.items(), key=lambda item: item[1])
        cursor_block: int | None = None
        for position, (block_index, start_line) in enumerate(sorted_starts):
            next_start = sorted_starts[position + 1][1] if position + 1 < len(sorted_starts) else line_count + 1
            if start_line <= cursor_line < next_start:
                cursor_block = block_index
                break
        if cursor_block is None:
            return None

        for (act, scene, line), block_index in verse_index.items():
            if block_index == cursor_block:
                return {"kind": "line", "act": act, "scene": scene, "line": line}
        for (act, scene, stage_number), block_index in stage_index.items():
            if block_index == cursor_block:
                return {"kind": "stage", "act": act, "scene": scene, "stage_index": stage_number}
        return None

    def _annotation_source_line_map(self) -> dict[str, list[int]]:
        if self.state.config is None:
            return {}
        text = self._current_text()
        if not text.strip():
            return {}
        try:
            verse_index, stage_index, block_start_lines = self._build_annotation_indices(text)
        except ValueError:
            return {}

        mapped: dict[str, list[int]] = {}
        for annotation in self.state.annotations.annotations:
            anchor = annotation.anchor
            lines: list[int] = []

            if anchor.kind == "line" and anchor.line is not None:
                for act_value in _numeric_equivalents(anchor.act) or {anchor.act}:
                    for scene_value in _numeric_equivalents(anchor.scene) or {anchor.scene}:
                        key = (act_value, scene_value, anchor.line)
                        block = verse_index.get(key)
                        if block is not None and block in block_start_lines:
                            lines = [block_start_lines[block]]
                            break
                    if lines:
                        break
            elif anchor.kind == "line_range" and anchor.start_line is not None and anchor.end_line is not None:
                if anchor.start_line.isdigit() and anchor.end_line.isdigit():
                    start = int(anchor.start_line)
                    end = int(anchor.end_line)
                    if start <= end:
                        for act_value in _numeric_equivalents(anchor.act) or {anchor.act}:
                            for scene_value in _numeric_equivalents(anchor.scene) or {anchor.scene}:
                                candidates: list[int] = []
                                for (a, s, line_number), block in verse_index.items():
                                    if a != act_value or s != scene_value:
                                        continue
                                    number_text = str(line_number)
                                    base = number_text.split(".", maxsplit=1)[0]
                                    if not base.isdigit():
                                        continue
                                    numeric = int(base)
                                    if start <= numeric <= end and block in block_start_lines:
                                        candidates.append(block_start_lines[block])
                                if candidates:
                                    lines = sorted(set(candidates))
                                    break
                            if lines:
                                break
            elif anchor.kind == "stage" and anchor.stage_index is not None:
                for act_value in _numeric_equivalents(anchor.act) or {anchor.act}:
                    for scene_value in _numeric_equivalents(anchor.scene) or {anchor.scene}:
                        block = stage_index.get((act_value, scene_value, anchor.stage_index))
                        if block is not None and block in block_start_lines:
                            lines = [block_start_lines[block]]
                            break
                    if lines:
                        break

            if lines:
                mapped[annotation.id] = lines
        return mapped

    def _refresh_annotation_highlights(self, focus_annotation_id: str | None = None) -> None:
        mapping = self._annotation_source_line_map()
        all_lines: list[int] = sorted({line for lines in mapping.values() for line in lines})
        focus_line: int | None = None
        if focus_annotation_id is not None:
            focus_lines = mapping.get(focus_annotation_id)
            if focus_lines:
                focus_line = focus_lines[0]
                self.editor.go_to_line(focus_line)
        self.editor.highlight_annotation_lines(all_lines, focus_line=focus_line)

    def _on_annotation_selected(self, annotation_id: str | None) -> None:
        if annotation_id is None:
            self._refresh_annotation_highlights()
            return
        self._refresh_annotation_highlights(focus_annotation_id=annotation_id)

    def _find_annotation(self, annotation_id: str) -> Annotation | None:
        for annotation in self.state.annotations.annotations:
            if annotation.id == annotation_id:
                return annotation
        return None

    @staticmethod
    def _annotation_to_payload(annotation: Annotation) -> dict[str, object]:
        anchor: dict[str, object] = {
            "kind": annotation.anchor.kind,
            "act": annotation.anchor.act,
            "scene": annotation.anchor.scene,
        }
        if annotation.anchor.kind == "line":
            anchor["line"] = annotation.anchor.line or ""
        elif annotation.anchor.kind == "line_range":
            anchor["start_line"] = annotation.anchor.start_line or ""
            anchor["end_line"] = annotation.anchor.end_line or ""
        elif annotation.anchor.kind == "stage":
            anchor["stage_index"] = annotation.anchor.stage_index if annotation.anchor.stage_index is not None else ""
        payload: dict[str, object] = {
            "id": annotation.id,
            "type": annotation.type,
            "anchor": anchor,
            "content": annotation.content,
            "status": annotation.status,
            "keywords": annotation.keywords,
        }
        if annotation.resp:
            payload["resp"] = annotation.resp
        return payload

    def _current_text(self) -> str:
        return self.editor.get_text()

    def _current_tei_text(self) -> str:
        return self.outputs.get_tei()

    def _on_tei_widget_edited(self) -> None:
        current = self._current_tei_text()
        if not current.strip():
            self.state.tei_xml = None
            self.state.tei_dirty_by_user = False
            self.state.outputs_stale = True
            return
        self.state.tei_xml = current
        self.state.tei_dirty_by_user = True
        self.state.outputs_stale = True

    def _suggest_basename(self) -> str:
        if self.state.config is not None:
            try:
                return suggest_output_basename(self._current_text(), self.state.config)
            except Exception:
                pass
        if self.state.current_file_path is not None:
            return self.state.current_file_path.stem
        return "document"

    def _default_filename(self, extension: str, *, suffix: str = "") -> str:
        base = self._suggest_basename()
        return f"{base}{suffix}{extension}"

    def _write_current_file(self, target: Path) -> None:
        target.write_text(self._current_text(), encoding="utf-8")
        self.state.current_file_path = target
        self.master.title(f"Ekdosis TEI Studio v2 - {target.name}")

    def _on_editor_content_changed(self, _event: tk.Event[tk.Misc]) -> None:
        self.after_idle(lambda: self._invalidate_outputs(reason="text_changed"))
        self._schedule_autosave()

    def _schedule_autosave(self) -> None:
        if self._autosave_after_id is not None:
            self.after_cancel(self._autosave_after_id)
        self._autosave_after_id = self.after(self.AUTOSAVE_DELAY_MS, self._perform_autosave)

    def _perform_autosave(self) -> None:
        self._autosave_after_id = None
        payload = AutosavePayload(
            text=self._current_text(),
            current_file_path=str(self.state.current_file_path) if self.state.current_file_path else None,
            config_path=str(self.state.config_path) if self.state.config_path else None,
        )
        try:
            self._autosave_store.save(payload)
        except OSError:
            # Non-blocking by design: autosave failures must not interrupt editing.
            return

    def _invalidate_outputs(self, *, reason: str) -> None:
        if self.state.tei_xml is None and self.state.html_preview is None and not self.state.diagnostics:
            return
        self.state.tei_xml = None
        self.state.html_preview = None
        self.state.tei_dirty_by_user = False
        self.state.outputs_stale = True
        self.outputs.set_tei("")
        self.outputs.set_html("")
        if reason in {"text_changed", "new_file", "open_file", "config_changed", "reference_changed"}:
            self._set_diagnostics([])

    def _maybe_enrich_tei_with_annotations(self, tei_xml: str) -> tuple[str | None, list[AppDiagnostic], str | None]:
        if not self.state.annotations.annotations:
            return tei_xml, [], None
        enrichment = enrich_tei_with_annotations(tei_xml, self.state.annotations)
        if not enrichment.ok or enrichment.tei_xml is None:
            return None, enrichment.diagnostics, enrichment.message or "Échec de l'enrichissement TEI."
        return enrichment.tei_xml, enrichment.diagnostics, None

    def _apply_tei_generation(self, *, show_error: bool = True) -> bool:
        if not self._ensure_config():
            return False
        assert self.state.config is not None
        result = generate_tei_from_text(self._current_text(), self.state.config)
        if not result.ok or result.tei_xml is None:
            self._set_diagnostics(result.diagnostics)
            self.state.tei_xml = None
            self.state.html_preview = None
            self.state.outputs_stale = True
            self.outputs.set_tei("")
            self.outputs.set_html("")
            if show_error:
                messagebox.showerror("Génération TEI", result.message or "Échec de génération TEI.", parent=self.master)
            return False

        enriched_tei, enrichment_diagnostics, enrichment_error = self._maybe_enrich_tei_with_annotations(result.tei_xml)
        if enriched_tei is None:
            self._set_diagnostics(result.diagnostics + enrichment_diagnostics)
            self.state.tei_xml = None
            self.state.html_preview = None
            self.state.outputs_stale = True
            self.outputs.set_tei("")
            self.outputs.set_html("")
            if show_error:
                messagebox.showerror("Génération TEI", enrichment_error or "Échec de l'enrichissement TEI.", parent=self.master)
            return False

        self._set_diagnostics(result.diagnostics + enrichment_diagnostics)
        self.state.tei_xml = enriched_tei
        self.outputs.set_tei(enriched_tei)
        self.state.tei_dirty_by_user = False
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
        initialfile: str,
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
            initialfile=initialfile,
        )
        if not chosen:
            return
        try:
            target = exporter(content, chosen)
        except OSError as exc:
            messagebox.showerror(title, str(exc), parent=self.master)
            return
        messagebox.showinfo(title, f"Fichier exporté:\n{target}", parent=self.master)

    def _set_current_config(self, config: EditionConfig, config_path: Path | None) -> None:
        self.state.config = config
        self.state.config_path = config_path
        self._invalidate_outputs(reason="config_changed")
        self._refresh_config_ui()
        self._schedule_autosave()

    def action_new_file(self) -> None:
        self.editor.clear()
        self._invalidate_outputs(reason="new_file")
        self.state.current_file_path = None
        self.master.title("Ekdosis TEI Studio v2")
        self._schedule_autosave()

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
        self._schedule_autosave()

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
            initialfile=self._default_filename(".txt"),
        )
        if not chosen:
            return
        try:
            self._write_current_file(Path(chosen))
        except OSError as exc:
            messagebox.showerror("Erreur d'enregistrement", str(exc), parent=self.master)
            return
        self._schedule_autosave()

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
        self._set_current_config(config, Path(chosen))
        messagebox.showinfo("Configuration chargée", "Configuration chargée avec succès.", parent=self.master)

    def action_new_config(self) -> None:
        config = open_config_dialog(self.master, None)
        if config is None:
            return
        self._set_current_config(config, None)
        messagebox.showinfo("Configuration", "Nouvelle configuration appliquée en mémoire.", parent=self.master)

    def action_edit_config(self) -> None:
        config = open_config_dialog(self.master, self.state.config)
        if config is None:
            return
        self._set_current_config(config, self.state.config_path)
        messagebox.showinfo("Configuration", "Configuration modifiée en mémoire.", parent=self.master)

    def action_save_config_as(self) -> None:
        if self.state.config is None:
            messagebox.showwarning(
                "Configuration",
                "Aucune configuration à enregistrer. Créez ou chargez une configuration d'abord.",
                parent=self.master,
            )
            return
        chosen = filedialog.asksaveasfilename(
            parent=self.master,
            title="Enregistrer la configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=self._default_filename(".json", suffix="_config"),
        )
        if not chosen:
            return
        try:
            target = save_config(self.state.config, chosen)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Configuration", str(exc), parent=self.master)
            return
        self.state.config_path = target
        self._refresh_config_ui()
        messagebox.showinfo("Configuration", f"Configuration enregistrée:\n{target}", parent=self.master)

    def action_load_annotations(self) -> None:
        chosen = filedialog.askopenfilename(
            parent=self.master,
            title="Charger un fichier d'annotations",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not chosen:
            return
        try:
            collection = load_annotations(chosen)
        except AnnotationValidationError as exc:
            messagebox.showerror("Annotations", self._format_annotation_error(exc), parent=self.master)
            return
        except (OSError, ValueError) as exc:
            messagebox.showerror("Annotations", str(exc), parent=self.master)
            return
        self._set_annotations(collection, Path(chosen))
        messagebox.showinfo("Annotations", "Annotations chargées.", parent=self.master)

    def action_save_annotations(self) -> None:
        initial_path = self.state.annotations_path
        if initial_path is None:
            chosen = filedialog.asksaveasfilename(
                parent=self.master,
                title="Enregistrer les annotations",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=self._default_filename(".json", suffix="_annotations"),
            )
            if not chosen:
                return
            target = Path(chosen)
        else:
            target = initial_path
        try:
            written = save_annotations(self.state.annotations, target)
        except AnnotationValidationError as exc:
            messagebox.showerror("Annotations", self._format_annotation_error(exc), parent=self.master)
            return
        except (OSError, ValueError) as exc:
            messagebox.showerror("Annotations", str(exc), parent=self.master)
            return
        self._set_annotations(self.state.annotations, written)
        messagebox.showinfo("Annotations", f"Annotations enregistrées:\n{written}", parent=self.master)

    def action_add_annotation(self) -> None:
        resolved_anchor = self.resolve_current_editor_position_to_annotation_anchor()
        if resolved_anchor is None:
            messagebox.showinfo(
                "Annotations",
                "La ligne courante ne correspond pas a un vers ni a une didascalie annotable.",
                parent=self.master,
            )
            return
        initial_payload: dict[str, object] = {
            "id": suggest_next_annotation_id(self.state.annotations),
            "anchor": resolved_anchor,
        }
        payload = open_annotation_dialog(self.master, initial=initial_payload, id_readonly=True)
        if payload is None:
            return
        try:
            annotation = parse_annotation(payload)
            collection = create_annotation(self.state.annotations, annotation)
        except AnnotationValidationError as exc:
            messagebox.showerror("Annotations", self._format_annotation_error(exc), parent=self.master)
            return
        self._set_annotations(collection, self.state.annotations_path)

    def action_edit_annotation(self) -> None:
        selected_id = self.outputs.selected_annotation_id()
        if selected_id is None:
            messagebox.showwarning("Annotations", "Sélectionnez une annotation à modifier.", parent=self.master)
            return
        current = self._find_annotation(selected_id)
        if current is None:
            messagebox.showerror("Annotations", "Annotation introuvable dans l'état courant.", parent=self.master)
            return
        payload = open_annotation_dialog(self.master, initial=self._annotation_to_payload(current), id_readonly=True)
        if payload is None:
            return
        try:
            updated = parse_annotation(payload)
            collection = update_annotation(self.state.annotations, updated)
        except AnnotationValidationError as exc:
            messagebox.showerror("Annotations", self._format_annotation_error(exc), parent=self.master)
            return
        self._set_annotations(collection, self.state.annotations_path)

    def action_delete_annotation(self) -> None:
        selected_id = self.outputs.selected_annotation_id()
        if selected_id is None:
            messagebox.showwarning("Annotations", "Sélectionnez une annotation à supprimer.", parent=self.master)
            return
        if not messagebox.askyesno(
            "Annotations",
            f"Supprimer l'annotation {selected_id} ?",
            parent=self.master,
        ):
            return
        try:
            collection = delete_annotation(self.state.annotations, selected_id)
        except AnnotationValidationError as exc:
            messagebox.showerror("Annotations", self._format_annotation_error(exc), parent=self.master)
            return
        self._set_annotations(collection, self.state.annotations_path)

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
        self._schedule_autosave()

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
        if self.state.tei_dirty_by_user:
            confirm = messagebox.askyesno(
                "Génération TEI",
                "La TEI a été modifiée manuellement.\nLa régénération va écraser ces modifications.\nContinuer ?",
                parent=self.master,
            )
            if not confirm:
                return
        self._apply_tei_generation(show_error=True)

    def action_validate_generated_tei(self) -> None:
        current_tei = self._current_tei_text()
        if not current_tei.strip():
            messagebox.showinfo("Validation TEI", "Aucune TEI générée à valider.", parent=self.master)
            return

        self.state.tei_xml = current_tei
        result = validate_tei_xml(current_tei)
        if result.is_valid:
            messagebox.showinfo(
                "Validation TEI",
                f"TEI valide ({result.schema_name}, moteur {result.engine_name}).",
                parent=self.master,
            )
            return

        if result.errors:
            lines = []
            for issue in result.errors[:20]:
                loc = ""
                if issue.line is not None:
                    loc = f" (ligne {issue.line}"
                    if issue.column is not None:
                        loc += f", colonne {issue.column}"
                    loc += ")"
                lines.append(f"- {issue.level}: {issue.message}{loc}")
            details = "\n".join(lines)
        else:
            details = "- ERROR: validation échouée sans détail."
        messagebox.showwarning(
            "Validation TEI",
            f"TEI invalide avec le schéma {result.schema_name}.\n\n{details}",
            parent=self.master,
        )

    def action_preview_html(self) -> None:
        current_tei = self._current_tei_text()
        if current_tei.strip():
            self.state.tei_xml = current_tei
        elif self.state.tei_xml is None:
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
        try:
            preview_url = self._preview_server.publish_html(html_result.html)
            self._open_browser(preview_url)
        except OSError as exc:
            messagebox.showerror("Aperçu HTML", f"Impossible de lancer le serveur local: {exc}", parent=self.master)

    def action_restore_autosave(self) -> None:
        try:
            payload = self._autosave_store.load()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Autosave", f"Impossible de lire l'enregistrement automatique: {exc}", parent=self.master)
            return
        if payload is None:
            messagebox.showinfo("Autosave", "Aucun enregistrement automatique disponible.", parent=self.master)
            return

        current = self._current_text().strip()
        if current:
            confirm = messagebox.askyesno(
                "Autosave",
                "Remplacer le texte courant par le dernier enregistrement automatique ?",
                parent=self.master,
            )
            if not confirm:
                return

        self.editor.set_text(payload.text)
        self._invalidate_outputs(reason="open_file")

        self.state.current_file_path = Path(payload.current_file_path) if payload.current_file_path else None
        if self.state.current_file_path is not None:
            self.master.title(f"Ekdosis TEI Studio v2 - {self.state.current_file_path.name}")
        else:
            self.master.title("Ekdosis TEI Studio v2")

        if payload.config_path:
            config_path = Path(payload.config_path)
            if config_path.exists():
                try:
                    config = load_config(config_path)
                except ValueError:
                    config = None
                if config is not None:
                    self.state.config = config
                    self.state.config_path = config_path
                    self._refresh_config_ui()

        self._schedule_autosave()
        messagebox.showinfo("Autosave", "Enregistrement automatique restauré.", parent=self.master)

    def action_export_tei(self) -> None:
        current_tei = self._current_tei_text()
        if current_tei.strip():
            self.state.tei_xml = current_tei
        self._export_content(
            title="Exporter le TEI",
            warning_message="Générez d'abord un TEI.",
            default_extension=".xml",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
            content=self.state.tei_xml,
            initialfile=self._default_filename(".xml"),
            exporter=export_tei,
        )

    def action_export_html(self) -> None:
        current_tei = self._current_tei_text()
        if current_tei.strip():
            self.state.tei_xml = current_tei
        elif self.state.tei_xml is None:
            if not self._apply_tei_generation(show_error=False):
                messagebox.showerror("Exporter le HTML", "Échec de génération TEI.", parent=self.master)
                return
        if self.state.tei_xml is None:
            messagebox.showwarning("Exporter le HTML", "Générez d'abord un TEI.", parent=self.master)
            return

        html_result = generate_html_preview_from_tei(self.state.tei_xml)
        if not html_result.ok or html_result.html is None:
            if html_result.diagnostics:
                self._set_diagnostics(html_result.diagnostics)
            messagebox.showerror("Exporter le HTML", html_result.message or "Échec de génération HTML.", parent=self.master)
            return
        self.state.html_preview = html_result.html
        self.outputs.set_html(html_result.html)

        self._export_content(
            title="Exporter le HTML",
            warning_message="Générez d'abord un aperçu HTML.",
            default_extension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            content=html_result.html,
            initialfile=self._default_filename(".html"),
            exporter=export_html,
        )

    def action_build_publication_site(self) -> None:
        chosen = filedialog.askopenfilename(
            parent=self.master,
            title="Choisir la configuration du site (JSON)",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not chosen:
            return

        result = build_site_from_config_file(chosen)
        if not result.ok:
            detail = result.error_detail or "Erreur inconnue."
            messagebox.showerror(
                "Génération du site",
                f"{result.message or 'Échec de génération du site.'}\n\n{detail}",
                parent=self.master,
            )
            return

        assert result.output_dir is not None
        base_message = (
            "Génération du site terminée.\n\n"
            f"Dossier de sortie: {result.output_dir}\n"
            f"Pages générées: {len(result.generated_pages)}\n"
            f"Pièces détectées: {result.play_count}\n"
            f"Notices détectées: {result.notice_count}"
        )
        if result.warnings:
            warning_lines = "\n".join(f"- {item}" for item in result.warnings[:20])
            messagebox.showwarning(
                "Génération du site (avec avertissements)",
                f"{base_message}\n\nAvertissements:\n{warning_lines}",
                parent=self.master,
            )
            return

        messagebox.showinfo("Génération du site", base_message, parent=self.master)

    def action_undo(self) -> None:
        widget = self._active_text_widget()
        if widget is None:
            return
        widget.event_generate("<<Undo>>")

    def action_redo(self) -> None:
        widget = self._active_text_widget()
        if widget is None:
            return
        widget.event_generate("<<Redo>>")

    def action_cut(self) -> None:
        widget = self._active_text_widget()
        if widget is None:
            return
        widget.event_generate("<<Cut>>")

    def action_copy(self) -> None:
        widget = self._active_text_widget()
        if widget is None:
            return
        widget.event_generate("<<Copy>>")

    def action_paste(self) -> None:
        widget = self._active_text_widget()
        if widget is None:
            return
        widget.event_generate("<<Paste>>")

    def action_select_all(self) -> None:
        widget = self._active_text_widget()
        if widget is None:
            widget = self.editor.text
        widget.tag_add("sel", "1.0", "end-1c")
        widget.mark_set("insert", "1.0")
        widget.see("insert")

    def _search_next_in(self, text: tk.Text, needle: str) -> bool:
        start = text.index("insert +1c")
        idx = text.search(needle, start, stopindex="end", nocase=True)
        if not idx:
            idx = text.search(needle, "1.0", stopindex=start, nocase=True)
        if not idx:
            return False
        end = f"{idx}+{len(needle)}c"
        text.tag_remove("sel", "1.0", "end")
        text.tag_add("sel", idx, end)
        text.mark_set("insert", end)
        text.see(idx)
        text.focus_set()
        return True

    def _is_widget_editable(self, text: tk.Text) -> bool:
        return str(text.cget("state")) == "normal"

    def _replace_one_in(self, text: tk.Text, pattern: str, replacement: str) -> bool:
        if not self._is_widget_editable(text):
            return False
        if not pattern:
            return False
        ranges = text.tag_ranges("sel")
        if len(ranges) == 2 and text.get(ranges[0], ranges[1]) == pattern:
            text.delete(ranges[0], ranges[1])
            text.insert(ranges[0], replacement)
            return True
        if not self._search_next_in(text, pattern):
            return False
        return self._replace_one_in(text, pattern, replacement)

    def _replace_all_in(self, text: tk.Text, pattern: str, replacement: str) -> int:
        if not self._is_widget_editable(text):
            return 0
        if not pattern:
            return 0
        count = 0
        start = "1.0"
        while True:
            idx = text.search(pattern, start, stopindex="end", nocase=True)
            if not idx:
                break
            end = f"{idx}+{len(pattern)}c"
            text.delete(idx, end)
            text.insert(idx, replacement)
            start = f"{idx}+{len(replacement)}c"
            count += 1
        return count

    def action_find(self) -> None:
        target = self._active_text_widget() or self.editor.text

        SearchReplaceDialog(
            self.master,
            on_find_next=lambda needle: self._search_next_in(target, needle),
            on_replace=lambda needle, replacement: self._replace_one_in(target, needle, replacement),
            on_replace_all=lambda needle, replacement: self._replace_all_in(target, needle, replacement),
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
        if self._autosave_after_id is not None:
            self.after_cancel(self._autosave_after_id)
            self._autosave_after_id = None
        try:
            self._perform_autosave()
        except Exception:
            pass
        self._preview_server.stop()
        self.master.destroy()
