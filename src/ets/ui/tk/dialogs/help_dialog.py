from __future__ import annotations

import tkinter as tk
from tkinter import messagebox


def show_help_dialog(parent: tk.Misc) -> None:
    messagebox.showinfo(
        "Aide syntaxe",
        "Rappels de syntaxe:\n"
        "- ####...#### : acte\n"
        "- ###...### : scène\n"
        "- ##...## : distribution\n"
        "- #...# : locuteur\n"
        "- **...** : didascalie explicite\n"
        "- *** : vers partagés\n"
        "- ##### : variante de ligne entière\n"
        "- $$TYPE$$ ... $$fin$$ : didascalie implicite",
        parent=parent,
    )

