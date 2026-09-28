"""Ajustement de la geometrie des boites de dialogue a l'ecran disponible.

Sur certains PC portables, la barre des taches Windows reste affichee en
permanence et reduit la hauteur reellement disponible pour les fenetres,
sans que Tkinter n'en tienne compte (winfo_screenheight renvoie la hauteur
totale de l'ecran, barre des taches comprise). Une boite de dialogue dont
la hauteur demandee est proche de la hauteur de l'ecran se retrouve alors
avec son bas masque par la barre des taches, y compris ses boutons de
validation, sans qu'aucun ascenseur ne permette d'y acceder.

fit_dialog_to_screen() reduit et centre la geometrie demandee pour qu'elle
tienne dans la zone de travail reellement visible.
"""

from __future__ import annotations

import sys
import tkinter as tk


def _usable_screen_height(window: tk.Misc, screen_height: int) -> int:
    """Retourne la hauteur utile de l'ecran (hors barre des taches si connue)."""
    if sys.platform == "win32":
        try:
            import ctypes
            import ctypes.wintypes

            SPI_GETWORKAREA = 0x0030
            rect = ctypes.wintypes.RECT()
            ok = ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETWORKAREA, 0, ctypes.byref(rect), 0
            )
            if ok:
                work_height = rect.bottom - rect.top
                if 0 < work_height <= screen_height:
                    return work_height
        except Exception:
            pass

    # Repli prudent si l'API Windows n'est pas disponible (autre OS,
    # environnement restreint, etc.) : on reserve une marge raisonnable
    # pour une eventuelle barre des taches.
    return max(screen_height - 80, 480)


def fit_dialog_to_screen(window: tk.Misc, width: int, height: int) -> None:
    """Applique une geometrie centree qui tient dans la zone de travail visible.

    Le comportement est identique a un simple `window.geometry(f"{width}x{height}")`
    tant que la fenetre demandee tient dans l'ecran ; elle est seulement reduite
    et repositionnee quand ce n'est pas le cas.
    """
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    usable_height = min(_usable_screen_height(window, screen_height), screen_height)

    final_width = min(width, screen_width)
    final_height = min(height, usable_height)

    x = max((screen_width - final_width) // 2, 0)
    y = max((usable_height - final_height) // 2, 0)

    window.geometry(f"{final_width}x{final_height}+{x}+{y}")
