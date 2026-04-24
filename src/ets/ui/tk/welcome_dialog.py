"""Fenêtre d'accueil de TEI Studio.

Petit écran d'ouverture inspiré de la V1, volontairement autonome :
- aucune logique métier ;
- aucun accès aux services ;
- fermeture par Entrée, Échap, bouton ou croix ;
- affichage du logo CEEN si l'image existe dans assets/logos/.
"""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
import webbrowser


BACKGROUND = "#f6eed9"
TITLE_BACKGROUND = "#efe6b8"
INK = "#3d2a0c"
BUTTON_BACKGROUND = "#f1e7bd"
LINK_FOREGROUND = "#6f4e00"

LOGO_FILENAME = "logo_CEEN_nagscreen.png"
LOGO_MAX_WIDTH = 300
LOGO_MAX_HEIGHT = 120

PURH_URL = "https://purh.univ-rouen.fr"
CEEN_URL = "https://ceen.hypotheses.org"
CEREDI_URL = "https://ceredi.hypotheses.org"
CEEN_EMAIL = "ceen_team@listes.univ-rouen.fr"
CEEN_MAILTO_URL = f"mailto:{CEEN_EMAIL}"


def _find_project_root(start: Path) -> Path:
    """Remonte l'arborescence jusqu'à trouver le dossier assets."""
    for candidate in [start, *start.parents]:
        if (candidate / "assets").exists():
            return candidate
    return start


def _resolve_logo_path() -> Path:
    """Retourne le chemin attendu du logo, sans garantir son existence."""
    project_root = _find_project_root(Path(__file__).resolve())
    return project_root / "assets" / "logos" / LOGO_FILENAME


class WelcomeDialog(tk.Toplevel):
    """Nagscreen d'ouverture de TEI Studio."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.title("Bienvenue dans TEI Studio")
        self.configure(background=BACKGROUND)
        self.resizable(False, False)

        self._logo_image: tk.PhotoImage | None = None

        self._build_widgets()
        self._bind_shortcuts()
        self._make_modal()
        self._center_on_parent(master)

    def _load_logo_image(self, path: Path) -> tk.PhotoImage:
        """Charge le logo et le réduit si sa taille native est excessive."""
        image = tk.PhotoImage(file=str(path))

        width = image.width()
        height = image.height()

        factor = max(
            1,
            (width + LOGO_MAX_WIDTH - 1) // LOGO_MAX_WIDTH,
            (height + LOGO_MAX_HEIGHT - 1) // LOGO_MAX_HEIGHT,
        )

        if factor > 1:
            return image.subsample(factor, factor)

        return image

    def _add_credit_link(self, parent: tk.Misc, text: str, url: str) -> None:
        """Ajoute un lien cliquable dans le bloc de crédits."""
        link = tk.Label(
            parent,
            text=text,
            font=("Georgia", 11, "underline"),
            foreground=LINK_FOREGROUND,
            background=BACKGROUND,
            cursor="hand2",
        )
        link.pack()
        link.bind("<Button-1>", lambda _event: webbrowser.open_new_tab(url))

    def _build_widgets(self) -> None:
        container = tk.Frame(self, background=BACKGROUND, padx=46, pady=38)
        container.pack(fill="both", expand=True)

        title = tk.Label(
            container,
            text="TEI Studio",
            font=("Georgia", 30, "bold"),
            foreground=INK,
            background=TITLE_BACKGROUND,
            padx=28,
            pady=14,
        )
        title.pack(fill="x")

        version = tk.Label(
            container,
            text="V. 2.0",
            font=("Georgia", 13, "bold"),
            foreground=INK,
            background=BACKGROUND,
        )
        version.pack(pady=(14, 0))

        logo_path = _resolve_logo_path()
        if logo_path.exists():
            try:
                self._logo_image = self._load_logo_image(logo_path)
                logo_label = tk.Label(
                    container,
                    image=self._logo_image,
                    background=BACKGROUND,
                    borderwidth=0,
                )
                logo_label.pack(pady=(22, 14))
            except tk.TclError:
                self._logo_image = None
        else:
            spacer = tk.Frame(container, background=BACKGROUND, height=18)
            spacer.pack()

        subtitle = tk.Label(
            container,
            text="Plate-forme d'édition critique de textes de théâtre",
            font=("Georgia", 12),
            foreground="black",
            background=BACKGROUND,
        )
        subtitle.pack(pady=(0, 16))

        credits = tk.Frame(container, background=BACKGROUND)
        credits.pack()

        author = tk.Label(
            credits,
            text="conçue et développée par T. Gheeraert",
            font=("Georgia", 11),
            foreground="black",
            background=BACKGROUND,
            justify="center",
        )
        author.pack()

        self._add_credit_link(
            credits,
            "Presses universitaires de Rouen et du Havre",
            PURH_URL,
        )
        self._add_credit_link(
            credits,
            "Chaire d'excellence en éditions numériques",
            CEEN_URL,
        )
        self._add_credit_link(
            credits,
            "CEREdI (UR 3229)",
            CEREDI_URL,
        )

        self._add_credit_link(
            credits,
            CEEN_EMAIL,
            CEEN_MAILTO_URL,
        )

        codex_credit = tk.Label(
            credits,
            text="\nCo-écrit avec Codex AI",
            font=("Georgia", 11),
            foreground="black",
            background=BACKGROUND,
            justify="center",
        )
        codex_credit.pack()

        button = tk.Button(
            container,
            text="Commencer",
            command=self.destroy,
            font=("Georgia", 11, "bold"),
            foreground="black",
            background=BUTTON_BACKGROUND,
            activebackground=TITLE_BACKGROUND,
            relief="ridge",
            borderwidth=2,
            width=26,
            default="active",
        )
        button.pack(pady=(24, 0))
        button.focus_set()

    def _bind_shortcuts(self) -> None:
        self.bind("<Return>", lambda _event: self.destroy())
        self.bind("<KP_Enter>", lambda _event: self.destroy())
        self.bind("<Escape>", lambda _event: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _make_modal(self) -> None:
        self.transient(self.master)
        self.grab_set()
        self.lift()
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))

    def _center_on_parent(self, parent: tk.Misc) -> None:
        self.update_idletasks()

        width = self.winfo_width()
        height = self.winfo_height()

        try:
            parent.update_idletasks()
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()

            x = parent_x + max((parent_width - width) // 2, 0)
            y = parent_y + max((parent_height - height) // 2, 0)
        except tk.TclError:
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x = max((screen_width - width) // 2, 0)
            y = max((screen_height - height) // 2, 0)

        self.geometry(f"{width}x{height}+{x}+{y}")


def show_welcome_dialog(parent: tk.Misc) -> None:
    """Affiche la fenêtre d'accueil et attend sa fermeture."""
    dialog = WelcomeDialog(parent)
    parent.wait_window(dialog)