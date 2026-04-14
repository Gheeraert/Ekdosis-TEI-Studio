from __future__ import annotations

import tkinter as tk
from pathlib import Path
from uuid import uuid4

import pytest

from ets.application import AppDiagnostic
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
