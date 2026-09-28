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

Piege additionnel deja rencontre sur ce projet : `geometry("LxH")` ne
dimensionne que la zone *client* d'une fenetre Windows. La barre de titre,
les bordures redimensionnables et une eventuelle barre de menu native
(`root.configure(menu=...)`) s'ajoutent par-dessus, en dehors de ce que
Tkinter rapporte. Une fenetre ajustee "pile" a la hauteur utile de l'ecran
deborde donc quand meme sous la barre des taches, de la hauteur de cette
decoration. fit_dialog_to_screen() mesure cette decoration reelle (via
GetWindowRect/GetClientRect) une fois la fenetre geometree une premiere
fois, puis corrige la hauteur client en consequence.
"""

from __future__ import annotations

import sys
import tkinter as tk


def _measured_chrome_height(window: tk.Misc) -> int:
    """Mesure la hauteur reelle de la decoration non-client de la fenetre
    (barre de titre, bordures, barre de menu native eventuelle) en comparant
    le rectangle exterieur Windows au rectangle client.

    Necessite que `window` ait deja une geometrie appliquee (sa largeur
    reelle peut influencer le nombre de lignes d'une barre de menu). Retourne
    0 si la mesure echoue ou hors Windows : dans ce cas fit_dialog_to_screen()
    se rabat sur son comportement precedent, sans correction de decoration.
    """
    if sys.platform != "win32":
        return 0
    try:
        import ctypes
        import ctypes.wintypes as wt

        user32 = ctypes.windll.user32
        hwnd = window.winfo_id()

        outer = wt.RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(outer)):
            return 0
        client = wt.RECT()
        if not user32.GetClientRect(hwnd, ctypes.byref(client)):
            return 0

        top_left = wt.POINT(0, 0)
        bottom_right = wt.POINT(client.right, client.bottom)
        user32.ClientToScreen(hwnd, ctypes.byref(top_left))
        user32.ClientToScreen(hwnd, ctypes.byref(bottom_right))

        window_height = outer.bottom - outer.top
        client_height = bottom_right.y - top_left.y
        chrome = window_height - client_height
        return chrome if 0 < chrome < window_height else 0
    except Exception:
        return 0


def _estimated_chrome_height() -> int:
    """Estimation de secours de la decoration (barre de titre + bordures +
    barre de menu) via les metriques systeme Windows, utilisee quand la
    mesure directe par rectangles (`_measured_chrome_height`) ne donne rien
    (fenetre pas encore reellement affichee par le compositeur, session sans
    decoration mesurable, etc.). Volontairement large : mieux vaut perdre
    quelques pixels de hauteur utile que masquer le bas de la fenetre.
    """
    if sys.platform != "win32":
        return 0
    try:
        import ctypes

        SM_CYCAPTION = 4
        SM_CYMENU = 15
        SM_CYSIZEFRAME = 33
        SM_CXPADDEDBORDER = 92

        user32 = ctypes.windll.user32
        caption = user32.GetSystemMetrics(SM_CYCAPTION)
        menu = user32.GetSystemMetrics(SM_CYMENU)
        frame = user32.GetSystemMetrics(SM_CYSIZEFRAME) + user32.GetSystemMetrics(
            SM_CXPADDEDBORDER
        )
        return caption + menu + 2 * frame
    except Exception:
        return 0


def _chrome_height(window: tk.Misc) -> int:
    return _measured_chrome_height(window) or _estimated_chrome_height()


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

    Pour que la barre de menu native soit prise en compte dans la mesure de
    decoration, appeler cette fonction apres avoir installe le menu de la
    fenetre (`root.configure(menu=...)`), pas avant.
    """
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    usable_height = min(_usable_screen_height(window, screen_height), screen_height)

    final_width = min(width, screen_width)
    final_height = min(height, usable_height)

    x = max((screen_width - final_width) // 2, 0)
    y = max((usable_height - final_height) // 2, 0)

    # Premier passage "naif" : necessaire pour disposer d'une fenetre reelle
    # (avec sa largeur definitive) sur laquelle mesurer la decoration Windows.
    window.geometry(f"{final_width}x{final_height}+{x}+{y}")
    window.update_idletasks()

    chrome = _chrome_height(window)
    if chrome:
        corrected_height = max(min(height, usable_height - chrome), 1)
        if corrected_height != final_height:
            final_height = corrected_height
            y = max((usable_height - chrome - final_height) // 2, 0)
            window.geometry(f"{final_width}x{final_height}+{x}+{y}")
