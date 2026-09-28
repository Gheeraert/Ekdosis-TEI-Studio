"""Info-bulle Tkinter legere et reutilisable.

Aucune dependance externe : une petite fenetre sans decoration (Toplevel
`overrideredirect`) apparait pres du widget au survol de la souris et
disparait des que la souris le quitte. Pas de clic requis, pas de modal.

Usage :
    add_tooltip(widget, "Texte explicatif, eventuellement sur\\nplusieurs lignes.")
"""

from __future__ import annotations

import tkinter as tk

_SHOW_DELAY_MS = 400


class Tooltip:
    """Associe une info-bulle a un widget Tkinter."""

    def __init__(self, widget: tk.Misc, text: str) -> None:
        self._widget = widget
        self._text = text
        self._tip_window: tk.Toplevel | None = None
        self._after_id: str | None = None
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, _event: tk.Event[tk.Misc]) -> None:
        self._schedule_show()

    def _on_leave(self, _event: tk.Event[tk.Misc]) -> None:
        self._cancel_scheduled_show()
        self._hide()

    def _schedule_show(self) -> None:
        self._cancel_scheduled_show()
        self._after_id = self._widget.after(_SHOW_DELAY_MS, self._show)

    def _cancel_scheduled_show(self) -> None:
        if self._after_id is not None:
            self._widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self) -> None:
        if self._tip_window is not None:
            return
        try:
            x = self._widget.winfo_rootx() + 12
            y = self._widget.winfo_rooty() + self._widget.winfo_height() + 6
        except tk.TclError:
            return

        window = tk.Toplevel(self._widget)
        window.wm_overrideredirect(True)
        try:
            window.wm_attributes("-topmost", True)
        except tk.TclError:
            pass
        window.wm_geometry(f"+{x}+{y}")

        tk.Label(
            window,
            text=self._text,
            justify="left",
            background="#ffffe0",
            foreground="black",
            relief="solid",
            borderwidth=1,
            wraplength=360,
            padx=6,
            pady=3,
            font=("Segoe UI", 9),
        ).pack()

        self._tip_window = window

    def _hide(self) -> None:
        if self._tip_window is not None:
            self._tip_window.destroy()
            self._tip_window = None


def add_tooltip(widget: tk.Misc, text: str) -> Tooltip:
    """Attache une info-bulle discrete a `widget` et la renvoie."""
    return Tooltip(widget, text)
