from __future__ import annotations

import tkinter as tk

import pytest

from ets.application import AppDiagnostic
from ets.ui.tk.helpers import diagnostic_line_numbers, format_config_status
from ets.ui.tk.main_window import MainWindow


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
