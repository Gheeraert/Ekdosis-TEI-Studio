from __future__ import annotations

import tkinter as tk

import pytest

from ets.ui.tk.main_window import MainWindow


def _make_root() -> tk.Tk:
    try:
        root = tk.Tk()
    except tk.TclError as exc:  # pragma: no cover - depends on runtime display availability
        pytest.skip(f"Tk not available in this environment: {exc}")
    root.withdraw()
    return root


def test_main_window_exposes_markdown_editor_tab() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        labels = [window.editor_tabs.tab(tab_id, "text") for tab_id in window.editor_tabs.tabs()]
        assert "Éditeur Markdown" in labels
    finally:
        root.destroy()


def test_markdown_format_action_wraps_selection() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        window.editor_tabs.select(window.markdown_editor)
        window.markdown_editor.set_text("mot")
        window.markdown_editor.source_text.tag_add("sel", "1.0", "1.3")
        window.action_markdown_format_bold()
        assert window.markdown_editor.get_text() == "**mot**"
    finally:
        root.destroy()


def test_markdown_source_widget_exists_and_is_editable() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        window.editor_tabs.select(window.markdown_editor)
        source = window.markdown_editor.source_text
        assert isinstance(source, tk.Text)
        assert str(source.cget("state")) == "normal"
        source.delete("1.0", "end")
        source.insert("1.0", "abc")
        assert source.get("1.0", "end-1c") == "abc"
    finally:
        root.destroy()


def test_markdown_preview_widget_is_distinct_and_readonly() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        window.editor_tabs.select(window.markdown_editor)
        source = window.markdown_editor.source_text
        preview = window.markdown_editor.preview_text
        assert isinstance(preview, tk.Text)
        assert source is not preview
        assert str(preview.cget("state")) == "disabled"
        panes = window.markdown_editor.paned.panes()
        assert len(panes) == 2
    finally:
        root.destroy()


def test_action_find_routes_to_markdown_source_dialog(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        window.editor_tabs.select(window.markdown_editor)
        calls: list[str] = []
        monkeypatch.setattr(window.markdown_editor, "open_source_search_dialog", lambda: calls.append("source"))
        monkeypatch.setattr(window.markdown_editor, "open_preview_search_dialog", lambda: calls.append("preview"))
        window.action_find()
        assert calls == ["source"]
    finally:
        root.destroy()


def test_menus_include_markdown_specific_cascades() -> None:
    root = _make_root()
    try:
        MainWindow(root)
        menubar = root.nametowidget(str(root["menu"]))
        labels: list[str] = []
        end = menubar.index("end")
        assert end is not None
        for i in range(end + 1):
            if menubar.type(i) == "cascade":
                labels.append(menubar.entrycget(i, "label"))
        assert "Insertion" in labels
        assert "Format" in labels
        assert "Structure" in labels
    finally:
        root.destroy()
