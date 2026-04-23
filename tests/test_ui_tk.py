from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from uuid import uuid4

import pytest

from ets.annotations import Annotation, AnnotationAnchor, AnnotationCollection
from ets.application import (
    AppDiagnostic,
    DramaticTeiMergeRequest,
    DramaticTeiMergeServiceResult,
    DramaticDocumentInput,
    DramaticPlayInput,
    GenerationResult,
    SiteIdentityInput,
    SitePublicationRequest,
    TextTranscriptionMergeRequest,
    TextTranscriptionMergeServiceResult,
    load_annotations,
    load_config,
)
from ets.application.editorial_notice_import.models import (
    EditorialImportResult,
    ValidationMessage,
    ValidationReport,
    ValidationSeverity,
)
from ets.application.site_builder_models import SiteBuildServiceResult
from ets.infrastructure import AutosavePayload, AutosaveStore
from ets.ui.tk.helpers import diagnostic_line_numbers, format_config_status
from ets.ui.tk.main_window import MainWindow, suggest_next_annotation_id
from ets.ui.tk.dialogs.publication_dialog import PublicationDialog


RUNTIME_DIR = Path(__file__).resolve().parents[1] / "tests" / "_runtime"
RUNTIME_DIR.mkdir(exist_ok=True)


def _collection_with_ids(*ids: str) -> AnnotationCollection:
    annotations = [
        Annotation(
            id=item,
            type="explicative",
            anchor=AnnotationAnchor(kind="line", act="1", scene="1", line="1"),
            content="x",
            status="draft",
            keywords=[],
        )
        for item in ids
    ]
    return AnnotationCollection(version=1, annotations=annotations)


def test_suggest_next_annotation_id_empty_collection() -> None:
    assert suggest_next_annotation_id(_collection_with_ids()) == "n1"


def test_suggest_next_annotation_id_sequential_ids() -> None:
    assert suggest_next_annotation_id(_collection_with_ids("n1", "n2", "n3")) == "n4"


def test_suggest_next_annotation_id_with_gaps() -> None:
    assert suggest_next_annotation_id(_collection_with_ids("n1", "n3", "n4")) == "n5"


def test_suggest_next_annotation_id_with_mixed_ids() -> None:
    assert suggest_next_annotation_id(_collection_with_ids("note_old", "n7")) == "n8"


def _make_root() -> tk.Tk:
    try:
        root = tk.Tk()
    except tk.TclError as exc:  # pragma: no cover - depends on runtime display availability
        pytest.skip(f"Tk not available in this environment: {exc}")
    root.withdraw()
    return root


def _annotations_fixture_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "annotations" / "berenice_1_1"


def _load_annotation_fixture_in_window(window: MainWindow) -> Path:
    fixture_dir = _annotations_fixture_dir()
    window.state.config = load_config(fixture_dir / "config.json")
    window.editor.set_text((fixture_dir / "input.txt").read_text(encoding="utf-8"))
    return fixture_dir


def test_tk_main_window_smoke_instantiation() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        root.update_idletasks()
        assert window.winfo_exists()
    finally:
        root.destroy()


def test_ui_invalidate_outputs_clears_stale_generated_content() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        window.state.tei_xml = "<TEI/>"
        window.state.html_preview = "<html/>"
        window.state.diagnostics = [AppDiagnostic(level="ERROR", code="E", message="m", line_number=1)]
        window._invalidate_outputs(reason="text_changed")

        assert window.state.tei_xml is None
        assert window.state.html_preview is None
        assert window.state.outputs_stale is True
        assert window.state.diagnostics == []
    finally:
        root.destroy()


def test_ui_helpers_are_stable() -> None:
    diagnostics = [
        AppDiagnostic(level="ERROR", code="E1", message="x", line_number=4),
        AppDiagnostic(level="ERROR", code="E2", message="x", line_number=2),
        AppDiagnostic(level="WARNING", code="W1", message="x", line_number=4),
        AppDiagnostic(level="ERROR", code="E3", message="x", line_number=None),
    ]
    assert diagnostic_line_numbers(diagnostics) == [2, 4]
    assert "aucune" in format_config_status(None, None)


def test_main_window_uses_vertical_pane_and_control_wrap_logic() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)

        panes = window.vertical_pane.panes()
        assert len(panes) == 2

        window.control._relayout(800)
        wrapped_row = int(window.control.buttons_row.grid_info()["row"])
        assert wrapped_row == 1

        window.control._relayout(1400)
        wide_row = int(window.control.buttons_row.grid_info()["row"])
        assert wide_row == 0
    finally:
        root.destroy()


def test_restore_autosave_reloads_text_and_invalidates_outputs(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        autosave_base = RUNTIME_DIR / f"ui_autosave_{uuid4().hex}"
        autosave_base.mkdir(parents=True, exist_ok=True)

        store = AutosaveStore(base_dir=autosave_base)
        store.save(AutosavePayload(text="Texte restauré"))

        window = MainWindow(root, autosave_store=store)
        window.state.tei_xml = "<TEI/>"
        window.state.html_preview = "<html/>"
        window.outputs.set_tei("<TEI/>")
        window.outputs.set_html("<html/>")

        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args, **kwargs: None)
        monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *args, **kwargs: True)

        window.action_restore_autosave()

        assert window.editor.get_text() == "Texte restauré"
        assert window.state.tei_xml is None
        assert window.state.html_preview is None
        assert window.state.outputs_stale is True
    finally:
        root.destroy()


def test_restore_autosave_when_missing_is_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        autosave_base = RUNTIME_DIR / f"ui_autosave_missing_{uuid4().hex}"
        autosave_base.mkdir(parents=True, exist_ok=True)

        window = MainWindow(root, autosave_store=AutosaveStore(base_dir=autosave_base))
        called: list[str] = []
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args, **kwargs: called.append("info"))

        window.action_restore_autosave()
        assert called == ["info"]
    finally:
        root.destroy()


def test_validate_generated_tei_action_without_tei_is_non_blocking(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        called: list[str] = []
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args, **kwargs: called.append("info"))
        window.action_validate_generated_tei()
        assert called == ["info"]
    finally:
        root.destroy()


def test_validate_generated_tei_action_with_invalid_tei_keeps_state(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        window.state.tei_xml = "<root/>"
        warnings: list[str] = []
        monkeypatch.setattr("tkinter.messagebox.showwarning", lambda *args, **kwargs: warnings.append("warn"))

        window.action_validate_generated_tei()

        assert warnings == ["warn"]
        assert window.state.tei_xml == "<root/>"
    finally:
        root.destroy()


def test_output_tabs_tei_editable_html_readonly() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        assert str(window.outputs.tei_text.cget("state")) == "normal"
        assert str(window.outputs.html_text.cget("state")) == "disabled"
    finally:
        root.destroy()


def test_output_tabs_include_annotations_tab() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        labels = [window.outputs.notebook.tab(tab_id, "text") for tab_id in window.outputs.notebook.tabs()]
        assert "Annotations" in labels
    finally:
        root.destroy()


def test_manual_tei_edit_sets_dirty_flag() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        window.outputs.set_tei("<TEI/>")
        window.state.tei_dirty_by_user = False
        window.outputs.tei_text.insert("end", "\n<!-- edit -->")
        root.update_idletasks()

        assert window.state.tei_dirty_by_user is True
        assert "<!-- edit -->" in (window.state.tei_xml or "")
    finally:
        root.destroy()


def test_generate_tei_warns_before_overwriting_manual_edit(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        window.state.tei_dirty_by_user = True
        called: list[str] = []
        monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *args, **kwargs: False)
        monkeypatch.setattr(window, "_apply_tei_generation", lambda **kwargs: called.append("gen") or True)

        window.action_generate_tei()
        assert called == []
    finally:
        root.destroy()


def test_export_tei_uses_visible_edited_tei(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        window.outputs.set_tei("<TEI>edited</TEI>")
        window.state.tei_xml = "<TEI>old</TEI>"

        out_path = RUNTIME_DIR / f"export_tei_{uuid4().hex}.xml"
        monkeypatch.setattr("tkinter.filedialog.asksaveasfilename", lambda **kwargs: str(out_path))
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args, **kwargs: None)
        captured: list[str] = []

        def _fake_export(content: str, output_path: str | Path) -> Path:
            captured.append(content)
            path = Path(output_path)
            path.write_text(content, encoding="utf-8")
            return path

        monkeypatch.setattr("ets.ui.tk.main_window.export_tei", _fake_export)
        window.action_export_tei()

        assert captured == ["<TEI>edited</TEI>"]
    finally:
        root.destroy()


def test_validate_generated_tei_uses_visible_edited_tei(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        window.outputs.set_tei("<TEI>edited</TEI>")
        window.state.tei_xml = "<TEI>old</TEI>"

        seen: list[str] = []

        class _Result:
            is_valid = False
            schema_name = "tei_all.rng"
            engine_name = "lxml-relaxng"
            errors = []

        monkeypatch.setattr("ets.ui.tk.main_window.validate_tei_xml", lambda xml_text: seen.append(xml_text) or _Result())
        monkeypatch.setattr("tkinter.messagebox.showwarning", lambda *args, **kwargs: None)

        window.action_validate_generated_tei()
        assert seen == ["<TEI>edited</TEI>"]
    finally:
        root.destroy()


def test_find_targets_active_tei_widget(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        window.outputs.set_tei("alpha beta")
        window.editor.set_text("gamma delta")
        monkeypatch.setattr(window, "_active_text_widget", lambda: window.outputs.tei_text)

        def _fake_dialog(parent: tk.Misc, *, on_find_next, on_replace, on_replace_all) -> None:  # type: ignore[no-untyped-def]
            assert on_find_next("beta") is True

        monkeypatch.setattr("ets.ui.tk.main_window.SearchReplaceDialog", _fake_dialog)
        window.action_find()

        selected = window.outputs.tei_text.get("sel.first", "sel.last")
        assert selected == "beta"
    finally:
        root.destroy()


def test_select_all_applies_to_active_tei_widget() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        window.outputs.set_tei("abc")
        window._active_text_widget = lambda: window.outputs.tei_text  # type: ignore[method-assign]
        window.action_select_all()
        assert window.outputs.tei_text.get("sel.first", "sel.last") == "abc"
    finally:
        root.destroy()


def test_tools_menu_contains_manual_tei_validation_action() -> None:
    root = _make_root()
    try:
        MainWindow(root)
        menubar = root.nametowidget(str(root["menu"]))
        tools_menu_widget = None
        end = menubar.index("end")
        assert end is not None
        for i in range(end + 1):
            if menubar.type(i) == "cascade" and menubar.entrycget(i, "label") == "Outils":
                tools_menu_widget = root.nametowidget(menubar.entrycget(i, "menu"))
                break
        assert tools_menu_widget is not None

        labels: list[str] = []
        tools_end = tools_menu_widget.index("end")
        assert tools_end is not None
        for i in range(tools_end + 1):
            if tools_menu_widget.type(i) == "command":
                labels.append(tools_menu_widget.entrycget(i, "label"))
        assert "Valider la TEI générée" in labels
        assert "Fusionner des transcriptions texte…" in labels
        assert "Fusionner des XML dramatiques…" in labels
        assert "Générer le site de publication…" in labels
    finally:
        root.destroy()


def test_action_merge_text_transcriptions_success_routes_through_service(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        request = TextTranscriptionMergeRequest(
            input_paths=(RUNTIME_DIR / "scene1.txt", RUNTIME_DIR / "scene2.txt"),
            output_path=RUNTIME_DIR / "merged.txt",
            separator="\n\n",
        )
        messages: list[str] = []
        called: list[TextTranscriptionMergeRequest] = []
        monkeypatch.setattr("ets.ui.tk.main_window.open_text_transcription_merge_dialog", lambda _parent: request)
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args, **kwargs: None)
        monkeypatch.setattr("tkinter.messagebox.showwarning", lambda *args, **kwargs: None)

        def _fake_merge(payload: TextTranscriptionMergeRequest) -> TextTranscriptionMergeServiceResult:
            called.append(payload)
            return TextTranscriptionMergeServiceResult(
                ok=True,
                output_path=(RUNTIME_DIR / "merged.txt").resolve(),
                merged_file_count=2,
                warnings=(),
                message="ok",
            )

        monkeypatch.setattr("ets.ui.tk.main_window.merge_text_transcription_files", _fake_merge)
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda _title, message, **kwargs: messages.append(message))

        window.action_merge_text_transcriptions()

        assert called == [request]
        assert messages
        assert "Fusion de transcriptions terminee" in messages[-1]
        assert "Fichiers fusionnes: 2" in messages[-1]
    finally:
        root.destroy()


def test_action_merge_text_transcriptions_failure_shows_error(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        request = TextTranscriptionMergeRequest(
            input_paths=(RUNTIME_DIR / "scene1.txt", RUNTIME_DIR / "scene2.txt"),
            output_path=RUNTIME_DIR / "merged.txt",
        )
        errors: list[str] = []
        monkeypatch.setattr("ets.ui.tk.main_window.open_text_transcription_merge_dialog", lambda _parent: request)
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args, **kwargs: None)
        monkeypatch.setattr("tkinter.messagebox.showwarning", lambda *args, **kwargs: None)
        monkeypatch.setattr(
            "ets.ui.tk.main_window.merge_text_transcription_files",
            lambda _request: TextTranscriptionMergeServiceResult(
                ok=False,
                message="Text transcription merge failed.",
                error_code="E_TEXT_TRANSCRIPTION_MERGE",
                error_detail="invalid encoding",
            ),
        )
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda _title, message, **kwargs: errors.append(message))

        window.action_merge_text_transcriptions()

        assert errors
        assert "Text transcription merge failed." in errors[-1]
        assert "invalid encoding" in errors[-1]
    finally:
        root.destroy()


def test_action_merge_text_transcriptions_surfaces_warnings(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        request = TextTranscriptionMergeRequest(
            input_paths=(RUNTIME_DIR / "scene1.txt", RUNTIME_DIR / "scene2.txt"),
            output_path=RUNTIME_DIR / "merged.txt",
        )
        warnings: list[str] = []
        called: list[TextTranscriptionMergeRequest] = []
        monkeypatch.setattr("ets.ui.tk.main_window.open_text_transcription_merge_dialog", lambda _parent: request)
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args, **kwargs: None)
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args, **kwargs: None)

        def _fake_merge(payload: TextTranscriptionMergeRequest) -> TextTranscriptionMergeServiceResult:
            called.append(payload)
            return TextTranscriptionMergeServiceResult(
                ok=True,
                output_path=(RUNTIME_DIR / "merged.txt").resolve(),
                merged_file_count=2,
                warnings=("Skipped duplicate path.",),
                message="ok",
            )

        monkeypatch.setattr("ets.ui.tk.main_window.merge_text_transcription_files", _fake_merge)
        monkeypatch.setattr("tkinter.messagebox.showwarning", lambda _title, message, **kwargs: warnings.append(message))

        window.action_merge_text_transcriptions()

        assert called == [request]
        assert warnings
        assert "Avertissements" in warnings[-1]
        assert "Skipped duplicate path." in warnings[-1]
    finally:
        root.destroy()


def test_action_merge_text_transcriptions_cancelled_dialog_does_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        called: list[str] = []
        monkeypatch.setattr("ets.ui.tk.main_window.open_text_transcription_merge_dialog", lambda _parent: None)
        monkeypatch.setattr(
            "ets.ui.tk.main_window.merge_text_transcription_files",
            lambda _request: called.append("service") or TextTranscriptionMergeServiceResult(ok=False),
        )
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args, **kwargs: called.append("info"))
        monkeypatch.setattr("tkinter.messagebox.showwarning", lambda *args, **kwargs: called.append("warn"))
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args, **kwargs: called.append("error"))

        window.action_merge_text_transcriptions()

        assert called == []
    finally:
        root.destroy()


def test_action_merge_dramatic_tei_success_routes_through_service(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        request = DramaticTeiMergeRequest(
            act_xml_paths=(RUNTIME_DIR / "act1.xml", RUNTIME_DIR / "act2.xml"),
            output_path=RUNTIME_DIR / "merged.xml",
        )
        messages: list[str] = []
        called: list[DramaticTeiMergeRequest] = []
        monkeypatch.setattr("ets.ui.tk.main_window.open_dramatic_merge_dialog", lambda _parent: request)
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args, **kwargs: None)
        monkeypatch.setattr("tkinter.messagebox.showwarning", lambda *args, **kwargs: None)

        def _fake_merge(payload: DramaticTeiMergeRequest) -> DramaticTeiMergeServiceResult:
            called.append(payload)
            return DramaticTeiMergeServiceResult(
                ok=True,
                output_path=(RUNTIME_DIR / "merged.xml").resolve(),
                merged_act_count=2,
                warnings=(),
                message="ok",
            )

        monkeypatch.setattr("ets.ui.tk.main_window.merge_dramatic_tei_files", _fake_merge)
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda _title, message, **kwargs: messages.append(message))

        window.action_merge_dramatic_tei()

        assert called == [request]
        assert messages
        assert "Fusion XML dramatique" in messages[-1]
        assert "Actes fusionnes: 2" in messages[-1]
    finally:
        root.destroy()


def test_action_merge_dramatic_tei_failure_shows_error(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        request = DramaticTeiMergeRequest(
            act_xml_paths=(RUNTIME_DIR / "act1.xml", RUNTIME_DIR / "act2.xml"),
            output_path=RUNTIME_DIR / "merged.xml",
        )
        errors: list[str] = []
        monkeypatch.setattr("ets.ui.tk.main_window.open_dramatic_merge_dialog", lambda _parent: request)
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args, **kwargs: None)
        monkeypatch.setattr("tkinter.messagebox.showwarning", lambda *args, **kwargs: None)
        monkeypatch.setattr(
            "ets.ui.tk.main_window.merge_dramatic_tei_files",
            lambda _request: DramaticTeiMergeServiceResult(
                ok=False,
                message="Dramatic TEI merge failed.",
                error_code="E_DRAMATIC_TEI_MERGE",
                error_detail="title differs",
            ),
        )
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda _title, message, **kwargs: errors.append(message))

        window.action_merge_dramatic_tei()

        assert errors
        assert "Dramatic TEI merge failed." in errors[-1]
        assert "title differs" in errors[-1]
    finally:
        root.destroy()


def test_action_merge_dramatic_tei_surfaces_warnings(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        request = DramaticTeiMergeRequest(
            act_xml_paths=(RUNTIME_DIR / "act1.xml", RUNTIME_DIR / "act2.xml"),
            output_path=RUNTIME_DIR / "merged.xml",
        )
        warnings: list[str] = []
        called: list[DramaticTeiMergeRequest] = []
        monkeypatch.setattr("ets.ui.tk.main_window.open_dramatic_merge_dialog", lambda _parent: request)
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args, **kwargs: None)
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args, **kwargs: None)

        def _fake_merge(payload: DramaticTeiMergeRequest) -> DramaticTeiMergeServiceResult:
            called.append(payload)
            return DramaticTeiMergeServiceResult(
                ok=True,
                output_path=(RUNTIME_DIR / "merged.xml").resolve(),
                merged_act_count=2,
                warnings=("Header differs for 'act2.xml'.",),
                message="ok",
            )

        monkeypatch.setattr("ets.ui.tk.main_window.merge_dramatic_tei_files", _fake_merge)
        monkeypatch.setattr("tkinter.messagebox.showwarning", lambda _title, message, **kwargs: warnings.append(message))

        window.action_merge_dramatic_tei()

        assert called == [request]
        assert warnings
        assert "Avertissements" in warnings[-1]
        assert "Header differs for 'act2.xml'." in warnings[-1]
    finally:
        root.destroy()


def test_action_merge_dramatic_tei_cancelled_dialog_does_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        called: list[str] = []
        monkeypatch.setattr("ets.ui.tk.main_window.open_dramatic_merge_dialog", lambda _parent: None)
        monkeypatch.setattr(
            "ets.ui.tk.main_window.merge_dramatic_tei_files",
            lambda _request: called.append("service") or DramaticTeiMergeServiceResult(ok=False),
        )
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args, **kwargs: called.append("info"))
        monkeypatch.setattr("tkinter.messagebox.showwarning", lambda *args, **kwargs: called.append("warn"))
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args, **kwargs: called.append("error"))

        window.action_merge_dramatic_tei()

        assert called == []
    finally:
        root.destroy()


def test_action_build_publication_site_success_routes_through_service(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        opened_urls: list[str] = []
        window = MainWindow(root, open_browser=lambda url: opened_urls.append(url) or True)
        request = SitePublicationRequest(
            identity=SiteIdentityInput(site_title="ETS"),
            output_dir=RUNTIME_DIR,
            plays=(
                DramaticPlayInput(
                    play_slug="andromaque",
                    document=DramaticDocumentInput(source_path=RUNTIME_DIR / "andromaque.xml"),
                ),
            ),
        )
        messages: list[str] = []
        called: list[SitePublicationRequest] = []
        monkeypatch.setattr("ets.ui.tk.main_window.open_publication_dialog", lambda _parent: request)
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args, **kwargs: None)
        monkeypatch.setattr("tkinter.messagebox.showwarning", lambda *args, **kwargs: None)

        def _fake_build(payload: SitePublicationRequest) -> SiteBuildServiceResult:
            called.append(payload)
            return SiteBuildServiceResult(
                ok=True,
                output_dir=RUNTIME_DIR.resolve(),
                generated_pages=(RUNTIME_DIR / "index.html", RUNTIME_DIR / "plays" / "andromaque.html"),
                copied_assets=(),
                warnings=(),
                play_count=1,
                notice_count=1,
                message="ok",
                generated_page_relpaths=("index.html", "plays/andromaque.html"),
            )

        monkeypatch.setattr("ets.ui.tk.main_window.build_site_from_publication_request", _fake_build)
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda _title, message, **kwargs: messages.append(message))
        monkeypatch.setattr(window, "_open_publication_site_preview", lambda output_dir: opened_urls.append(str(output_dir)))

        window.action_build_publication_site()

        assert called == [request]
        assert messages
        assert opened_urls == [str(RUNTIME_DIR.resolve())]
        assert "Génération du site terminée." in messages[-1]
        assert "Pages générées: 2" in messages[-1]
    finally:
        root.destroy()


def test_action_build_publication_site_failure_shows_error(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        opened_urls: list[str] = []
        window = MainWindow(root, open_browser=lambda url: opened_urls.append(url) or True)
        request = SitePublicationRequest(
            identity=SiteIdentityInput(site_title="ETS"),
            output_dir=RUNTIME_DIR,
            plays=(
                DramaticPlayInput(
                    play_slug="andromaque",
                    document=DramaticDocumentInput(source_path=RUNTIME_DIR / "andromaque.xml"),
                ),
            ),
        )
        errors: list[str] = []
        monkeypatch.setattr("ets.ui.tk.main_window.open_publication_dialog", lambda _parent: request)
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args, **kwargs: None)
        monkeypatch.setattr("tkinter.messagebox.showwarning", lambda *args, **kwargs: None)
        monkeypatch.setattr(
            "ets.ui.tk.main_window.build_site_from_publication_request",
            lambda _request: SiteBuildServiceResult(
                ok=False,
                message="Site build configuration failed.",
                error_code="E_SITE_CONFIG",
                error_detail="Invalid site configuration: 'site_title' is required.",
            ),
        )
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda _title, message, **kwargs: errors.append(message))
        monkeypatch.setattr(window, "_open_publication_site_preview", lambda output_dir: opened_urls.append(str(output_dir)))

        window.action_build_publication_site()

        assert errors
        assert opened_urls == []
        assert "Site build configuration failed." in errors[-1]
        assert "site_title" in errors[-1]
    finally:
        root.destroy()


def test_action_build_publication_site_surfaces_warnings(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        opened_urls: list[str] = []
        window = MainWindow(root, open_browser=lambda url: opened_urls.append(url) or True)
        request = SitePublicationRequest(
            identity=SiteIdentityInput(site_title="ETS"),
            output_dir=RUNTIME_DIR,
            plays=(
                DramaticPlayInput(
                    play_slug="andromaque",
                    document=DramaticDocumentInput(source_path=RUNTIME_DIR / "andromaque.xml"),
                ),
            ),
        )
        warnings: list[str] = []
        called: list[SitePublicationRequest] = []
        monkeypatch.setattr("ets.ui.tk.main_window.open_publication_dialog", lambda _parent: request)
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args, **kwargs: None)
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args, **kwargs: None)

        def _fake_build(payload: SitePublicationRequest) -> SiteBuildServiceResult:
            called.append(payload)
            return SiteBuildServiceResult(
                ok=True,
                output_dir=RUNTIME_DIR.resolve(),
                generated_pages=(RUNTIME_DIR / "index.html",),
                copied_assets=(),
                warnings=("Configured play_notice_map entry references unknown play slug.",),
                play_count=2,
                notice_count=1,
                message="ok",
                generated_page_relpaths=("index.html",),
            )

        monkeypatch.setattr("ets.ui.tk.main_window.build_site_from_publication_request", _fake_build)
        monkeypatch.setattr("tkinter.messagebox.showwarning", lambda _title, message, **kwargs: warnings.append(message))
        monkeypatch.setattr(window, "_open_publication_site_preview", lambda output_dir: opened_urls.append(str(output_dir)))

        window.action_build_publication_site()

        assert called == [request]
        assert warnings
        assert opened_urls == [str(RUNTIME_DIR.resolve())]
        assert "Avertissements" in warnings[-1]
        assert "unknown play slug" in warnings[-1]
    finally:
        root.destroy()


def test_action_build_publication_site_cancelled_dialog_does_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        called: list[str] = []
        monkeypatch.setattr("ets.ui.tk.main_window.open_publication_dialog", lambda _parent: None)
        monkeypatch.setattr(
            "ets.ui.tk.main_window.build_site_from_publication_request",
            lambda _request: called.append("service") or SiteBuildServiceResult(ok=False),
        )
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args, **kwargs: called.append("info"))
        monkeypatch.setattr("tkinter.messagebox.showwarning", lambda *args, **kwargs: called.append("warn"))
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args, **kwargs: called.append("error"))

        window.action_build_publication_site()

        assert called == []
    finally:
        root.destroy()


def test_publication_dialog_builds_rich_request_object(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        runtime = RUNTIME_DIR / f"publication_dialog_{uuid4().hex}"
        runtime.mkdir(parents=True, exist_ok=True)
        dramatic_a1 = runtime / "andromaque.xml"
        dramatic_b1 = runtime / "berenice.xml"
        notice_play = runtime / "andromaque_notice.xml"
        preface_play = runtime / "andromaque_preface.xml"
        dramatis_play = runtime / "andromaque_dramatis.xml"
        home_page_tei = runtime / "home_page.xml"
        general_intro = runtime / "introduction_generale.xml"
        logo = runtime / "logo.png"
        asset_dir = runtime / "assets"
        output_dir = runtime / "site_out"
        for path in (dramatic_a1, dramatic_b1, notice_play, preface_play, dramatis_play, home_page_tei, general_intro, logo):
            path.write_text("<xml/>", encoding="utf-8")
        asset_dir.mkdir(parents=True, exist_ok=True)

        dialog = PublicationDialog(root)
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args, **kwargs: None)
        dialog.vars.author_name.set("Jean Racine")
        dialog.vars.corpus_title.set("Théâtre complet")
        dialog.vars.scientific_editor.set("Caroline Labrune")
        dialog.vars.output_dir.set(str(output_dir))
        dialog.vars.home_page_tei.set(str(home_page_tei))
        dialog.vars.general_intro_tei.set(str(general_intro))
        dialog.vars.asset_directory.set(str(asset_dir))
        dialog._logo_paths = [logo]
        dialog.logo_list.insert(tk.END, str(logo))
        dialog._append_play_from_path(dramatic_a1)
        dialog._append_play_from_path(dramatic_b1)
        dialog._play_entries[0].notice_xml_path = notice_play.resolve()
        dialog._play_entries[0].preface_xml_path = preface_play.resolve()
        dialog._play_entries[0].dramatis_xml_path = dramatis_play.resolve()
        dialog._refresh_dramatic_list()
        dialog._sync_play_order_from_entries()
        dialog.play_order_list.delete(0, tk.END)
        dialog.play_order_list.insert(tk.END, "berenice")
        dialog.play_order_list.insert(tk.END, "andromaque")
        dialog.vars.show_xml_download.set(True)
        dialog.vars.publish_notices.set(True)
        dialog.vars.publish_prefaces.set(True)

        dialog._on_validate()

        request = dialog.result
        assert request is not None
        assert request.identity.site_title == "Théâtre complet"
        assert request.identity.site_subtitle == "Jean Racine"
        assert request.identity.editor == "Caroline Labrune"
        assert request.identity.project_name == "jean-racine-theatre-complet"
        assert request.general_notice_slug == "introduction-generale"
        assert request.play_order == ("berenice", "andromaque")
        assert len(request.plays) == 2
        assert request.plays[0].play_slug == "berenice"
        assert request.plays[1].play_slug == "andromaque"
        assert request.plays[1].document.source_path == dramatic_a1
        assert request.plays[1].related_notice_path == notice_play.resolve()
        assert request.plays[1].preface_xml_path == preface_play.resolve()
        assert request.plays[1].dramatis_xml_path == dramatis_play.resolve()
        assert len(request.notices) == 4
        assert request.assets.logo_files == (logo,)
        assert request.assets.asset_directories == (asset_dir.resolve(),)
        assert request.play_notice_map
        assert request.play_preface_map
        assert request.play_dramatis_map
        assert request.publish_notices is True
        assert request.publish_prefaces is True
    finally:
        root.destroy()


def test_publication_dialog_multiselect_without_slug_creates_distinct_plays(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        runtime = RUNTIME_DIR / f"publication_dialog_multiselect_{uuid4().hex}"
        runtime.mkdir(parents=True, exist_ok=True)
        andromaque = runtime / "andromaque.xml"
        berenice = runtime / "berenice.xml"
        andromaque.write_text("<xml/>", encoding="utf-8")
        berenice.write_text("<xml/>", encoding="utf-8")

        dialog = PublicationDialog(root)
        errors: list[str] = []
        monkeypatch.setattr(
            "tkinter.filedialog.askopenfilenames",
            lambda **kwargs: (str(andromaque), str(berenice)),
        )
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda _title, message, **kwargs: errors.append(message))

        dialog._add_dramatic_files()

        assert not errors
        assert [item.play_slug for item in dialog._play_entries] == ["andromaque", "berenice"]

        dialog.vars.corpus_title.set("Théâtre complet")
        dialog.vars.output_dir.set(str(runtime / "site_out"))
        request = dialog._build_request()
        assert len(request.plays) == 2
        assert request.plays[0].play_slug == "andromaque"
        assert request.plays[0].document.source_path == andromaque.resolve()
        assert request.plays[1].play_slug == "berenice"
        assert request.plays[1].document.source_path == berenice.resolve()
        dialog.destroy()
    finally:
        root.destroy()


def test_publication_dialog_each_play_keeps_single_dramatic_xml_source(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        runtime = RUNTIME_DIR / f"publication_dialog_single_xml_per_play_{uuid4().hex}"
        runtime.mkdir(parents=True, exist_ok=True)
        andromaque = runtime / "andromaque.xml"
        andromaque_revised = runtime / "andromaque_revised.xml"
        andromaque.write_text("<xml/>", encoding="utf-8")
        andromaque_revised.write_text("<xml/>", encoding="utf-8")

        dialog = PublicationDialog(root)
        monkeypatch.setattr(
            "tkinter.filedialog.askopenfilenames",
            lambda **kwargs: (str(andromaque),),
        )
        monkeypatch.setattr(
            "tkinter.filedialog.askopenfilename",
            lambda **kwargs: str(andromaque_revised),
        )
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args, **kwargs: None)

        dialog._add_dramatic_files()
        dialog.dramatic_list.selection_set(0)
        dialog._replace_dramatic_for_selected_play()

        dialog.vars.corpus_title.set("Theatre complet")
        dialog.vars.output_dir.set(str(runtime / "site_out"))
        request = dialog._build_request()

        assert len(request.plays) == 1
        assert request.plays[0].play_slug == "andromaque"
        assert request.plays[0].document.source_path == andromaque_revised.resolve()
        dialog.destroy()
    finally:
        root.destroy()


def test_publication_dialog_attach_and_clear_preface_and_dramatis(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        runtime = RUNTIME_DIR / f"publication_dialog_preface_dramatis_{uuid4().hex}"
        runtime.mkdir(parents=True, exist_ok=True)
        andromaque = runtime / "andromaque.xml"
        preface = runtime / "preface.xml"
        dramatis = runtime / "dramatis.xml"
        andromaque.write_text("<xml/>", encoding="utf-8")
        preface.write_text("<xml/>", encoding="utf-8")
        dramatis.write_text("<xml/>", encoding="utf-8")

        dialog = PublicationDialog(root)
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args, **kwargs: None)
        dialog._append_play_from_path(andromaque)
        dialog._refresh_dramatic_list()
        dialog.dramatic_list.selection_set(0)

        monkeypatch.setattr("tkinter.filedialog.askopenfilename", lambda **kwargs: str(preface))
        dialog._attach_preface_to_selected_play()
        assert dialog._play_entries[0].preface_xml_path == preface.resolve()
        assert "preface: preface.xml" in dialog.dramatic_list.get(0)

        monkeypatch.setattr("tkinter.filedialog.askopenfilename", lambda **kwargs: str(dramatis))
        dialog._attach_dramatis_to_selected_play()
        assert dialog._play_entries[0].dramatis_xml_path == dramatis.resolve()
        assert "dramatis: dramatis.xml" in dialog.dramatic_list.get(0)

        dialog._clear_preface_for_selected_play()
        dialog._clear_dramatis_for_selected_play()
        assert dialog._play_entries[0].preface_xml_path is None
        assert dialog._play_entries[0].dramatis_xml_path is None
        assert "preface: -" in dialog.dramatic_list.get(0)
        assert "dramatis: -" in dialog.dramatic_list.get(0)
        dialog.destroy()
    finally:
        root.destroy()


def test_publication_dialog_attach_notice_xml_non_regression(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        runtime = RUNTIME_DIR / f"publication_dialog_notice_xml_non_reg_{uuid4().hex}"
        runtime.mkdir(parents=True, exist_ok=True)
        andromaque = runtime / "andromaque.xml"
        notice = runtime / "notice.xml"
        andromaque.write_text("<xml/>", encoding="utf-8")
        notice.write_text("<xml/>", encoding="utf-8")

        dialog = PublicationDialog(root)
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args, **kwargs: None)
        dialog._append_play_from_path(andromaque)
        dialog._refresh_dramatic_list()
        dialog.dramatic_list.selection_set(0)
        monkeypatch.setattr("tkinter.filedialog.askopenfilename", lambda **kwargs: str(notice))

        dialog._attach_notice_to_selected_play()

        assert dialog._play_entries[0].notice_xml_path == notice.resolve()
        assert "notice: notice.xml" in dialog.dramatic_list.get(0)
        dialog.destroy()
    finally:
        root.destroy()


def test_publication_dialog_attach_notice_docx_with_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        runtime = RUNTIME_DIR / f"publication_dialog_notice_docx_warn_{uuid4().hex}"
        runtime.mkdir(parents=True, exist_ok=True)
        andromaque = runtime / "andromaque.xml"
        notice_docx = runtime / "notice.docx"
        andromaque.write_text("<xml/>", encoding="utf-8")
        notice_docx.write_text("placeholder", encoding="utf-8")

        dialog = PublicationDialog(root)
        dialog._append_play_from_path(andromaque)
        dialog._refresh_dramatic_list()
        dialog.dramatic_list.selection_set(0)

        warning_report = ValidationReport.from_messages(
            [
                ValidationMessage(
                    severity=ValidationSeverity.WARNING,
                    code="MISSING_BIBLIO_SECTION",
                    message="Rubrique Bibliographie absente.",
                )
            ]
        )
        monkeypatch.setattr(
            dialog._editorial_import_service,
            "inspect_source_for_ui",
            lambda path, source_kind: EditorialImportResult(
                source_path=path,
                source_kind=source_kind,
                report=warning_report,
                tei_xml="<TEI/>",
            ),
        )
        warnings: list[str] = []
        monkeypatch.setattr("tkinter.filedialog.askopenfilename", lambda **kwargs: str(notice_docx))
        monkeypatch.setattr("tkinter.messagebox.showwarning", lambda _title, message, **kwargs: warnings.append(message))
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args, **kwargs: None)

        dialog._attach_notice_to_selected_play()

        assert dialog._play_entries[0].notice_xml_path == notice_docx.resolve()
        assert warnings
        dialog.destroy()
    finally:
        root.destroy()


def test_publication_dialog_attach_notice_docx_blocking_error_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        runtime = RUNTIME_DIR / f"publication_dialog_notice_docx_error_{uuid4().hex}"
        runtime.mkdir(parents=True, exist_ok=True)
        andromaque = runtime / "andromaque.xml"
        notice_docx = runtime / "notice.docx"
        andromaque.write_text("<xml/>", encoding="utf-8")
        notice_docx.write_text("placeholder", encoding="utf-8")

        dialog = PublicationDialog(root)
        dialog._append_play_from_path(andromaque)
        dialog._refresh_dramatic_list()
        dialog.dramatic_list.selection_set(0)

        error_report = ValidationReport.from_messages(
            [
                ValidationMessage(
                    severity=ValidationSeverity.ERROR,
                    code="UNKNOWN_PARAGRAPH_STYLE",
                    message="Style de paragraphe non autorise.",
                )
            ]
        )
        monkeypatch.setattr(
            dialog._editorial_import_service,
            "inspect_source_for_ui",
            lambda path, source_kind: EditorialImportResult(
                source_path=path,
                source_kind=source_kind,
                report=error_report,
                tei_xml=None,
            ),
        )
        errors: list[str] = []
        monkeypatch.setattr("tkinter.filedialog.askopenfilename", lambda **kwargs: str(notice_docx))
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda _title, message, **kwargs: errors.append(message))

        dialog._attach_notice_to_selected_play()

        assert dialog._play_entries[0].notice_xml_path is None
        assert errors
        dialog.destroy()
    finally:
        root.destroy()


def test_publication_dialog_choose_home_page_docx_validates_before_setting(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        runtime = RUNTIME_DIR / f"publication_dialog_home_docx_{uuid4().hex}"
        runtime.mkdir(parents=True, exist_ok=True)
        home_docx = runtime / "home.docx"
        home_docx.write_text("placeholder", encoding="utf-8")

        dialog = PublicationDialog(root)
        valid_report = ValidationReport.from_messages([])
        monkeypatch.setattr("tkinter.filedialog.askopenfilename", lambda **kwargs: str(home_docx))
        monkeypatch.setattr(
            dialog._editorial_import_service,
            "inspect_source_for_ui",
            lambda path, source_kind: EditorialImportResult(
                source_path=path,
                source_kind=source_kind,
                report=valid_report,
                tei_xml="<TEI/>",
            ),
        )

        dialog._choose_home_page_tei()

        assert dialog.vars.home_page_tei.get() == str(home_docx.resolve())
        dialog.destroy()
    finally:
        root.destroy()


def test_publication_dialog_save_and_load_config_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        runtime = RUNTIME_DIR / f"publication_dialog_config_{uuid4().hex}"
        runtime.mkdir(parents=True, exist_ok=True)
        config_path = runtime / "publication_config.json"

        dramatic_a1 = runtime / "andromaque.xml"
        dramatic_b1 = runtime / "berenice.xml"
        notice_play = runtime / "notice_andromaque.xml"
        preface_play = runtime / "preface_andromaque.xml"
        dramatis_play = runtime / "dramatis_andromaque.xml"
        home_page_tei = runtime / "home_page.xml"
        general_intro = runtime / "general_intro.xml"
        logo = runtime / "logo.png"
        asset_dir = runtime / "assets"
        output_dir = runtime / "site_out"
        for path in (
            dramatic_a1,
            dramatic_b1,
            notice_play,
            preface_play,
            dramatis_play,
            home_page_tei,
            general_intro,
            logo,
        ):
            path.write_text("<xml/>", encoding="utf-8")
        asset_dir.mkdir(parents=True, exist_ok=True)

        infos: list[str] = []
        errors: list[str] = []
        dialog = PublicationDialog(root)
        monkeypatch.setattr("tkinter.filedialog.asksaveasfilename", lambda **kwargs: str(config_path))
        monkeypatch.setattr("tkinter.filedialog.askopenfilename", lambda **kwargs: str(config_path))
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda _title, message, **kwargs: infos.append(message))
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda _title, message, **kwargs: errors.append(message))

        dialog.vars.author_name.set("Jean Racine")
        dialog.vars.corpus_title.set("Théâtre complet")
        dialog.vars.scientific_editor.set("Caroline Labrune")
        dialog.vars.output_dir.set(str(output_dir))
        dialog.vars.home_page_tei.set(str(home_page_tei))
        dialog.vars.general_intro_tei.set(str(general_intro))
        dialog.vars.asset_directory.set(str(asset_dir))
        dialog._logo_paths = [logo]
        dialog.logo_list.insert(tk.END, str(logo))
        dialog._append_play_from_path(dramatic_a1)
        dialog._append_play_from_path(dramatic_b1)
        dialog._play_entries[0].notice_xml_path = notice_play.resolve()
        dialog._play_entries[0].preface_xml_path = preface_play.resolve()
        dialog._play_entries[0].dramatis_xml_path = dramatis_play.resolve()
        dialog._refresh_dramatic_list()
        dialog._sync_play_order_from_entries()
        dialog.play_order_list.delete(0, tk.END)
        dialog.play_order_list.insert(tk.END, "berenice")
        dialog.play_order_list.insert(tk.END, "andromaque")
        dialog.vars.show_xml_download.set(True)
        dialog.vars.publish_prefaces.set(True)

        dialog._on_save_config()
        assert config_path.exists()
        saved_payload = json.loads(config_path.read_text(encoding="utf-8"))
        assert saved_payload["schema"] == "ets.site_publication_dialog_config"
        assert saved_payload["version"] == 3

        dialog.vars.corpus_title.set("Autre")
        dialog.vars.author_name.set("")
        dialog.vars.scientific_editor.set("")
        dialog.vars.home_page_tei.set("")
        dialog.vars.general_intro_tei.set("")
        dialog._play_entries.clear()
        dialog.dramatic_list.delete(0, tk.END)
        dialog.play_order_list.delete(0, tk.END)
        dialog._logo_paths.clear()
        dialog.logo_list.delete(0, tk.END)
        dialog.vars.output_dir.set("")

        dialog._on_load_config()

        assert not errors
        assert dialog.vars.author_name.get() == "Jean Racine"
        assert dialog.vars.corpus_title.get() == "Théâtre complet"
        assert dialog.vars.scientific_editor.get() == "Caroline Labrune"
        assert dialog.vars.home_page_tei.get() == str(home_page_tei.resolve())
        assert dialog.vars.general_intro_tei.get() == str(general_intro.resolve())
        assert dialog.vars.output_dir.get() == str(output_dir.resolve())
        assert dialog.vars.asset_directory.get() == str(asset_dir.resolve())
        assert dialog._logo_paths == [logo.resolve()]
        assert dialog._play_order_items() == ["berenice", "andromaque"]
        assert len(dialog._play_entries) == 2
        assert dialog._play_entries[0].notice_xml_path == notice_play.resolve()
        assert dialog._play_entries[0].preface_xml_path == preface_play.resolve()
        assert dialog._play_entries[0].dramatis_xml_path == dramatis_play.resolve()
        assert infos
        dialog.destroy()
    finally:
        root.destroy()


def test_publication_dialog_load_save_config_cancelled_paths_do_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        dialog = PublicationDialog(root)
        infos: list[str] = []
        errors: list[str] = []
        monkeypatch.setattr("tkinter.filedialog.asksaveasfilename", lambda **kwargs: "")
        monkeypatch.setattr("tkinter.filedialog.askopenfilename", lambda **kwargs: "")
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda _title, message, **kwargs: infos.append(message))
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda _title, message, **kwargs: errors.append(message))

        dialog._on_save_config()
        dialog._on_load_config()

        assert infos == []
        assert errors == []
        dialog.destroy()
    finally:
        root.destroy()


def test_publication_dialog_load_config_invalid_json_shows_error(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        runtime = RUNTIME_DIR / f"publication_dialog_invalid_json_{uuid4().hex}"
        runtime.mkdir(parents=True, exist_ok=True)
        bad_config = runtime / "invalid.json"
        bad_config.write_text("{", encoding="utf-8")

        dialog = PublicationDialog(root)
        errors: list[str] = []
        monkeypatch.setattr("tkinter.filedialog.askopenfilename", lambda **kwargs: str(bad_config))
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda _title, message, **kwargs: errors.append(message))

        dialog._on_load_config()

        assert errors
        assert "json" in errors[-1].lower()
        dialog.destroy()
    finally:
        root.destroy()


def test_publication_dialog_load_config_invalid_structure_shows_error(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        runtime = RUNTIME_DIR / f"publication_dialog_invalid_structure_{uuid4().hex}"
        runtime.mkdir(parents=True, exist_ok=True)
        bad_config = runtime / "invalid_structure.json"
        bad_config.write_text(json.dumps({"version": 1}, ensure_ascii=False, indent=2), encoding="utf-8")

        dialog = PublicationDialog(root)
        errors: list[str] = []
        monkeypatch.setattr("tkinter.filedialog.askopenfilename", lambda **kwargs: str(bad_config))
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda _title, message, **kwargs: errors.append(message))

        dialog._on_load_config()

        assert errors
        assert "schema" in errors[-1].lower()
        dialog.destroy()
    finally:
        root.destroy()


def test_publication_dialog_validation_error_is_non_blocking(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        dialog = PublicationDialog(root)
        errors: list[str] = []
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda _title, message, **kwargs: errors.append(message))

        dialog._on_validate()

        assert errors
        assert "titre de l'œuvre/corpus" in errors[-1].lower()
        assert dialog.result is None
        dialog.destroy()
    finally:
        root.destroy()


def _collect_widget_texts(widget: tk.Misc) -> list[str]:
    texts: list[str] = []
    if hasattr(widget, "cget"):
        try:
            text = widget.cget("text")
        except tk.TclError:
            text = ""
        if isinstance(text, str) and text:
            texts.append(text)
    for child in widget.winfo_children():
        texts.extend(_collect_widget_texts(child))
    return texts


def test_publication_dialog_uses_scrollable_body_and_fixed_action_bar() -> None:
    root = _make_root()
    try:
        dialog = PublicationDialog(root)
        root.update_idletasks()

        assert isinstance(dialog._scroll_canvas, tk.Canvas)
        assert dialog._scroll_canvas.master is not dialog.action_bar
        assert dialog.action_bar.master is dialog
        assert dialog.action_bar.grid_info()["row"] == 1
        dialog.destroy()
    finally:
        root.destroy()


def test_publication_dialog_contains_clarified_labels_and_hints() -> None:
    root = _make_root()
    try:
        dialog = PublicationDialog(root)
        root.update_idletasks()
        all_text = "\n".join(_collect_widget_texts(dialog))

        assert "Metadonnees generales" in all_text
        assert "Auteur" in all_text
        assert "Titre de l'oeuvre/corpus" in all_text
        assert "Responsable scientifique" in all_text
        assert "Source accueil (XML-TEI ou DOCX)" in all_text
        assert "Introduction generale" in all_text
        assert "Source introduction generale (XML-TEI ou DOCX)" in all_text
        assert "Corpus de pieces" in all_text
        assert "Ajouter piece XML" in all_text
        assert "Associer notice (XML ou DOCX)" in all_text
        assert "Associer preface (XML ou DOCX)" in all_text
        assert "Associer Dramatis XML" in all_text
        assert "Publier les prefaces" in all_text
        assert "Regle: 1 XML dramatique = 1 piece complete" in all_text
        assert "Ordre de navigation des pieces" in all_text
        assert "Dossier d'assets" in all_text
        assert "Charger config..." in all_text
        assert "Enregistrer config..." in all_text
        assert "Slug de piece" not in all_text
        assert "Projet" not in all_text
        assert "Credits" not in all_text
        assert "notice maitre" not in all_text.lower()
        assert "notices additionnelles" not in all_text.lower()
        dialog.destroy()
    finally:
        root.destroy()


def test_load_annotations_action_updates_state_and_panel(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        fixture = Path(__file__).resolve().parents[1] / "fixtures" / "annotations" / "berenice_1_1" / "annotations.json"
        monkeypatch.setattr("tkinter.filedialog.askopenfilename", lambda **kwargs: str(fixture))
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args, **kwargs: None)

        window.action_load_annotations()

        assert len(window.state.annotations.annotations) == 3
        assert window.outputs.annotation_row_count() == 3
        assert window.state.annotations_path == fixture
        first_anchor = window.outputs.annotations_panel.tree.item("n1", "values")[2]
        assert str(first_anchor).startswith("Acte 1, scene 1, vers")
    finally:
        root.destroy()


def test_generate_tei_with_loaded_annotations_stores_enriched_tei() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        fixture_dir = _annotations_fixture_dir()
        window.state.config = load_config(fixture_dir / "config.json")
        window.editor.set_text((fixture_dir / "input.txt").read_text(encoding="utf-8"))
        window._set_annotations(load_annotations(fixture_dir / "annotations.json"), fixture_dir / "annotations.json")

        window.action_generate_tei()

        assert window.state.tei_xml is not None
        assert "<note " in window.state.tei_xml
        assert "<note " in window.outputs.get_tei()
    finally:
        root.destroy()


def test_preview_html_uses_enriched_tei_when_annotations_are_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        fixture_dir = _annotations_fixture_dir()
        window.state.config = load_config(fixture_dir / "config.json")
        window.editor.set_text((fixture_dir / "input.txt").read_text(encoding="utf-8"))
        window._set_annotations(load_annotations(fixture_dir / "annotations.json"), fixture_dir / "annotations.json")
        monkeypatch.setattr(window._preview_server, "publish_html", lambda html: "http://localhost/preview")
        monkeypatch.setattr(window, "_open_browser", lambda url: True)

        window.action_generate_tei()
        window.action_preview_html()

        assert window.state.html_preview is not None
        assert 'class="note-call"' in window.state.html_preview
        assert 'class="notes"' in window.state.html_preview
    finally:
        root.destroy()


def test_export_html_uses_current_enriched_tei(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        fixture_dir = _annotations_fixture_dir()
        window.state.config = load_config(fixture_dir / "config.json")
        window.editor.set_text((fixture_dir / "input.txt").read_text(encoding="utf-8"))
        window._set_annotations(load_annotations(fixture_dir / "annotations.json"), fixture_dir / "annotations.json")

        out_path = RUNTIME_DIR / f"export_html_{uuid4().hex}.html"
        monkeypatch.setattr("tkinter.filedialog.asksaveasfilename", lambda **kwargs: str(out_path))
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args, **kwargs: None)
        captured: list[str] = []

        def _fake_export(content: str, output_path: str | Path) -> Path:
            captured.append(content)
            path = Path(output_path)
            path.write_text(content, encoding="utf-8")
            return path

        monkeypatch.setattr("ets.ui.tk.main_window.export_html", _fake_export)
        window.action_export_html()

        assert captured
        assert 'class="note-call"' in captured[0]
        assert 'class="notes"' in captured[0]
    finally:
        root.destroy()


def test_generate_tei_without_annotations_remains_plain() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        fixture_dir = _annotations_fixture_dir()
        window.state.config = load_config(fixture_dir / "config.json")
        window.editor.set_text((fixture_dir / "input.txt").read_text(encoding="utf-8"))

        window.action_generate_tei()

        assert window.state.tei_xml is not None
        assert "<note " not in window.state.tei_xml
    finally:
        root.destroy()


def test_enrichment_failure_surfaces_diagnostics_without_raw_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        fixture_dir = _annotations_fixture_dir()
        window.state.config = load_config(fixture_dir / "config.json")
        window.editor.set_text((fixture_dir / "input.txt").read_text(encoding="utf-8"))
        window._set_annotations(load_annotations(fixture_dir / "annotations.json"), fixture_dir / "annotations.json")

        monkeypatch.setattr(
            "ets.ui.tk.main_window.enrich_tei_with_annotations",
            lambda tei_xml, annotations: GenerationResult(
                ok=False,
                tei_xml=None,
                diagnostics=[AppDiagnostic(level="ERROR", code="E_TEST_ENRICH", message="Enrichment failed")],
                message="Enrichment failed",
            ),
        )
        errors: list[str] = []
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda title, message, **kwargs: errors.append(message))

        window.action_generate_tei()

        assert window.state.tei_xml is None
        assert window.outputs.get_tei().strip() == ""
        assert any(item.code == "E_TEST_ENRICH" for item in window.state.diagnostics)
        assert errors
    finally:
        root.destroy()


def test_annotation_crud_actions_update_state(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        fixture_dir = _load_annotation_fixture_in_window(window)
        fixture = fixture_dir / "annotations.json"
        collection = load_annotations(fixture)
        window._set_annotations(collection, fixture)
        window.editor.text.mark_set("insert", "13.0")

        add_payload = {
            "id": "n4",
            "type": "explicative",
            "anchor": {"kind": "line", "act": "1", "scene": "1", "line": "1"},
            "content": "ajout",
            "status": "draft",
            "keywords": [],
        }
        captured_add_kwargs: dict[str, object] = {}

        def _fake_add_dialog(*args, **kwargs):  # type: ignore[no-untyped-def]
            captured_add_kwargs.update(kwargs)
            return add_payload

        monkeypatch.setattr("ets.ui.tk.main_window.open_annotation_dialog", _fake_add_dialog)
        window.action_add_annotation()
        assert captured_add_kwargs.get("id_readonly") is True
        assert isinstance(captured_add_kwargs.get("initial"), dict)
        assert captured_add_kwargs["initial"]["id"] == "n4"  # type: ignore[index]
        assert any(item.id == "n4" for item in window.state.annotations.annotations)

        edit_payload = {
            "id": "n4",
            "type": "dramaturgique",
            "anchor": {"kind": "line", "act": "1", "scene": "1", "line": "1"},
            "content": "modif",
            "status": "reviewed",
            "keywords": [],
        }
        captured_edit_kwargs: dict[str, object] = {}

        def _fake_edit_dialog(*args, **kwargs):  # type: ignore[no-untyped-def]
            captured_edit_kwargs.update(kwargs)
            return edit_payload

        window.outputs.annotations_panel.tree.selection_set("n4")
        monkeypatch.setattr("ets.ui.tk.main_window.open_annotation_dialog", _fake_edit_dialog)
        window.action_edit_annotation()
        assert captured_edit_kwargs.get("id_readonly") is True
        assert captured_edit_kwargs["initial"]["id"] == "n4"  # type: ignore[index]
        edited = [item for item in window.state.annotations.annotations if item.id == "n4"][0]
        assert edited.type == "dramaturgique"
        assert edited.content == "modif"
        assert edited.id == "n4"

        monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *args, **kwargs: True)
        window.outputs.annotations_panel.tree.selection_set("n4")
        window.action_delete_annotation()
        assert all(item.id != "n4" for item in window.state.annotations.annotations)
    finally:
        root.destroy()


def test_load_annotations_refreshes_editor_annotation_highlights(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "annotations" / "berenice_1_1"
        window.state.config = load_config(fixture_dir / "config.json")
        window.editor.set_text((fixture_dir / "input.txt").read_text(encoding="utf-8"))

        calls: list[tuple[list[int], int | None]] = []
        monkeypatch.setattr(
            window.editor,
            "highlight_annotation_lines",
            lambda lines, focus_line=None: calls.append((list(lines), focus_line)),
        )
        monkeypatch.setattr("tkinter.filedialog.askopenfilename", lambda **kwargs: str(fixture_dir / "annotations.json"))
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args, **kwargs: None)

        window.action_load_annotations()

        assert calls
        lines, focus = calls[-1]
        assert 13 in lines
        assert 19 in lines
        assert 22 in lines
        assert focus is None
    finally:
        root.destroy()


def test_annotation_crud_triggers_highlight_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        fixture_dir = _load_annotation_fixture_in_window(window)
        collection = load_annotations(fixture_dir / "annotations.json")
        refresh_calls: list[str] = []
        monkeypatch.setattr(window, "_refresh_annotation_highlights", lambda *args, **kwargs: refresh_calls.append("refresh"))

        window._set_annotations(collection, fixture_dir / "annotations.json")
        assert refresh_calls
        refresh_calls.clear()

        add_payload = {
            "id": "n4",
            "type": "explicative",
            "anchor": {"kind": "line", "act": "1", "scene": "1", "line": "1"},
            "content": "ajout",
            "status": "draft",
            "keywords": [],
        }
        window.editor.text.mark_set("insert", "13.0")
        monkeypatch.setattr("ets.ui.tk.main_window.open_annotation_dialog", lambda *args, **kwargs: add_payload)
        window.action_add_annotation()
        assert refresh_calls
        refresh_calls.clear()

        edit_payload = {
            "id": "n4",
            "type": "dramaturgique",
            "anchor": {"kind": "line", "act": "1", "scene": "1", "line": "1"},
            "content": "modif",
            "status": "reviewed",
            "keywords": [],
        }
        window.outputs.annotations_panel.tree.selection_set("n4")
        monkeypatch.setattr("ets.ui.tk.main_window.open_annotation_dialog", lambda *args, **kwargs: edit_payload)
        window.action_edit_annotation()
        assert refresh_calls
        refresh_calls.clear()

        monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *args, **kwargs: True)
        window.outputs.annotations_panel.tree.selection_set("n4")
        window.action_delete_annotation()
        assert refresh_calls
    finally:
        root.destroy()


def test_add_annotation_prefills_anchor_from_current_verse_line(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        _load_annotation_fixture_in_window(window)
        window.editor.text.mark_set("insert", "14.0")
        captured: dict[str, object] = {}

        def _fake_dialog(*args, **kwargs):  # type: ignore[no-untyped-def]
            captured.update(kwargs)
            return None

        monkeypatch.setattr("ets.ui.tk.main_window.open_annotation_dialog", _fake_dialog)
        window.action_add_annotation()

        initial = captured["initial"]  # type: ignore[index]
        assert isinstance(initial, dict)
        assert initial["anchor"] == {"kind": "line", "act": "1", "scene": "1", "line": "1"}  # type: ignore[index]
    finally:
        root.destroy()


def test_add_annotation_prefills_anchor_from_current_stage_line(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        _load_annotation_fixture_in_window(window)
        window.editor.text.mark_set("insert", "17.0")
        captured: dict[str, object] = {}

        def _fake_dialog(*args, **kwargs):  # type: ignore[no-untyped-def]
            captured.update(kwargs)
            return None

        monkeypatch.setattr("ets.ui.tk.main_window.open_annotation_dialog", _fake_dialog)
        window.action_add_annotation()

        initial = captured["initial"]  # type: ignore[index]
        assert isinstance(initial, dict)
        assert initial["anchor"] == {"kind": "stage", "act": "1", "scene": "1", "stage_index": 1}  # type: ignore[index]
    finally:
        root.destroy()


def test_add_annotation_on_non_annotatable_line_shows_message_and_does_not_open_dialog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        _load_annotation_fixture_in_window(window)
        window.editor.text.mark_set("insert", "10.0")
        infos: list[str] = []
        opened: list[bool] = []
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda _title, message, **kwargs: infos.append(message))
        monkeypatch.setattr(
            "ets.ui.tk.main_window.open_annotation_dialog",
            lambda *args, **kwargs: opened.append(True) or None,
        )

        window.action_add_annotation()

        assert infos
        assert "ne correspond pas a un vers" in infos[-1]
        assert opened == []
    finally:
        root.destroy()


def test_add_annotation_from_editor_position_saves_canonical_anchor(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        fixture_dir = _load_annotation_fixture_in_window(window)
        window._set_annotations(load_annotations(fixture_dir / "annotations.json"), fixture_dir / "annotations.json")
        window.editor.text.mark_set("insert", "14.0")

        def _fake_dialog(*args, **kwargs):  # type: ignore[no-untyped-def]
            initial = kwargs["initial"]
            assert isinstance(initial, dict)
            return {
                "id": initial["id"],
                "type": "explicative",
                "anchor": initial["anchor"],
                "content": "note auto",
                "status": "draft",
                "keywords": [],
            }

        monkeypatch.setattr("ets.ui.tk.main_window.open_annotation_dialog", _fake_dialog)
        window.action_add_annotation()

        added = next(item for item in window.state.annotations.annotations if item.id == "n4")
        assert added.anchor.kind == "line"
        assert added.anchor.act == "1"
        assert added.anchor.scene == "1"
        assert added.anchor.line == "1"
        serialized = window._annotation_to_payload(added)
        assert set(serialized["anchor"].keys()) == {"kind", "act", "scene", "line"}  # type: ignore[index]
    finally:
        root.destroy()


def test_selecting_line_annotation_navigates_editor_to_target_line(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "annotations" / "berenice_1_1"
        window.state.config = load_config(fixture_dir / "config.json")
        window.editor.set_text((fixture_dir / "input.txt").read_text(encoding="utf-8"))
        window._set_annotations(load_annotations(fixture_dir / "annotations.json"), fixture_dir / "annotations.json")

        seen: list[int] = []
        monkeypatch.setattr(window.editor, "go_to_line", lambda line: seen.append(line))
        window._on_annotation_selected("n1")
        assert seen[-1] == 13
    finally:
        root.destroy()


def test_selecting_line_range_annotation_focuses_first_line_and_range(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "annotations" / "berenice_1_1"
        window.state.config = load_config(fixture_dir / "config.json")
        window.editor.set_text((fixture_dir / "input.txt").read_text(encoding="utf-8"))
        window._set_annotations(load_annotations(fixture_dir / "annotations.json"), fixture_dir / "annotations.json")

        seen_go: list[int] = []
        seen_highlights: list[tuple[list[int], int | None]] = []
        monkeypatch.setattr(window.editor, "go_to_line", lambda line: seen_go.append(line))
        monkeypatch.setattr(
            window.editor,
            "highlight_annotation_lines",
            lambda lines, focus_line=None: seen_highlights.append((list(lines), focus_line)),
        )
        window._on_annotation_selected("n2")
        assert seen_go[-1] == 19
        highlighted_lines, focus_line = seen_highlights[-1]
        assert 19 in highlighted_lines
        assert 22 in highlighted_lines
        assert focus_line == 19
    finally:
        root.destroy()

