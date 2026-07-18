"""Polices embarquées pour les sorties HTML (aperçu et site statique).

Les trois familles utilisées par la feuille XSLT dramatique (IM Fell DW Pica,
EB Garamond, Source Sans Pro) sont fournies en WOFF2 dans les ressources du
paquet (`ets/resources/fonts/`), sous licence SIL Open Font License. Aucune
requête vers un service externe (Google Fonts ou autre) ne doit être émise par
les pages générées.

Deux modes de diffusion :

- `render_font_face_css()` : règles ``@font-face`` avec URL relatives, pour un
  site statique qui copie les fichiers WOFF2 dans ses assets ;
- `render_inline_font_style()` : bloc ``<style>`` autonome avec les polices en
  data-URI base64, pour l'aperçu HTML autoporteur.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class FontFace:
    family: str
    filename: str
    unicode_range: str


_FONT_FACES: tuple[FontFace, ...] = (
    FontFace(
        family="EB Garamond",
        filename="eb-garamond-latin-ext.woff2",
        unicode_range=(
            "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, "
            "U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, "
            "U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF"
        ),
    ),
    FontFace(
        family="EB Garamond",
        filename="eb-garamond-latin.woff2",
        unicode_range=(
            "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, "
            "U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, "
            "U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD"
        ),
    ),
    FontFace(
        family="IM Fell DW Pica",
        filename="im-fell-dw-pica-latin.woff2",
        unicode_range=(
            "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, "
            "U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, "
            "U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD"
        ),
    ),
    FontFace(
        family="Source Sans Pro",
        filename="source-sans-pro-latin-ext.woff2",
        unicode_range=(
            "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, "
            "U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, "
            "U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF"
        ),
    ),
    FontFace(
        family="Source Sans Pro",
        filename="source-sans-pro-latin.woff2",
        unicode_range=(
            "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, "
            "U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, "
            "U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD"
        ),
    ),
)

FONT_STYLE_MARKER_CLASS = "ets-embedded-fonts"


def fonts_directory() -> Path:
    return Path(__file__).resolve().parents[1] / "resources" / "fonts"


def font_files() -> tuple[Path, ...]:
    directory = fonts_directory()
    return tuple(directory / face.filename for face in _FONT_FACES)


def _font_face_rule(face: FontFace, src: str) -> str:
    return (
        "@font-face {\n"
        f"  font-family: '{face.family}';\n"
        "  font-style: normal;\n"
        "  font-weight: 400;\n"
        "  font-display: swap;\n"
        f"  src: url({src}) format('woff2');\n"
        f"  unicode-range: {face.unicode_range};\n"
        "}"
    )


def render_font_face_css(base_href: str = "") -> str:
    """CSS ``@font-face`` avec des URL relatives (``base_href`` + nom de fichier)."""
    rules = [_font_face_rule(face, f"'{base_href}{face.filename}'") for face in _FONT_FACES]
    return "\n".join(rules) + "\n"


@lru_cache(maxsize=1)
def render_inline_font_style() -> str:
    """Bloc ``<style>`` autonome, polices incluses en data-URI base64."""
    directory = fonts_directory()
    rules = []
    for face in _FONT_FACES:
        data = (directory / face.filename).read_bytes()
        encoded = base64.b64encode(data).decode("ascii")
        rules.append(_font_face_rule(face, f"data:font/woff2;base64,{encoded}"))
    css = "\n".join(rules)
    return f'<style class="{FONT_STYLE_MARKER_CLASS}">\n{css}\n</style>'
