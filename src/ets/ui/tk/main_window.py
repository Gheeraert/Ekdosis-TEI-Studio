from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable
import webbrowser

from ets.ui.tk.welcome_dialog import show_welcome_dialog
from ets.annotations import Annotation, AnnotationCollection, AnnotationValidationError
from ets.markdown_editor import MarkdownEditorWidget
from ets.references import CitationOccurrence, CitationTokenData, ReferencesPanel, format_inline_citation
from ets.application import (
    AppDiagnostic,
    EkdosisGenerationError,
    merge_dramatic_tei_files,
    merge_text_transcription_files,
    build_site_from_publication_request,
    create_annotation,
    delete_annotation,
    export_ekdosis,
    enrich_tei_with_annotations,
    parse_annotation,
    export_html,
    export_tei,
    generate_ekdosis_from_text,
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
from ets.ftp_publish import publish_directory_via_ftp

from .control_bar import ControlBar
from .diagnostics_panel import DiagnosticsPanel
from .dialogs import (
    SearchReplaceDialog,
    open_annotation_dialog,
    open_config_dialog,
    open_dramatic_merge_dialog,
    open_publication_dialog,
    open_text_transcription_merge_dialog,
    show_about_dialog,
    show_help_dialog,
)
from .dialogs.publication_dialog import PublicationDialogResult
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
    ekdosis_body: str | None = None
    ekdosis_full_document: str | None = None
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
        self._preview_server = preview_server or LocalPreviewServer(preferred_port=8765)
        self._site_preview_server: LocalPreviewServer | None = None
        self._autosave_store = autosave_store or AutosaveStore()
        self._open_browser = open_browser or webbrowser.open_new_tab
        self._autosave_after_id: str | None = None
        self._menu_bar: tk.Menu | None = None

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

        self.editor_tabs = ttk.Notebook(self.top)
        self.editor_tabs.grid(row=0, column=0, sticky="nsew")

        self.transcription_tab = ttk.Frame(self.editor_tabs)
        self.transcription_tab.columnconfigure(0, weight=1)
        self.transcription_tab.rowconfigure(0, weight=1)
        self.editor = TextEditor(self.transcription_tab)
        self.editor.grid(row=0, column=0, sticky="nsew")

        self.markdown_editor = MarkdownEditorWidget(self.editor_tabs)
        self._last_editor_mode = "transcription"
        self._last_editable_text_widget: tk.Text = self.editor.text
        self.references_panel = ReferencesPanel(
            self.editor_tabs,
            get_current_text=self._get_text_for_references,
            insert_citation_token=self._insert_citation_token_into_active_editor,
            on_references_changed=self.markdown_editor.force_refresh_preview,
        )
        self.markdown_editor.set_citation_resolver(self._resolve_markdown_citation_preview)

        self.editor_tabs.add(self.transcription_tab, text="Transcription")
        self.editor_tabs.add(self.markdown_editor, text="Éditeur Markdown")
        self.editor_tabs.add(self.references_panel, text="Références")
        self.editor_tabs.bind("<<NotebookTabChanged>>", self._on_editor_tab_changed, add="+")

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
        self.editor.text.bind("<FocusIn>", self._track_transcription_focus, add="+")
        self.markdown_editor.source_text.bind("<FocusIn>", self._track_markdown_focus, add="+")

        self._refresh_config_ui()
        self._install_menus()
        self._install_shortcuts()
        self.markdown_editor.reset_split_view()

        self.after_idle(lambda: show_welcome_dialog(self.winfo_toplevel()))

    def _on_editor_tab_changed(self, _event: tk.Event[tk.Misc]) -> None:
        if self._is_markdown_mode():
            self._last_editor_mode = "markdown"
            self.after_idle(self.markdown_editor.focus_source)
            self.after_idle(self.markdown_editor.reset_split_view)
        elif self._is_transcription_mode():
            self._last_editor_mode = "transcription"
            self.after_idle(self.editor.focus_editor)

        self._refresh_window_title()
        self._refresh_menu_state()

    def _is_markdown_mode(self) -> bool:
        selected = self.editor_tabs.select()
        return bool(selected) and self.editor_tabs.nametowidget(selected) is self.markdown_editor

    def _is_transcription_mode(self) -> bool:
        selected = self.editor_tabs.select()
        return bool(selected) and self.editor_tabs.nametowidget(selected) is self.transcription_tab

    def _select_markdown_mode(self) -> None:
        self.editor_tabs.select(self.markdown_editor)
        self.after_idle(self.markdown_editor.focus_source)

    def _refresh_window_title(self) -> None:
        if self._is_markdown_mode():
            if self.markdown_editor.current_path is not None:
                self.master.title(f"Ekdosis TEI Studio v2 - {self.markdown_editor.current_path.name} [Markdown]")
            else:
                self.master.title("Ekdosis TEI Studio v2 - Document Markdown")
            return
        if self.state.current_file_path is not None:
            self.master.title(f"Ekdosis TEI Studio v2 - {self.state.current_file_path.name}")
            return
        self.master.title("Ekdosis TEI Studio v2")

    def _install_menus(self) -> None:
        install_menus(
            self.master,
            MenuCallbacks(
                new_file=self.action_new_file,
                open_file=self.action_open_file,
                save_file=self.action_save_file,
                save_file_as=self.action_save_file_as,
                close_document=self.action_close_document,
                export_markdown=self.action_export_markdown,
                export_xml_tei=self.action_export_xml_tei,
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
                find_in_preview=self.action_find_in_preview,
                insert_note=self.action_markdown_insert_note,
                insert_link=self.action_markdown_insert_link,
                insert_french_quotes=self.action_markdown_insert_french_quotes,
                insert_thin_nbsp=self.action_markdown_insert_thin_nbsp,
                insert_em_dash=self.action_markdown_insert_em_dash,
                insert_bibliography_block=self.action_markdown_insert_bibliography_block,
                references_add=self.action_references_add,
                references_import=self.action_references_import,
                references_insert_citation=self.action_references_insert_citation,
                references_bibliography=self.action_references_bibliography,
                references_style=self.action_references_style,
                format_bold=self.action_markdown_format_bold,
                format_italic=self.action_markdown_format_italic,
                format_underline=self.action_markdown_format_underline,
                format_sup=self.action_markdown_format_sup,
                format_sub=self.action_markdown_format_sub,
                format_caps=self.action_markdown_format_caps,
                format_smallcaps=self.action_markdown_format_smallcaps,
                structure_h1=self.action_markdown_structure_h1,
                structure_h2=self.action_markdown_structure_h2,
                structure_h3=self.action_markdown_structure_h3,
                structure_h4=self.action_markdown_structure_h4,
                structure_quote=self.action_markdown_structure_quote,
                structure_bulleted_list=self.action_markdown_structure_bulleted_list,
                structure_numbered_list=self.action_markdown_structure_numbered_list,
                structure_separator=self.action_markdown_structure_separator,
                structure_bibliography=self.action_markdown_structure_bibliography,
                validate=self.action_validate,
                validate_generated_tei=self.action_validate_generated_tei,
                generate_tei=self.action_generate_tei,
                preview_html=self.action_preview_html,
                export_tei=self.action_export_tei,
                export_html=self.action_export_html,
                export_ekdosis=self.action_export_ekdosis,
                merge_text_transcriptions=self.action_merge_text_transcriptions,
                merge_dramatic_tei=self.action_merge_dramatic_tei,
                build_publication_site=self.action_build_publication_site,
                add_annotation=self.action_add_annotation,
                edit_annotation=self.action_edit_annotation,
                delete_annotation=self.action_delete_annotation,
                force_preview_refresh=self.action_markdown_force_preview_refresh,
                reset_split_view=self.action_markdown_reset_split_view,
                toggle_diagnostics=self.action_toggle_diagnostics,
                show_about=lambda: show_about_dialog(self.master),
                show_help=lambda: show_help_dialog(self.master),
            ),
        )

        menu_name = self.master.cget("menu")
        if menu_name:
            try:
                self._menu_bar = self.master.nametowidget(menu_name)
            except KeyError:
                self._menu_bar = None

        self._refresh_menu_state()

    def _install_shortcuts(self) -> None:
        self.master.bind_all("<Control-f>", self._shortcut_find, add="+")
        self.master.bind_all("<Control-F>", self._shortcut_find, add="+")
        self.master.bind_all("<Control-a>", self._shortcut_select_all, add="+")
        self.master.bind_all("<Control-A>", self._shortcut_select_all, add="+")
        # Déjà bindés par tk, donc inutile de rebinder ici
        # self.master.bind_all("<Control-x>", self._shortcut_cut, add="+")
        # self.master.bind_all("<Control-X>", self._shortcut_cut, add="+")
        # self.master.bind_all("<Control-c>", self._shortcut_copy, add="+")
        # self.master.bind_all("<Control-C>", self._shortcut_copy, add="+")
        # self.master.bind_all("<Control-v>", self._shortcut_paste, add="+")
        # self.master.bind_all("<Control-V>", self._shortcut_paste, add="+")
        self.master.bind_all("<Control-h>", self._shortcut_replace, add="+")
        self.master.bind_all("<Control-H>", self._shortcut_replace, add="+")
        self.master.bind_all("<Control-s>", self._shortcut_save, add="+")
        self.master.bind_all("<Control-S>", self._shortcut_save, add="+")
        self.master.bind_all("<Control-Shift-S>", self._shortcut_save_as, add="+")
        self.master.bind_all("<Control-b>", self._shortcut_bold, add="+")
        self.master.bind_all("<Control-B>", self._shortcut_bold, add="+")
        self.master.bind_all("<Control-i>", self._shortcut_italic, add="+")
        self.master.bind_all("<Control-I>", self._shortcut_italic, add="+")

    def _active_text_widget(self) -> tk.Text | None:
        focused = self.master.focus_get()
        if isinstance(focused, tk.Text):
            return focused
        if self._is_markdown_mode():
            return self.markdown_editor.source_text
        if self._is_transcription_mode():
            return self.editor.text
        return None

    def _track_transcription_focus(self, _event: tk.Event[tk.Misc]) -> None:
        self._last_editable_text_widget = self.editor.text
        self._last_editor_mode = "transcription"

    def _track_markdown_focus(self, _event: tk.Event[tk.Misc]) -> None:
        self._last_editable_text_widget = self.markdown_editor.source_text
        self._last_editor_mode = "markdown"

    def _editable_insertion_target(self) -> tk.Text:
        focused = self.master.focus_get()
        if isinstance(focused, tk.Text) and str(focused.cget("state")) == "normal":
            self._last_editable_text_widget = focused
            return focused
        if str(self._last_editable_text_widget.cget("state")) == "normal":
            return self._last_editable_text_widget
        if self._last_editor_mode == "markdown":
            return self.markdown_editor.source_text
        return self.editor.text

    def _insert_citation_token_into_active_editor(self, token: str) -> bool:
        focused = self.master.focus_get()
        markdown_source = self.markdown_editor.source_text
        if focused is markdown_source and str(markdown_source.cget("state")) == "normal":
            self.markdown_editor.insert_text_at_cursor(token)
            self._last_editor_mode = "markdown"
            self._last_editable_text_widget = markdown_source
            return True
        if self._last_editor_mode == "markdown" and str(markdown_source.cget("state")) == "normal":
            self.markdown_editor.insert_text_at_cursor(token)
            self._last_editable_text_widget = markdown_source
            return True
        return False

    def _get_text_for_references(self) -> str:
        return self.markdown_editor.get_text()

    def _resolve_markdown_citation_preview(self, token: CitationTokenData) -> str | None:
        reference = self.references_panel.service.get_reference(token.reference_id)
        if reference is None:
            return None
        occurrence = CitationOccurrence(
            id="preview",
            reference_id=token.reference_id,
            locator=token.locator,
            prefix=token.prefix,
            suffix=token.suffix,
            citation_mode=token.mode,
            target_context="markdown_preview",
        )
        return format_inline_citation(reference, occurrence, self.references_panel.service.style_id)

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

    def _shortcut_replace(self, _event: tk.Event[tk.Misc]) -> str:
        self.action_replace()
        return "break"

    def _shortcut_save(self, _event: tk.Event[tk.Misc]) -> str:
        self.action_save_file()
        return "break"

    def _shortcut_save_as(self, _event: tk.Event[tk.Misc]) -> str:
        self.action_save_file_as()
        return "break"

    def _shortcut_bold(self, _event: tk.Event[tk.Misc]) -> str:
        if self._is_markdown_mode():
            self.markdown_editor.apply_bold()
            return "break"
        return ""

    def _shortcut_italic(self, _event: tk.Event[tk.Misc]) -> str:
        if self._is_markdown_mode():
            self.markdown_editor.apply_italic()
            return "break"
        return ""

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
            act_label = str(act_pos)
            for scene_pos, scene in enumerate(act.scenes, start=1):
                scene_label = str(scene_pos)
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
        self._refresh_window_title()

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
        if (
            self.state.tei_xml is None
            and self.state.html_preview is None
            and self.state.ekdosis_body is None
            and not self.state.diagnostics
        ):
            return
        self.state.tei_xml = None
        self.state.html_preview = None
        self.state.ekdosis_body = None
        self.state.ekdosis_full_document = None
        self.state.tei_dirty_by_user = False
        self.state.outputs_stale = True
        self.outputs.set_tei("")
        self.outputs.set_html("")
        self.outputs.set_ekdosis("")
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
            self.state.ekdosis_body = None
            self.state.ekdosis_full_document = None
            self.state.outputs_stale = True
            self.outputs.set_tei("")
            self.outputs.set_html("")
            self.outputs.set_ekdosis("")
            if show_error:
                messagebox.showerror("Génération TEI", result.message or "Échec de génération TEI.", parent=self.master)
            return False

        enriched_tei, enrichment_diagnostics, enrichment_error = self._maybe_enrich_tei_with_annotations(result.tei_xml)
        if enriched_tei is None:
            self._set_diagnostics(result.diagnostics + enrichment_diagnostics)
            self.state.tei_xml = None
            self.state.html_preview = None
            self.state.ekdosis_body = None
            self.state.ekdosis_full_document = None
            self.state.outputs_stale = True
            self.outputs.set_tei("")
            self.outputs.set_html("")
            self.outputs.set_ekdosis("")
            if show_error:
                messagebox.showerror("Génération TEI", enrichment_error or "Échec de l'enrichissement TEI.", parent=self.master)
            return False

        self._set_diagnostics(result.diagnostics + enrichment_diagnostics)
        self.state.tei_xml = enriched_tei
        self.outputs.set_tei(enriched_tei)
        self.state.tei_dirty_by_user = False
        self.state.html_preview = None
        self.state.ekdosis_body = None
        self.state.ekdosis_full_document = None
        self.outputs.set_html("")
        self.outputs.set_ekdosis("")
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
        if self._is_markdown_mode():
            self.markdown_editor.new_document()
            self._refresh_window_title()
            return
        self.editor.clear()
        self._invalidate_outputs(reason="new_file")
        self.state.current_file_path = None
        self._refresh_window_title()
        self._schedule_autosave()

    def action_open_file(self) -> None:
        if self._is_markdown_mode():
            try:
                opened = self.markdown_editor.open_file()
            except OSError as exc:
                messagebox.showerror("Erreur d'ouverture", str(exc), parent=self.master)
                return
            if opened is None:
                return
            self._refresh_window_title()
            return
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
        self._refresh_window_title()
        self._schedule_autosave()

    def action_save_file(self) -> None:
        if self._is_markdown_mode():
            try:
                saved = self.markdown_editor.save_file()
            except OSError as exc:
                messagebox.showerror("Erreur d'enregistrement", str(exc), parent=self.master)
                return
            if saved is not None:
                self._refresh_window_title()
            return
        if self.state.current_file_path is None:
            self.action_save_file_as()
            return
        try:
            self._write_current_file(self.state.current_file_path)
        except OSError as exc:
            messagebox.showerror("Erreur d'enregistrement", str(exc), parent=self.master)

    def action_save_file_as(self) -> None:
        if self._is_markdown_mode():
            try:
                saved = self.markdown_editor.save_file_as()
            except OSError as exc:
                messagebox.showerror("Erreur d'enregistrement", str(exc), parent=self.master)
                return
            if saved is not None:
                self._refresh_window_title()
            return
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

    def action_close_document(self) -> None:
        if self._is_markdown_mode():
            self.markdown_editor.close_document()
            self._refresh_window_title()
            return
        self.action_new_file()

    def action_export_markdown(self) -> None:
        try:
            exported = self.markdown_editor.export_markdown()
        except OSError as exc:
            messagebox.showerror("Exporter Markdown", str(exc), parent=self.master)
            return
        if exported is None:
            return
        messagebox.showinfo("Exporter Markdown", f"Fichier exporté:\n{exported}", parent=self.master)

    def action_export_xml_tei(self) -> None:
        if self._is_markdown_mode():
            try:
                exported = self.markdown_editor.export_tei_document()
            except OSError as exc:
                messagebox.showerror("Exporter XML-TEI", str(exc), parent=self.master)
                return
            if exported is None:
                return
            messagebox.showinfo("Exporter XML-TEI", f"Fichier exporté:\n{exported}", parent=self.master)
            return
        self.action_export_tei()

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
        self._refresh_window_title()

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

    def action_export_ekdosis(self) -> None:
        if not self._ensure_config():
            return
        assert self.state.config is not None

        metadata = {
            "title": self.state.config.title,
            "author": self.state.config.author,
            "editor": self.state.config.editor,
        }
        witness_data = [
            {"abbr": witness.siglum, "year": witness.year, "desc": witness.description}
            for witness in self.state.config.witnesses
        ]

        try:
            result = generate_ekdosis_from_text(
                text=self._current_text(),
                witnesses=witness_data,
                reference_witness=self.state.config.reference_witness,
                metadata=metadata,
            )
        except EkdosisGenerationError as exc:
            if exc.diagnostics:
                details = "\n".join(exc.diagnostics[:20])
                message = f"{exc}\n\n{details}"
            else:
                message = str(exc)
            messagebox.showerror("Export LaTeX-Ekdosis", message, parent=self.master)
            return

        self.state.ekdosis_body = result.body
        self.state.ekdosis_full_document = result.full_document
        self.outputs.set_ekdosis(result.body)

        if result.warnings:
            warning_lines = "\n".join(f"- {item}" for item in result.warnings[:20])
            messagebox.showwarning(
                "Export LaTeX-Ekdosis",
                f"Le document Ekdosis a été généré avec avertissements.\n\n{warning_lines}",
                parent=self.master,
            )

        self._export_content(
            title="Exporter le LaTeX-Ekdosis",
            warning_message="Aucun contenu Ekdosis à exporter.",
            default_extension=".tex",
            filetypes=[("LaTeX files", "*.tex"), ("All files", "*.*")],
            content=result.full_document,
            initialfile=self._default_filename(".tex", suffix="_ekdosis"),
            exporter=export_ekdosis,
        )

    def action_build_publication_site(self) -> None:
        dialog_result = open_publication_dialog(self.master)
        if dialog_result is None:
            return

        if isinstance(dialog_result, PublicationDialogResult):
            action = dialog_result.action
            request = dialog_result.site_request
            ftp_config = dialog_result.ftp_config
        else:
            action = "build"
            request = dialog_result
            ftp_config = None

        try:
            result = build_site_from_publication_request(request)
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            messagebox.showerror(
                "Génération du site",
                f"Échec de génération du site.\n\n{exc}",
                parent=self.master,
            )
            return
        if not result.ok:
            detail = result.error_detail or "Erreur inconnue."
            messagebox.showerror(
                "Génération du site",
                f"{result.message or 'Échec de génération du site.'}\n\n{detail}",
                parent=self.master,
            )
            return

        if action == "publish_ftp":
            if ftp_config is None:
                messagebox.showerror(
                    "Publication FTP",
                    "Requête de FTP - mais pas de fichier de configuration fourni.",
                    parent=self.master,
                )
                return
            if result.output_dir is None:
                messagebox.showerror(
                    "Publication FTP",
                    "Site generation terminé, mais répertoire de sortie non précisé. L'upload FTP ne peut pas démarrer.",
                    parent=self.master,
                )
                return

            try:
                ftp_result = publish_directory_via_ftp(local_dir=result.output_dir, config=ftp_config)
            except Exception as exc:  # pragma: no cover - defensive UI boundary
                messagebox.showerror(
                    "Publication FTP",
                    f"Échec inattendu pendant la publication FTP.\n\n{exc}",
                    parent=self.master,
                )
                return
            if not ftp_result.ok:
                detail = ftp_result.error_detail or "Erreur FTP inconnue."
                messagebox.showerror(
                    "Publication FTP",
                    (
                        "Site generationOK, mais échec de la publication FTP.\n\n"
                        f"{detail}\n\n"
                        f"Fichiers transférés: {ftp_result.files_transferred}\n"
                        f"Répertoires créés: {ftp_result.directories_created}"
                    ),
                    parent=self.master,
                )
                return

            base_message = (
                "Site généré et publié via FTP : OK.\n\n"
                f"Local output: {result.output_dir}\n"
                f"Fichiers transférés: {ftp_result.files_transferred}\n"
                f"Répertoires créés: {ftp_result.directories_created}"
            )
            if ftp_result.warnings:
                warning_lines = "\n".join(f"- {item}" for item in ftp_result.warnings[:20])
                messagebox.showwarning(
                    "Publication FTP (avec avertissements)",
                    f"{base_message}\n\nWarnings:\n{warning_lines}",
                    parent=self.master,
                )
            else:
                messagebox.showinfo("Publication FTP", base_message, parent=self.master)
            return

        output_dir_text = str(result.output_dir) if result.output_dir is not None else "(inconnu)"
        base_message = (
            "Génération du site terminée.\n\n"
            f"Dossier de sortie: {output_dir_text}\n"
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
        else:
            messagebox.showinfo("Génération du site", base_message, parent=self.master)

        if result.output_dir is not None:
            try:
                self._open_publication_site_preview(result.output_dir)
            except OSError as exc:
                messagebox.showwarning(
                    "Génération du site",
                    f"Le site a bien été généré, mais l'ouverture automatique a échoué.\n\n{exc}",
                    parent=self.master,
                )

    def _open_publication_site_preview(self, output_dir: Path) -> None:
        resolved_output_dir = output_dir.resolve()
        if self._site_preview_server is None or self._site_preview_server.root_dir.resolve() != resolved_output_dir:
            if self._site_preview_server is not None:
                self._site_preview_server.stop()
            self._site_preview_server = LocalPreviewServer(root_dir=resolved_output_dir, preferred_port=8766,)

        self._site_preview_server.ensure_running()
        site_url = self._site_preview_server.url_for("index.html")
        self._open_browser(site_url)

    def action_merge_dramatic_tei(self) -> None:
        request = open_dramatic_merge_dialog(self.master)
        if request is None:
            return

        try:
            result = merge_dramatic_tei_files(request)
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            messagebox.showerror(
                "Fusion XML dramatiques",
                f"Echec de la fusion XML dramatique.\n\n{exc}",
                parent=self.master,
            )
            return

        if not result.ok:
            detail = result.error_detail or "Erreur inconnue."
            messagebox.showerror(
                "Fusion XML dramatiques",
                f"{result.message or 'Echec de la fusion XML dramatique.'}\n\n{detail}",
                parent=self.master,
            )
            return

        output_text = str(result.output_path) if result.output_path is not None else "(inconnu)"
        base_message = (
            "Fusion XML dramatique terminée.\n\n"
            f"Fichier de sortie: {output_text}\n"
            f"Actes fusionnes: {result.merged_act_count}"
        )
        if result.warnings:
            warning_lines = "\n".join(f"- {item}" for item in result.warnings[:20])
            messagebox.showwarning(
                "Fusion XML dramatiques (avec avertissements)",
                f"{base_message}\n\nAvertissements:\n{warning_lines}",
                parent=self.master,
            )
            return

        messagebox.showinfo("Fusion XML dramatiques", base_message, parent=self.master)

    def action_merge_text_transcriptions(self) -> None:
        request = open_text_transcription_merge_dialog(self.master)
        if request is None:
            return

        try:
            result = merge_text_transcription_files(request)
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            messagebox.showerror(
                "Fusion transcriptions texte",
                f"Echec de la fusion de transcriptions.\n\n{exc}",
                parent=self.master,
            )
            return

        if not result.ok:
            detail = result.error_detail or "Erreur inconnue."
            messagebox.showerror(
                "Fusion transcriptions texte",
                f"{result.message or 'Echec de la fusion de transcriptions.'}\n\n{detail}",
                parent=self.master,
            )
            return

        output_text = str(result.output_path) if result.output_path is not None else "(inconnu)"
        base_message = (
            "Fusion de transcriptions terminee.\n\n"
            f"Fichier de sortie: {output_text}\n"
            f"Fichiers fusionnes: {result.merged_file_count}"
        )
        if result.warnings:
            warning_lines = "\n".join(f"- {item}" for item in result.warnings[:20])
            messagebox.showwarning(
                "Fusion transcriptions texte (avec avertissements)",
                f"{base_message}\n\nAvertissements:\n{warning_lines}",
                parent=self.master,
            )
            return

        messagebox.showinfo("Fusion transcriptions texte", base_message, parent=self.master)

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
            widget = self.markdown_editor.source_text if self._is_markdown_mode() else self.editor.text
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
        if self._is_markdown_mode():
            focus = self.master.focus_get()
            if focus is self.markdown_editor.preview_text:
                self.markdown_editor.open_preview_search_dialog()
            else:
                self.markdown_editor.open_source_search_dialog()
            return
        target = self._active_text_widget() or self.editor.text

        SearchReplaceDialog(
            self.master,
            on_find_next=lambda needle: self._search_next_in(target, needle),
            on_replace=lambda needle, replacement: self._replace_one_in(target, needle, replacement),
            on_replace_all=lambda needle, replacement: self._replace_all_in(target, needle, replacement),
        )

    def action_replace(self) -> None:
        if self._is_markdown_mode():
            self.markdown_editor.open_source_search_dialog()
            return
        self.action_find()

    def action_find_in_preview(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.open_preview_search_dialog()

    def action_markdown_insert_note(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.insert_note()

    def action_markdown_insert_link(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.insert_link()

    def action_markdown_insert_french_quotes(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.insert_french_quotes()

    def action_markdown_insert_thin_nbsp(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.insert_thin_nbsp()

    def action_markdown_insert_em_dash(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.insert_em_dash()

    def action_markdown_insert_bibliography_block(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.insert_bibliography_block()

    def action_references_add(self) -> None:
        self.editor_tabs.select(self.references_panel)
        self.references_panel.action_add_reference()

    def action_references_import(self) -> None:
        self.editor_tabs.select(self.references_panel)
        self.references_panel.action_import_references()

    def action_references_insert_citation(self) -> None:
        self.references_panel.action_insert_citation()

    def action_references_bibliography(self) -> None:
        self.editor_tabs.select(self.references_panel)
        self.references_panel.action_show_bibliography()

    def action_references_style(self) -> None:
        self.editor_tabs.select(self.references_panel)
        self.references_panel.action_choose_style()

    def action_markdown_format_bold(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.apply_bold()

    def action_markdown_format_italic(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.apply_italic()

    def action_markdown_format_underline(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.apply_underline()

    def action_markdown_format_sup(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.apply_sup()

    def action_markdown_format_sub(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.apply_sub()

    def action_markdown_format_caps(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.apply_caps()

    def action_markdown_format_smallcaps(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.apply_smallcaps()

    def action_markdown_structure_h1(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.apply_heading_1()

    def action_markdown_structure_h2(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.apply_heading_2()

    def action_markdown_structure_h3(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.apply_heading_3()

    def action_markdown_structure_h4(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.apply_heading_4()

    def action_markdown_structure_quote(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.apply_quote()

    def action_markdown_structure_bulleted_list(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.apply_bullet_list()

    def action_markdown_structure_numbered_list(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.apply_numbered_list()

    def action_markdown_structure_separator(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.insert_separator()

    def action_markdown_structure_bibliography(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.insert_bibliography_block()

    def action_markdown_force_preview_refresh(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.force_refresh_preview()

    def action_markdown_reset_split_view(self) -> None:
        self._select_markdown_mode()
        self.markdown_editor.reset_split_view()

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
        if self._site_preview_server is not None:
            self._site_preview_server.stop()
        self.master.destroy()

    def _is_references_mode(self) -> bool:
        selected = self.editor_tabs.select()
        return bool(selected) and self.editor_tabs.nametowidget(selected) is self.references_panel

    def _set_top_menu_state(self, label: str, state: str) -> None:
        if self._menu_bar is None:
            return
        end_index = self._menu_bar.index("end")
        if end_index is None:
            return

        for index in range(end_index + 1):
            try:
                if self._menu_bar.entrycget(index, "label") == label:
                    self._menu_bar.entryconfigure(index, state=state)
                    return
            except tk.TclError:
                continue

    def _refresh_menu_state(self) -> None:
        if self._is_transcription_mode():
            states = {
                "Insertion": "disabled",
                "Références": "disabled",
                "Format": "disabled",
                "Structure": "disabled",
            }
        elif self._is_references_mode():
            states = {
                "Insertion": "disabled",
                "Références": "normal",
                "Format": "disabled",
                "Structure": "disabled",
            }
        else:  # mode markdown
            states = {
                "Insertion": "normal",
                "Références": "normal",
                "Format": "normal",
                "Structure": "normal",
            }

        for label, state in states.items():
            self._set_top_menu_state(label, state)
