from __future__ import annotations

import tkinter as tk

from .main_window import MainWindow


def main() -> int:
    root = tk.Tk()
    # Reste cachee tant que l'utilisateur n'a pas choisi un module sur le
    # nagscreen (voir MainWindow._show_welcome_dialog_and_route) : sinon la
    # fenetre d'edition apparait brievement avant que le choix soit fait.
    root.withdraw()
    MainWindow(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

