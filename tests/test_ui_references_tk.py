from __future__ import annotations

import tkinter as tk

import pytest

from ets.references.dialogs import AddReferenceDialog, InsertCitationDialog
from ets.references.models import ReferenceRecord
from ets.ui.tk.main_window import MainWindow


def _make_root() -> tk.Tk:
    try:
        root = tk.Tk()
    except tk.TclError as exc:  # pragma: no cover - depends on runtime display availability
        pytest.skip(f"Tk not available in this environment: {exc}")
    root.withdraw()
    return root


def test_main_window_exposes_references_tab() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        labels = [window.editor_tabs.tab(tab_id, "text") for tab_id in window.editor_tabs.tabs()]
        assert "Références" in labels
        assert window.references_panel.winfo_exists()
    finally:
        root.destroy()


def test_references_menu_exists() -> None:
    root = _make_root()
    try:
        MainWindow(root)
        menubar = root.nametowidget(str(root["menu"]))
        labels: list[str] = []
        end = menubar.index("end")
        assert end is not None
        for index in range(end + 1):
            if menubar.type(index) == "cascade":
                labels.append(menubar.entrycget(index, "label"))
        assert "Références" in labels
    finally:
        root.destroy()


def test_insert_citation_token_targets_markdown_source() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        window.editor_tabs.select(window.markdown_editor)
        window._last_editor_mode = "markdown"
        window._last_editable_text_widget = window.markdown_editor.source_text

        inserted = window._insert_citation_token_into_active_editor("{{CITE:demo}}")
        assert inserted is True
        assert "{{CITE:demo}}" in window.markdown_editor.get_text()
    finally:
        root.destroy()


def test_add_reference_action_updates_catalog_and_service(monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        payload = {
            "authors": "Forestier; Mauron",
            "title": "Berenice",
            "date": "1999",
            "reference_type": "book",
            "publisher": "Gallimard",
            "place": "Paris",
            "container_title": "",
            "editor": "",
            "translator": "",
            "volume": "",
            "issue": "",
            "pages": "",
            "url": "",
            "doi": "",
            "source_key": "",
            "note": "",
        }
        monkeypatch.setattr("ets.references.ui.open_add_reference_dialog", lambda _parent: payload)

        window.references_panel.action_add_reference()

        assert len(window.references_panel.references_table.get_children()) == 1
        matches = window.references_panel.service.search_references("berenice")
        assert len(matches) == 1
        assert matches[0].publisher == "Gallimard"
        assert matches[0].place == "Paris"
    finally:
        root.destroy()


def test_insert_citation_dialog_populates_rows_and_submit_returns_selection() -> None:
    root = _make_root()
    try:
        refs = (
            ReferenceRecord(
                id="r1",
                origin="manual",
                source_key=None,
                type="book",
                title="Titre 1",
                authors=("Auteur A",),
            ),
            ReferenceRecord(
                id="r2",
                origin="manual",
                source_key=None,
                type="book",
                title="Titre 2",
                authors=("Auteur B",),
            ),
        )
        dialog = InsertCitationDialog(root, references=refs)
        dialog.update_idletasks()
        rows = dialog.table.get_children()
        assert len(rows) == 2
        dialog.table.selection_set(rows[1])
        dialog.table.focus(rows[1])
        dialog._submit()
        assert dialog.result is not None
        assert dialog.result["reference_id"] == "r2"
        if dialog.winfo_exists():
            dialog.destroy()
    finally:
        root.destroy()


def test_insert_citation_refuses_when_markdown_context_not_available() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        window._last_editor_mode = "transcription"
        window.editor.set_text("Texte brut")
        inserted = window._insert_citation_token_into_active_editor("{{CITE:nope}}")
        assert inserted is False
        assert "{{CITE:nope}}" not in window.editor.get_text()
        assert "{{CITE:nope}}" not in window.markdown_editor.get_text()
    finally:
        root.destroy()


def test_references_text_source_is_markdown_only() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        window.editor.set_text("TRANSCRIPTION")
        window.markdown_editor.set_text("MARKDOWN {{CITE:x}}")
        assert window._get_text_for_references() == "MARKDOWN {{CITE:x}}"
    finally:
        root.destroy()


def test_add_reference_dialog_exposes_editor_and_place_fields_and_validates_title(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _make_root()
    try:
        warnings: list[str] = []
        monkeypatch.setattr("tkinter.messagebox.showwarning", lambda _title, message, **kwargs: warnings.append(message))
        dialog = AddReferenceDialog(root)
        dialog.update_idletasks()
        assert "publisher" in dialog._entries
        assert "place" in dialog._entries
        dialog._vars["title"].set("")
        dialog._submit()
        assert warnings
        assert "titre" in warnings[-1].lower()
        assert dialog.result is None
        dialog.destroy()
    finally:
        root.destroy()


def test_markdown_preview_renders_citation_token_as_readable_text() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        ref = window.references_panel.service.add_manual_reference(
            title="Berenice",
            authors=["Forestier"],
            date="1999",
        )
        window.references_panel.service.set_style("simple_author_date")
        window.markdown_editor.set_text(f"Citation {window.references_panel.service.build_citation_token(ref.id, locator='p. 143')}.")
        window.markdown_editor.force_refresh_preview()

        preview = window.markdown_editor.preview_text.get("1.0", "end-1c")
        assert "{{CITE:" not in preview
        assert "Forestier" in preview
        assert "1999" in preview
    finally:
        root.destroy()


def test_markdown_preview_uses_fallback_and_warning_for_unknown_reference() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        window.markdown_editor.set_text("Texte {{CITE:ref-inconnue|locator=p. 10}}.")
        window.markdown_editor.force_refresh_preview()
        preview = window.markdown_editor.preview_text.get("1.0", "end-1c")
        assert "{{CITE:" not in preview
        assert "[ref-inconnue, p. 10]" in preview
        codes = {item.code for item in (window.markdown_editor.current_parse_result.diagnostics if window.markdown_editor.current_parse_result else ())}
        assert "W_MD_CITE_ORPHAN" in codes
    finally:
        root.destroy()


def test_bibliography_generation_still_uses_citations_in_markdown_text() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        ref = window.references_panel.service.add_manual_reference(title="Berenice", authors=["Forestier"], date="1999")
        token = window.references_panel.service.build_citation_token(ref.id, locator="p. 12")
        window.markdown_editor.set_text(f"Corps du texte {token}.")
        state = window.references_panel.refresh_bibliography()
        assert state.cited_reference_ids == (ref.id,)
    finally:
        root.destroy()


def test_token_inside_bibl_block_is_not_rendered_as_raw_code() -> None:
    root = _make_root()
    try:
        window = MainWindow(root)
        ref = window.references_panel.service.add_manual_reference(title="Berenice", authors=["Forestier"], date="1999")
        token = window.references_panel.service.build_citation_token(ref.id)
        window.markdown_editor.set_text(f":::bibl\n- Entrée {token}\n:::\n")
        window.markdown_editor.force_refresh_preview()
        preview = window.markdown_editor.preview_text.get("1.0", "end-1c")
        assert "{{CITE:" not in preview
        codes = {item.code for item in (window.markdown_editor.current_parse_result.diagnostics if window.markdown_editor.current_parse_result else ())}
        assert "W_MD_CITE_IN_BIBL" in codes
    finally:
        root.destroy()
