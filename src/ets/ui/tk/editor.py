from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class TextEditor(ttk.Frame):
    """Transcription editor with line-number gutter."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.gutter = tk.Text(
            self,
            width=5,
            padx=6,
            takefocus=0,
            borderwidth=0,
            background="#f2f2f2",
            foreground="#666666",
            state="disabled",
            wrap="none",
            font=("Consolas", 10),
        )
        self.gutter.grid(row=0, column=0, sticky="ns")

        self.text = tk.Text(
            self,
            undo=True,
            wrap="none",
            font=("Consolas", 10),
        )
        self.text.grid(row=0, column=1, sticky="nsew")

        self.v_scroll = ttk.Scrollbar(self, orient="vertical", command=self._on_vertical_scroll)
        self.v_scroll.grid(row=0, column=2, sticky="ns")
        self.h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)
        self.h_scroll.grid(row=1, column=1, sticky="ew")
        self.text.configure(yscrollcommand=self._on_text_yscroll, xscrollcommand=self.h_scroll.set)

        self.text.bind("<KeyRelease>", self._on_text_changed, add="+")
        self.text.bind("<MouseWheel>", self._on_text_changed, add="+")
        self.text.bind("<ButtonRelease-1>", self._on_text_changed, add="+")
        self.text.bind("<Configure>", self._on_text_changed, add="+")

        self._update_gutter()

    def _on_vertical_scroll(self, *args: str) -> None:
        self.text.yview(*args)
        self.gutter.yview(*args)

    def _on_text_yscroll(self, first: str, last: str) -> None:
        self.v_scroll.set(first, last)
        self.gutter.yview_moveto(first)

    def _on_text_changed(self, _event: tk.Event[tk.Misc]) -> None:
        self.after_idle(self._update_gutter)

    def _update_gutter(self) -> None:
        line_count = int(self.text.index("end-1c").split(".")[0])
        content = "\n".join(str(i) for i in range(1, line_count + 1))
        self.gutter.configure(state="normal")
        self.gutter.delete("1.0", "end")
        self.gutter.insert("1.0", content)
        self.gutter.configure(state="disabled")
        self.gutter.yview_moveto(self.text.yview()[0])

    def get_text(self) -> str:
        return self.text.get("1.0", "end-1c")

    def set_text(self, value: str) -> None:
        self.text.delete("1.0", "end")
        self.text.insert("1.0", value)
        self._update_gutter()

    def clear(self) -> None:
        self.set_text("")

    def focus_editor(self) -> None:
        self.text.focus_set()

    def go_to_line(self, line_number: int) -> None:
        index = f"{line_number}.0"
        self.text.mark_set("insert", index)
        self.text.see(index)
        self.text.focus_set()

    def clear_diagnostic_highlights(self) -> None:
        self.text.tag_remove("diag_error", "1.0", "end")

    def highlight_lines(self, line_numbers: list[int]) -> None:
        self.clear_diagnostic_highlights()
        self.text.tag_configure("diag_error", background="#ffe0e0")
        for line in line_numbers:
            self.text.tag_add("diag_error", f"{line}.0", f"{line}.end")
        self.text.tag_raise("diag_error")

    def clear_annotation_highlights(self) -> None:
        self.text.tag_remove("ann_target", "1.0", "end")
        self.text.tag_remove("ann_focus", "1.0", "end")

    def highlight_annotation_lines(self, line_numbers: list[int], *, focus_line: int | None = None) -> None:
        self.clear_annotation_highlights()
        if not line_numbers:
            return
        self.text.tag_configure("ann_target", background="#fff6cc")
        self.text.tag_configure("ann_focus", background="#ffe08a")
        for line in sorted(set(line_numbers)):
            self.text.tag_add("ann_target", f"{line}.0", f"{line}.end")
        if focus_line is not None:
            self.text.tag_add("ann_focus", f"{focus_line}.0", f"{focus_line}.end")
        # Diagnostics keep visual priority over annotation marks when both exist.
        self.text.tag_lower("ann_target")
        self.text.tag_raise("ann_target")
        self.text.tag_raise("ann_focus")
        if "diag_error" in self.text.tag_names():
            self.text.tag_raise("diag_error")
