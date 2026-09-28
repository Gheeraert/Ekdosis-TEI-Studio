from __future__ import annotations

import tkinter as tk

import pytest

from ets.ui.tk import dialog_geometry


def _make_root() -> tk.Tk:
    try:
        root = tk.Tk()
    except tk.TclError as exc:  # pragma: no cover - depends on runtime display availability
        pytest.skip(f"Tk not available in this environment: {exc}")
    root.withdraw()
    return root


@pytest.fixture()
def root() -> tk.Tk:
    window = _make_root()
    try:
        yield window
    finally:
        window.destroy()


@pytest.fixture()
def toplevel(root: tk.Tk) -> tk.Toplevel:
    # Une vraie fenetre Toplevel, comme les boites de dialogue de
    # l'application (contrairement a `root`, qui reste masquee) : le
    # comportement de geometrie de Tk sur une fenetre sans widget mais
    # jamais rendue visible ne reflete pas l'usage reel.
    return tk.Toplevel(root)


def test_fit_dialog_to_screen_keeps_requested_size_when_it_fits(
    toplevel: tk.Toplevel, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(dialog_geometry, "_usable_screen_height", lambda window, screen_height: 650)
    monkeypatch.setattr(dialog_geometry, "_chrome_height", lambda window: 0)

    dialog_geometry.fit_dialog_to_screen(toplevel, 400, 300)
    toplevel.update_idletasks()

    assert toplevel.winfo_width() == 400
    assert toplevel.winfo_height() == 300


def test_fit_dialog_to_screen_shrinks_for_taskbar_and_window_chrome(
    toplevel: tk.Toplevel, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Zone de travail deja reduite par la barre des taches (usable_height),
    # a laquelle s'ajoute une decoration de fenetre mesuree ou estimee
    # (barre de titre + barre de menu) qui grignote encore la hauteur
    # client reellement disponible : c'est cette seconde reduction qui
    # manquait avant et laissait le bas de la fenetre sous la barre des
    # taches.
    monkeypatch.setattr(dialog_geometry, "_usable_screen_height", lambda window, screen_height: 650)
    monkeypatch.setattr(dialog_geometry, "_chrome_height", lambda window: 60)

    dialog_geometry.fit_dialog_to_screen(toplevel, 1200, 850)
    toplevel.update_idletasks()

    # 650 (zone de travail) - 60 (decoration de la fenetre) = 590 max.
    assert toplevel.winfo_height() <= 590
    assert toplevel.winfo_height() > 0
    # La largeur demandee tient sur l'ecran : elle n'a pas besoin d'etre reduite.
    assert toplevel.winfo_width() == 1200
    # La fenetre entiere (y compris sa decoration) reste au-dessus de la
    # barre des taches.
    assert toplevel.winfo_y() + toplevel.winfo_height() + 60 <= 650
