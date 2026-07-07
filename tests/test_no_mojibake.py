"""Garde-fou anti-mojibake : aucune chaine corrompue dans le depot.

Les motifs sont construits avec ``chr()`` pour que ce fichier reste en pur
ASCII et ne se signale jamais lui-meme. Chaque motif est une sequence qui
n'apparait jamais en francais correct : U+00C3 suivi du second octet UTF-8
relu en cp1252 (sequence corrompue de e accent aigu, etc.), U+00E2 U+20AC
(apostrophes typographiques corrompues), U+FFFD. Le U+00C2 isole n'est pas
liste car il est legitime (par exemple dans le mot Age avec accent
circonflexe).
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCANNED_DIRS = ("src", "tests", "fixtures")

TEXT_SUFFIXES = {
    ".py", ".json", ".xml", ".txt", ".md", ".html", ".xsl", ".rng",
    ".toml", ".cfg", ".ini", ".js", ".css", ".tex", ".yaml", ".yml",
}

EXCLUDED_PARTS = {
    "_runtime",        # sorties de tests regenerees, gitignorees
    "__pycache__",
    ".venv",
    "legacy_reference",  # asset externe vendorise (widget minifie, U+FFFD volontaire)
}

_C3 = chr(0xC3)  # premier octet UTF-8 des lettres accentuees, relu en cp1252
MOJIBAKE_PATTERNS = [
    _C3 + chr(0xA9),   # e accent aigu corrompu
    _C3 + chr(0xA8),   # e accent grave corrompu
    _C3 + chr(0xA0),   # a accent grave corrompu (suivi d'un NBSP)
    _C3 + " ",         # a accent grave corrompu (NBSP retombe en espace)
    _C3 + chr(0xAA),   # e accent circonflexe corrompu
    _C3 + chr(0xA2),   # a accent circonflexe corrompu
    _C3 + chr(0xAE),   # i accent circonflexe corrompu
    _C3 + chr(0xAF),   # i trema corrompu
    _C3 + chr(0xB4),   # o accent circonflexe corrompu
    _C3 + chr(0xBB),   # u accent circonflexe corrompu
    _C3 + chr(0xB9),   # u accent grave corrompu
    _C3 + chr(0xA7),   # c cedille corrompu
    _C3 + chr(0xAB),   # e trema corrompu
    _C3 + chr(0xA3),   # a tilde corrompu (abreviation ancienne)
    _C3 + chr(0xBC),   # u trema corrompu (graphie ancienne)
    _C3 + chr(0xA4),   # a trema corrompu
    _C3 + chr(0xB6),   # o trema corrompu
    _C3 + chr(0xA6),   # ae ligature corrompue
    _C3 + chr(0x2030),  # E majuscule accent aigu corrompu
    _C3 + chr(0x0192),  # double encodage (U+00C3 + U+0192)
    _C3 + chr(0x201A),  # double encodage (U+00C3 + U+201A)
    chr(0xE2) + chr(0x20AC),  # apostrophes/guillemets typographiques corrompus
    chr(0xC5) + chr(0x201C),  # oe ligature corrompue
    chr(0xC5) + chr(0x2019),  # OE ligature corrompue
    chr(0xFFFD),       # caractere de remplacement U+FFFD
]


def _scannable_files() -> list[Path]:
    files: list[Path] = []
    for directory in SCANNED_DIRS:
        base = ROOT / directory
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if EXCLUDED_PARTS & set(path.parts):
                continue
            files.append(path)
    return files


def test_repository_contains_no_mojibake_literals() -> None:
    offenders: list[str] = []
    for path in _scannable_files():
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            offenders.append(f"{path.relative_to(ROOT)}: fichier non UTF-8")
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            if any(pattern in line for pattern in MOJIBAKE_PATTERNS):
                offenders.append(f"{path.relative_to(ROOT)}:{line_number}: {line.strip()[:80]}")
                break

    assert not offenders, "Mojibake detecte :" + chr(10) + chr(10).join(offenders)
