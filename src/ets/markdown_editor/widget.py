from __future__ import annotations

from pathlib import Path
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from .dialogs import PreviewSearchDialog, SourceSearchOptions, SourceSearchReplaceDialog
from ets.references import CitationTokenData

from .models import MarkdownDiagnostic, MarkdownParseResult
from .preview import PreviewRenderer
from .service import MarkdownEditorService


class MarkdownEditorWidget(ttk.Frame):
    PREVIEW_DEBOUNCE_MS = 320

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=6)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.service = MarkdownEditorService()
        self.renderer = PreviewRenderer()
        self.current_path: Path | None = None
        self.current_parse_result: MarkdownParseResult | None = None
        self._dirty = False
        self._after_id: str | None = None

        self._build_toolbar()
        self._build_panes()
        self._build_diagnostics()
        self._install_bindings()
        self.force_refresh_preview()

    def _build_toolbar(self) -> None:
        self.toolbar = ttk.Frame(self)
        self.toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.toolbar.columnconfigure(0, weight=1)

        row1 = ttk.Frame(self.toolbar)
        row1.grid(row=0, column=0, sticky="w")
        row2 = ttk.Frame(self.toolbar)
        row2.grid(row=1, column=0, sticky="w", pady=(4, 0))

        row1_buttons = [
            ("Gras", self.apply_bold),
            ("Italique", self.apply_italic),
            ("Souligné", self.apply_underline),
            ("Exposant", self.apply_sup),
            ("Indice", self.apply_sub),
            ("Capitales", self.apply_caps),
            ("Petites cap.", self.apply_smallcaps),
            ("T1", self.apply_heading_1),
            ("T2", self.apply_heading_2),
            ("T3", self.apply_heading_3),
        ]
        row2_buttons = [
            ("Citation", self.apply_quote),
            ("Note", self.insert_note),
            ("Bibliographie", self.insert_bibliography_block),
            ("Rechercher", self.open_source_search_dialog),
            ("Rech. aperçu", self.open_preview_search_dialog),
        ]

        for index, (label, command) in enumerate(row1_buttons):
            ttk.Button(row1, text=label, command=command, width=11).grid(row=0, column=index, padx=2)
        for index, (label, command) in enumerate(row2_buttons):
            ttk.Button(row2, text=label, command=command, width=13).grid(row=0, column=index, padx=2)

    def _build_panes(self) -> None:
        self.paned = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        self.paned.grid(row=1, column=0, sticky="nsew")

        self.left = ttk.Frame(self.paned)
        self.left.columnconfigure(0, weight=1)
        self.left.rowconfigure(0, weight=1)

        self.source_text = tk.Text(self.left, undo=True, wrap="word", font=("Consolas", 11))
        self.source_text.grid(row=0, column=0, sticky="nsew")
        self.source_text.configure(state="normal")
        source_y = ttk.Scrollbar(self.left, orient="vertical", command=self.source_text.yview)
        source_y.grid(row=0, column=1, sticky="ns")
        self.source_text.configure(yscrollcommand=source_y.set)

        self.right = ttk.Frame(self.paned)
        self.right.columnconfigure(0, weight=1)
        self.right.rowconfigure(0, weight=1)

        self.preview_text = tk.Text(
            self.right,
            undo=False,
            wrap="word",
            font=("Georgia", 11),
            state="disabled",
            cursor="xterm",
            takefocus=False,
        )
        self.preview_text.grid(row=0, column=0, sticky="nsew")
        preview_y = ttk.Scrollbar(self.right, orient="vertical", command=self.preview_text.yview)
        preview_y.grid(row=0, column=1, sticky="ns")
        self.preview_text.configure(yscrollcommand=preview_y.set)
        self.preview_text.tag_configure("preview_search", background="#fef08a")

        self.paned.add(self.left, weight=3)
        self.paned.add(self.right, weight=2)
        self.after_idle(self.reset_split_view)

        self._source_menu = tk.Menu(self.source_text, tearoff=False)
        self._source_menu.add_command(label="Couper", command=lambda: self.source_text.event_generate("<<Cut>>"))
        self._source_menu.add_command(label="Copier", command=lambda: self.source_text.event_generate("<<Copy>>"))
        self._source_menu.add_command(label="Coller", command=lambda: self.source_text.event_generate("<<Paste>>"))
        self._source_menu.add_separator()
        self._source_menu.add_command(label="Tout sélectionner", command=self.select_all_source)

    def _build_diagnostics(self) -> None:
        diagnostics_frame = ttk.LabelFrame(self, text="Diagnostics", padding=(6, 4))
        diagnostics_frame.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        diagnostics_frame.columnconfigure(0, weight=1)
        diagnostics_frame.rowconfigure(0, weight=1)

        self.diagnostics_list = tk.Listbox(diagnostics_frame, height=5)
        self.diagnostics_list.grid(row=0, column=0, sticky="ew")
        diag_scroll = ttk.Scrollbar(diagnostics_frame, orient="vertical", command=self.diagnostics_list.yview)
        diag_scroll.grid(row=0, column=1, sticky="ns")
        self.diagnostics_list.configure(yscrollcommand=diag_scroll.set)

    def _install_bindings(self) -> None:
        for sequence in ("<KeyRelease>", "<<Paste>>", "<<Cut>>", "<Delete>"):
            self.source_text.bind(sequence, self._on_source_changed, add="+")
        self.source_text.bind("<Button-1>", self._on_source_click_focus, add="+")
        self.source_text.bind("<Button-3>", self._show_source_menu, add="+")
        self.source_text.bind("<Control-b>", self._shortcut(self.apply_bold), add="+")
        self.source_text.bind("<Control-B>", self._shortcut(self.apply_bold), add="+")
        self.source_text.bind("<Control-i>", self._shortcut(self.apply_italic), add="+")
        self.source_text.bind("<Control-I>", self._shortcut(self.apply_italic), add="+")

    def _shortcut(self, command: callable) -> callable:
        def callback(_event: tk.Event[tk.Misc]) -> str:
            command()
            return "break"

        return callback

    def _show_source_menu(self, event: tk.Event[tk.Misc]) -> str:
        self._source_menu.tk_popup(event.x_root, event.y_root)
        return "break"

    def _on_source_click_focus(self, _event: tk.Event[tk.Misc]) -> None:
        self.source_text.focus_set()

    def _on_source_changed(self, _event: tk.Event[tk.Misc]) -> None:
        self._dirty = True
        self.schedule_preview_refresh()

    def schedule_preview_refresh(self) -> None:
        if self._after_id is not None:
            self.after_cancel(self._after_id)
        self._after_id = self.after(self.PREVIEW_DEBOUNCE_MS, self.force_refresh_preview)

    def force_refresh_preview(self) -> None:
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        focused = self.focus_get()
        source = self.get_text()
        result = self.service.parse(source)
        preview_diagnostics = self.renderer.render(self.preview_text, result.document)
        combined_diagnostics = result.diagnostics + preview_diagnostics
        self.current_parse_result = MarkdownParseResult(document=result.document, diagnostics=combined_diagnostics)
        self._refresh_diagnostics(combined_diagnostics)
        if focused is self.source_text:
            self.source_text.focus_set()

    def _refresh_diagnostics(self, diagnostics: tuple[MarkdownDiagnostic, ...]) -> None:
        self.diagnostics_list.delete(0, "end")
        if not diagnostics:
            self.diagnostics_list.insert("end", "Aucun diagnostic.")
            return
        for diagnostic in diagnostics:
            where = ""
            if diagnostic.line is not None:
                where = f" (ligne {diagnostic.line}"
                if diagnostic.column is not None:
                    where += f", col. {diagnostic.column}"
                where += ")"
            self.diagnostics_list.insert(
                "end",
                f"[{diagnostic.severity}] {diagnostic.code}: {diagnostic.message}{where}",
            )

    def set_citation_resolver(self, resolver: Callable[[CitationTokenData], str | None] | None) -> None:
        self.renderer.set_citation_resolver(resolver)
        self.force_refresh_preview()

    def reset_split_view(self) -> None:
        self.update_idletasks()
        total_width = self.paned.winfo_width()
        if total_width <= 1:
            total_width = self.winfo_width()
        if total_width <= 1:
            total_width = 1000
        target = int(total_width * 0.58)
        if total_width > 600:
            target = max(280, min(target, total_width - 260))
        try:
            self.paned.sashpos(0, target)
        except tk.TclError:
            return

    def get_text(self) -> str:
        return self.source_text.get("1.0", "end-1c")

    def set_text(self, value: str) -> None:
        self.source_text.delete("1.0", "end")
        self.source_text.insert("1.0", value)
        self._dirty = False
        self.force_refresh_preview()

    def focus_source(self) -> None:
        self.source_text.focus_set()

    def is_dirty(self) -> bool:
        return self._dirty

    def select_all_source(self) -> None:
        self.source_text.tag_add("sel", "1.0", "end-1c")
        self.source_text.mark_set("insert", "1.0")
        self.source_text.see("insert")
        self.source_text.focus_set()

    def new_document(self) -> None:
        self.current_path = None
        self.set_text("")

    def open_file(self, path: str | Path | None = None) -> Path | None:
        if path is None:
            selected = filedialog.askopenfilename(
                title="Ouvrir un Markdown",
                filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("Tous les fichiers", "*.*")],
            )
            if not selected:
                return None
            path = selected
        resolved = Path(path).resolve()
        content = self.service.load_markdown(resolved)
        self.current_path = resolved
        self.set_text(content)
        return resolved

    def save_file(self) -> Path | None:
        if self.current_path is None:
            return self.save_file_as()
        self.service.save_markdown(self.get_text(), self.current_path)
        self._dirty = False
        return self.current_path

    def save_file_as(self, path: str | Path | None = None) -> Path | None:
        if path is None:
            selected = filedialog.asksaveasfilename(
                title="Enregistrer le Markdown",
                defaultextension=".md",
                filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("Tous les fichiers", "*.*")],
            )
            if not selected:
                return None
            path = selected
        resolved = self.service.save_markdown(self.get_text(), path)
        self.current_path = resolved
        self._dirty = False
        return resolved

    def export_markdown(self, path: str | Path | None = None) -> Path | None:
        if path is None:
            selected = filedialog.asksaveasfilename(
                title="Exporter Markdown",
                defaultextension=".md",
                filetypes=[("Markdown", "*.md"), ("Tous les fichiers", "*.*")],
            )
            if not selected:
                return None
            path = selected
        return self.service.save_markdown(self.get_text(), path)

    def export_tei_document(self, path: str | Path | None = None) -> Path | None:
        result = self.service.export_document(self.get_text(), title=self._suggest_title())
        if path is None:
            selected = filedialog.asksaveasfilename(
                title="Exporter XML-TEI",
                defaultextension=".xml",
                filetypes=[("XML", "*.xml"), ("Tous les fichiers", "*.*")],
            )
            if not selected:
                return None
            path = selected
        return self.service.save_tei(result.tei_xml, path)

    def export_tei_fragment(self, path: str | Path | None = None) -> Path | None:
        result = self.service.export_fragment(self.get_text())
        if path is None:
            selected = filedialog.asksaveasfilename(
                title="Exporter fragment XML-TEI",
                defaultextension=".xml",
                filetypes=[("XML", "*.xml"), ("Tous les fichiers", "*.*")],
            )
            if not selected:
                return None
            path = selected
        return self.service.save_tei(result.tei_xml, path)

    def _suggest_title(self) -> str:
        if self.current_parse_result is None:
            return "Notice éditoriale"
        return self.service.document_title(self.current_parse_result.document)

    def _selection_or_placeholder(self, placeholder: str = "texte") -> tuple[str, str, str]:
        try:
            start = self.source_text.index("sel.first")
            end = self.source_text.index("sel.last")
            selected = self.source_text.get(start, end)
            return start, end, selected
        except tk.TclError:
            cursor = self.source_text.index("insert")
            return cursor, cursor, placeholder

    def _wrap_selection(self, prefix: str, suffix: str, *, placeholder: str = "texte") -> None:
        start, end, selected = self._selection_or_placeholder(placeholder=placeholder)
        insertion = f"{prefix}{selected}{suffix}"
        self.source_text.delete(start, end)
        self.source_text.insert(start, insertion)
        if start == end:
            cursor = self.source_text.index(f"{start}+{len(prefix)}c")
            self.source_text.mark_set("insert", cursor)
        else:
            select_end = self.source_text.index(f"{start}+{len(insertion)}c")
            self.source_text.tag_add("sel", start, select_end)
        self.source_text.focus_set()
        self._on_source_changed(tk.Event())

    def _prefix_lines(self, prefix: str, *, numbered: bool = False) -> None:
        try:
            start_index = self.source_text.index("sel.first linestart")
            end_index = self.source_text.index("sel.last lineend")
        except tk.TclError:
            start_index = self.source_text.index("insert linestart")
            end_index = self.source_text.index("insert lineend")

        lines = self.source_text.get(start_index, end_index).splitlines()
        transformed: list[str] = []
        for idx, line in enumerate(lines, start=1):
            if numbered:
                transformed.append(f"{idx}. {line.lstrip()}")
            else:
                transformed.append(f"{prefix}{line}")
        replacement = "\n".join(transformed)
        self.source_text.delete(start_index, end_index)
        self.source_text.insert(start_index, replacement)
        self.source_text.focus_set()
        self._on_source_changed(tk.Event())

    def apply_bold(self) -> None:
        self._wrap_selection("**", "**")

    def apply_italic(self) -> None:
        self._wrap_selection("*", "*")

    def apply_underline(self) -> None:
        self._wrap_selection("[u]", "[/u]")

    def apply_sup(self) -> None:
        self._wrap_selection("[sup]", "[/sup]")

    def apply_sub(self) -> None:
        self._wrap_selection("[sub]", "[/sub]")

    def apply_caps(self) -> None:
        self._wrap_selection("[caps]", "[/caps]")

    def apply_smallcaps(self) -> None:
        self._wrap_selection("[sc]", "[/sc]")

    def apply_heading_1(self) -> None:
        self._prefix_lines("# ")

    def apply_heading_2(self) -> None:
        self._prefix_lines("## ")

    def apply_heading_3(self) -> None:
        self._prefix_lines("### ")

    def apply_heading_4(self) -> None:
        self._prefix_lines("#### ")

    def apply_quote(self) -> None:
        self._prefix_lines("> ")

    def apply_bullet_list(self) -> None:
        self._prefix_lines("- ")

    def apply_numbered_list(self) -> None:
        self._prefix_lines("", numbered=True)

    def insert_separator(self) -> None:
        self.source_text.insert("insert", "\n---\n")
        self._on_source_changed(tk.Event())

    def insert_link(self) -> None:
        self._wrap_selection("[", "](https://example.org)", placeholder="texte")

    def insert_note(self) -> None:
        existing_ids = {int(match.group(1)) for match in re.finditer(r"\[\^(\d+)\]", self.get_text())}
        next_id = 1
        while next_id in existing_ids:
            next_id += 1
        note_ref = f"[^{next_id}]"
        self.source_text.insert("insert", note_ref)
        if f"[^{next_id}]:" not in self.get_text():
            current_end = self.source_text.get("1.0", "end-1c")
            separator = "" if current_end.endswith("\n\n") else "\n\n"
            self.source_text.insert("end", f"{separator}[^{next_id}]: ")
        self.source_text.focus_set()
        self._on_source_changed(tk.Event())

    def insert_bibliography_block(self) -> None:
        template = "\n:::bibl\n- Référence 1\n:::\n"
        self.source_text.insert("insert", template)
        self._on_source_changed(tk.Event())

    def insert_french_quotes(self) -> None:
        self._wrap_selection("«\u202f", "\u202f»")

    def insert_thin_nbsp(self) -> None:
        self.source_text.insert("insert", "\u202f")
        self._on_source_changed(tk.Event())

    def insert_em_dash(self) -> None:
        self.source_text.insert("insert", "—")
        self._on_source_changed(tk.Event())

    def insert_text_at_cursor(self, value: str) -> None:
        if value:
            self.source_text.insert("insert", value)
        self.source_text.focus_set()
        self._on_source_changed(tk.Event())

    def close_document(self) -> None:
        if self._dirty and not messagebox.askyesno(
            "Fermer le document",
            "Le document Markdown contient des modifications non enregistrées. Fermer quand même ?",
            parent=self,
        ):
            return
        self.new_document()

    def _compiled_pattern(self, options: SourceSearchOptions) -> tuple[str, bool]:
        if options.regex:
            pattern = options.pattern
        else:
            pattern = re.escape(options.pattern)
        if options.whole_word:
            pattern = rf"\b{pattern}\b"
            return pattern, True
        return pattern, options.regex

    def _find_in_source(self, options: SourceSearchOptions, backward: bool) -> bool:
        if not options.pattern:
            return False
        pattern, use_regex = self._compiled_pattern(options)
        nocase = not options.case_sensitive
        count_var = tk.IntVar(value=0)
        widget = self.source_text

        if options.in_selection:
            try:
                scope_start = widget.index("sel.first")
                scope_end = widget.index("sel.last")
            except tk.TclError:
                return False
        else:
            scope_start = "1.0"
            scope_end = "end-1c"

        insert_index = widget.index("insert")
        if backward:
            idx = widget.search(
                pattern,
                insert_index,
                stopindex=scope_start,
                regexp=use_regex,
                nocase=nocase,
                backwards=True,
                count=count_var,
            )
            if not idx and not options.in_selection:
                idx = widget.search(
                    pattern,
                    scope_end,
                    stopindex=insert_index,
                    regexp=use_regex,
                    nocase=nocase,
                    backwards=True,
                    count=count_var,
                )
        else:
            idx = widget.search(
                pattern,
                insert_index,
                stopindex=scope_end,
                regexp=use_regex,
                nocase=nocase,
                count=count_var,
            )
            if not idx and not options.in_selection:
                idx = widget.search(
                    pattern,
                    scope_start,
                    stopindex=insert_index,
                    regexp=use_regex,
                    nocase=nocase,
                    count=count_var,
                )

        if not idx:
            return False

        length = max(count_var.get(), 1)
        end = widget.index(f"{idx}+{length}c")
        widget.tag_remove("sel", "1.0", "end")
        widget.tag_add("sel", idx, end)
        widget.mark_set("insert", idx if backward else end)
        widget.see(idx)
        widget.focus_set()
        return True

    def _replace_one(self, options: SourceSearchOptions) -> bool:
        if not options.pattern:
            return False
        try:
            start = self.source_text.index("sel.first")
            end = self.source_text.index("sel.last")
            selected = self.source_text.get(start, end)
            pattern, use_regex = self._compiled_pattern(options)
            flags = 0 if options.case_sensitive else re.IGNORECASE
            if use_regex:
                if re.fullmatch(pattern, selected, flags=flags) is None:
                    if not self._find_in_source(options, backward=False):
                        return False
                    return self._replace_one(options)
            elif (selected == options.pattern) if options.case_sensitive else (selected.lower() == options.pattern.lower()):
                pass
            else:
                if not self._find_in_source(options, backward=False):
                    return False
                return self._replace_one(options)
            self.source_text.delete(start, end)
            self.source_text.insert(start, options.replacement)
            self.source_text.tag_add("sel", start, f"{start}+{len(options.replacement)}c")
            self._on_source_changed(tk.Event())
            return True
        except tk.TclError:
            if not self._find_in_source(options, backward=False):
                return False
            return self._replace_one(options)

    def _replace_all(self, options: SourceSearchOptions) -> int:
        if not options.pattern:
            return 0
        source = self.get_text()
        pattern, use_regex = self._compiled_pattern(options)
        flags = 0 if options.case_sensitive else re.IGNORECASE

        if options.in_selection:
            try:
                start = self.source_text.index("sel.first")
                end = self.source_text.index("sel.last")
            except tk.TclError:
                return 0
            selected = self.source_text.get(start, end)
            if use_regex:
                replaced, count = re.subn(pattern, options.replacement, selected, flags=flags)
            else:
                if options.case_sensitive:
                    count = selected.count(options.pattern)
                    replaced = selected.replace(options.pattern, options.replacement)
                else:
                    replaced, count = re.subn(re.escape(options.pattern), options.replacement, selected, flags=flags)
            self.source_text.delete(start, end)
            self.source_text.insert(start, replaced)
            if count:
                self._on_source_changed(tk.Event())
            return count

        if use_regex:
            replaced, count = re.subn(pattern, options.replacement, source, flags=flags)
        else:
            if options.case_sensitive:
                count = source.count(options.pattern)
                replaced = source.replace(options.pattern, options.replacement)
            else:
                replaced, count = re.subn(re.escape(options.pattern), options.replacement, source, flags=flags)
        if count:
            self.set_text(replaced)
            self._dirty = True
        return count

    def open_source_search_dialog(self) -> None:
        SourceSearchReplaceDialog(
            self,
            on_find=self._find_in_source,
            on_replace=self._replace_one,
            on_replace_all=self._replace_all,
        )

    def _find_in_preview(self, query: str, backward: bool) -> bool:
        text = self.preview_text
        text.configure(state="normal")
        text.tag_remove("preview_search", "1.0", "end")
        start = "1.0"
        while True:
            idx = text.search(query, start, stopindex="end", nocase=True)
            if not idx:
                break
            end = f"{idx}+{len(query)}c"
            text.tag_add("preview_search", idx, end)
            start = end

        insert = text.index("insert")
        if backward:
            idx = text.search(query, insert, stopindex="1.0", nocase=True, backwards=True)
            if not idx:
                idx = text.search(query, "end", stopindex=insert, nocase=True, backwards=True)
        else:
            idx = text.search(query, insert, stopindex="end", nocase=True)
            if not idx:
                idx = text.search(query, "1.0", stopindex=insert, nocase=True)
        if not idx:
            text.configure(state="disabled")
            return False
        end = f"{idx}+{len(query)}c"
        text.tag_remove("sel", "1.0", "end")
        text.tag_add("sel", idx, end)
        text.mark_set("insert", end)
        text.see(idx)
        text.focus_set()
        text.configure(state="disabled")
        return True

    def open_preview_search_dialog(self) -> None:
        PreviewSearchDialog(self, on_find_next=self._find_in_preview)

    def destroy(self) -> None:
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None
        super().destroy()
