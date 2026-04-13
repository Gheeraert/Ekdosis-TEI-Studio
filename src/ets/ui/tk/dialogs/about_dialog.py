from __future__ import annotations

import tkinter as tk
from tkinter import messagebox


def show_about_dialog(parent: tk.Misc) -> None:
    messagebox.showinfo(
        "À propos",
        "Ekdosis TEI Studio v2\nInterface Tkinter locale (V1)\n\n"
        "Cette interface utilise la couche de services application.",
        parent=parent,
    )

