from __future__ import annotations

import tkinter as tk
from pathlib import Path
from uuid import uuid4

import pytest

from ets.application import AppDiagnostic, load_annotations
from ets.infrastructure import AutosavePayload, AutosaveStore
from ets.ui.tk.helpers import diagnostic_line_numbers, format_config_status
from ets.ui.tk.main_window import MainWindow


RUNTIME_DIR = Path(__file__).resolve().parents[1] / "tests" / "_runtime"
RUNTIME_DIR.mkdir(exist_ok=True)


def _make_root() -> tk.Tk:
    try:
        root = tk.Tk()
    except tk.TclError as exc:  # pragma: no cover - depends on runtime display availability
        pytest.skip(f"Tk not available in this environment: {exc}")
    root.withdraw()
    return root


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
    finally:
        root.destroy()


def test_annotation_crud_actions_update_state(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        fixture = Path(__file__).resolve().parents[1] / "fixtures" / "annotations" / "berenice_1_1" / "annotations.json"
        collection = load_annotations(fixture)
        window._set_annotations(collection, fixture)

        add_payload = {
            "id": "n_added",
            "type": "explicative",
            "anchor": {"kind": "line", "act": "1", "scene": "1", "line": "1"},
            "content": "ajout",
            "status": "draft",
            "keywords": [],
        }
        monkeypatch.setattr("ets.ui.tk.main_window.open_annotation_dialog", lambda *args, **kwargs: add_payload)
        window.action_add_annotation()
        assert any(item.id == "n_added" for item in window.state.annotations.annotations)

        edit_payload = {
            "id": "n_added",
            "type": "dramaturgique",
            "anchor": {"kind": "line", "act": "1", "scene": "1", "line": "1"},
            "content": "modif",
            "status": "reviewed",
            "keywords": [],
        }
        window.outputs.annotations_panel.tree.selection_set("n_added")
        monkeypatch.setattr("ets.ui.tk.main_window.open_annotation_dialog", lambda *args, **kwargs: edit_payload)
        window.action_edit_annotation()
        edited = [item for item in window.state.annotations.annotations if item.id == "n_added"][0]
        assert edited.type == "dramaturgique"
        assert edited.content == "modif"

        monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *args, **kwargs: True)
        window.outputs.annotations_panel.tree.selection_set("n_added")
        window.action_delete_annotation()
        assert all(item.id != "n_added" for item in window.state.annotations.annotations)
    finally:
        root.destroy()
