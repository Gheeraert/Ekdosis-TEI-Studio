from __future__ import annotations

import tkinter as tk
from pathlib import Path
from uuid import uuid4

import pytest

from ets.annotations import Annotation, AnnotationAnchor, AnnotationCollection
from ets.application import (
    AppDiagnostic,
    DramaticDocumentInput,
    DramaticPlayInput,
    GenerationResult,
    SiteIdentityInput,
    SitePublicationRequest,
    load_annotations,
    load_config,
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
        assert "Générer le site de publication…" in labels
    finally:
        root.destroy()


def test_action_build_publication_site_success_routes_through_service(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        request = SitePublicationRequest(
            identity=SiteIdentityInput(site_title="ETS"),
            output_dir=RUNTIME_DIR,
            plays=(
                DramaticPlayInput(
                    play_slug="andromaque",
                    documents=(DramaticDocumentInput(source_path=RUNTIME_DIR / "andromaque.xml"),),
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

        window.action_build_publication_site()

        assert called == [request]
        assert messages
        assert "Génération du site terminée." in messages[-1]
        assert "Pages générées: 2" in messages[-1]
    finally:
        root.destroy()


def test_action_build_publication_site_failure_shows_error(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        request = SitePublicationRequest(
            identity=SiteIdentityInput(site_title="ETS"),
            output_dir=RUNTIME_DIR,
            plays=(
                DramaticPlayInput(
                    play_slug="andromaque",
                    documents=(DramaticDocumentInput(source_path=RUNTIME_DIR / "andromaque.xml"),),
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

        window.action_build_publication_site()

        assert errors
        assert "Site build configuration failed." in errors[-1]
        assert "site_title" in errors[-1]
    finally:
        root.destroy()


def test_action_build_publication_site_surfaces_warnings(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        request = SitePublicationRequest(
            identity=SiteIdentityInput(site_title="ETS"),
            output_dir=RUNTIME_DIR,
            plays=(
                DramaticPlayInput(
                    play_slug="andromaque",
                    documents=(DramaticDocumentInput(source_path=RUNTIME_DIR / "andromaque.xml"),),
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

        window.action_build_publication_site()

        assert called == [request]
        assert warnings
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
        dramatic_a1 = runtime / "andromaque_A1.xml"
        dramatic_a2 = runtime / "andromaque_A2.xml"
        dramatic_b1 = runtime / "berenice_A1.xml"
        notice_master = runtime / "master_notice.xml"
        notice_intro = runtime / "notice_intro.xml"
        logo = runtime / "logo.png"
        asset_dir = runtime / "assets"
        output_dir = runtime / "site_out"
        for path in (dramatic_a1, dramatic_a2, dramatic_b1, notice_master, notice_intro, logo):
            path.write_text("<xml/>", encoding="utf-8")
        asset_dir.mkdir(parents=True, exist_ok=True)

        dialog = PublicationDialog(root)
        monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args, **kwargs: None)
        dialog.vars.site_title.set("ETS Publication")
        dialog.vars.site_subtitle.set("Corpus test")
        dialog.vars.project_name.set("ETS")
        dialog.vars.editor.set("Equipe ETS")
        dialog.vars.credits.set("Credits")
        dialog.homepage_intro.insert("1.0", "Introduction accueil")
        dialog.vars.output_dir.set(str(output_dir))
        dialog.vars.asset_directory.set(str(asset_dir))
        dialog.vars.master_notice.set(str(notice_master))
        dialog._notice_paths = [notice_intro]
        dialog.notice_list.insert(tk.END, str(notice_intro))
        dialog._logo_paths = [logo]
        dialog.logo_list.insert(tk.END, str(logo))
        dialog._add_dramatic_entries("andromaque", (dramatic_a1, dramatic_a2))
        dialog._add_dramatic_entries("berenice", (dramatic_b1,))
        dialog.play_order_list.delete(0, tk.END)
        dialog.play_order_list.insert(tk.END, "berenice")
        dialog.play_order_list.insert(tk.END, "andromaque")
        dialog.mapping_text.insert("1.0", "andromaque|master-notice\n")
        dialog.vars.show_xml_download.set(True)
        dialog.vars.publish_notices.set(True)

        dialog._on_validate()

        request = dialog.result
        assert request is not None
        assert request.identity.site_title == "ETS Publication"
        assert request.identity.homepage_intro == "Introduction accueil"
        assert request.play_order == ("berenice", "andromaque")
        assert len(request.plays) == 2
        assert request.plays[0].play_slug == "berenice"
        assert request.plays[1].play_slug == "andromaque"
        assert len(request.plays[1].documents) == 2
        assert len(request.notices) == 2
        assert request.assets.logo_files == (logo,)
        assert request.assets.asset_directories == (asset_dir.resolve(),)
        assert request.play_notice_map == (("andromaque", "master-notice"),)
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
        assert "titre du site" in errors[-1].lower()
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

        assert "Identifiant de pièce (slug)" in all_text
        assert "Ajoutez les fichiers d'une même pièce avec le même slug" in all_text
        assert "Fichier maître de notice Métopes" in all_text
        assert "Ordre de navigation des pièces" in all_text
        assert "Dossier d'assets statiques" in all_text
        assert "slug_piece|slug_notice" in all_text
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
