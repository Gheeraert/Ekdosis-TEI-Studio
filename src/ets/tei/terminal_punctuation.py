"""Isolation de la ponctuation terminale avant le rendu TEI.

Transformation locale et pure des segments d'un ``CollatedText`` :

- quand la ponctuation terminale est identique dans le lemme et toutes les
  leçons d'un apparat, elle est extraite vers un ``LiteralTokenSegment`` qui
  suit l'apparat ;
- quand seule la ponctuation terminale varie (variante déjà classée
  ``minor_punctuation`` / ``punctuation_only``), le noyau lexical commun sort
  de l'apparat et l'apparat ne porte plus que sur la ponctuation.

La transformation n'opère que sur des chaînes Python, avant toute
sérialisation XML : la portée des italiques (marqueurs ``_``) est préservée
par construction, puisqu'on n'extrait qu'une ponctuation qui est le dernier
caractère non blanc du texte (donc après un éventuel ``_`` fermant).
Tout cas ambigu conserve exactement le comportement actuel.
"""

from __future__ import annotations

from dataclasses import replace

from ets.domain import (
    ApparatusTokenSegment,
    CollatedTokenSegment,
    LiteralTokenSegment,
)

TERMINAL_PUNCTUATION = {",", ".", ";", ":", "?", "!"}
DOUBLE_PUNCTUATION = {";", ":", "?", "!"}

NBSP = " "
# Le marqueur ETS "~" est normalement déjà converti en espace insécable en
# amont du générateur ; il n'est accepté ici que par robustesse et il est
# toujours renormalisé en  , jamais réémis tel quel dans la TEI.
NBSP_MARKERS = {NBSP, "~"}


def split_terminal_punctuation(text: str) -> tuple[str, str, str]:
    """Découpe ``text`` en (noyau, ponctuation terminale, espacement final).

    L'espacement final est la suite d'espaces simples ajoutée par la collation
    aux tokens non terminaux. La ponctuation terminale extractible est soit un
    signe simple (`,`, `.`, `;`, `:`, `?`, `!`), soit une ponctuation double
    précédée d'une espace insécable (`` ;`` etc.), renvoyée normalisée
    avec `` ``. Si rien n'est extractible, la ponctuation renvoyée est
    vide et le noyau vaut ``text`` privé de son espacement final.
    """
    core = text.rstrip(" ")
    spacing = text[len(core):]
    if not core:
        return core, "", spacing

    last = core[-1]
    if last not in TERMINAL_PUNCTUATION:
        return core, "", spacing

    remainder = core[:-1]
    punctuation = last
    if last in DOUBLE_PUNCTUATION and remainder and remainder[-1] in NBSP_MARKERS:
        remainder = remainder[:-1]
        punctuation = NBSP + last
    if remainder and (remainder[-1] in TERMINAL_PUNCTUATION or remainder[-1] in NBSP_MARKERS):
        # Séquence composite ("...", "?!", double marqueur) : ne rien extraire.
        return core, "", spacing
    return remainder, punctuation, spacing


def _plain(text: str) -> str:
    return text.replace("_", "")


def _is_markup_variant(texts: list[str]) -> bool:
    return len(set(texts)) > 1 and len({_plain(text) for text in texts}) == 1


def _splittable_readings(segment: ApparatusTokenSegment) -> list | None:
    readings = [segment.lemma, *segment.readings]
    texts = [reading.text for reading in readings]
    if not texts or any(not text for text in texts):
        return None
    if _is_markup_variant(texts):
        return None
    return readings


def _extract_common_terminal_punctuation(
    segment: ApparatusTokenSegment,
) -> list[CollatedTokenSegment] | None:
    """Cas 1 : ponctuation terminale identique dans toutes les leçons."""
    readings = _splittable_readings(segment)
    if readings is None:
        return None
    splits = [split_terminal_punctuation(reading.text) for reading in readings]
    punctuations = {punctuation for _, punctuation, _ in splits}
    spacings = {spacing for _, _, spacing in splits}
    if len(punctuations) != 1 or len(spacings) != 1:
        return None
    punctuation = next(iter(punctuations))
    if not punctuation:
        return None
    cores = [core for core, _, _ in splits]
    if any(not _plain(core).strip() for core in cores):
        return None
    new_readings = [replace(reading, text=core) for reading, core in zip(readings, cores)]
    return [
        replace(segment, lemma=new_readings[0], readings=new_readings[1:]),
        LiteralTokenSegment(text=punctuation + next(iter(spacings))),
    ]


def _isolate_punctuation_only_variant(
    segment: ApparatusTokenSegment,
    next_segment: CollatedTokenSegment | None,
) -> list[CollatedTokenSegment] | None:
    """Cas 2 : le noyau lexical est commun, seule la ponctuation varie."""
    if segment.candidate_class != "minor_punctuation" and segment.rule_code != "punctuation_only":
        return None
    readings = _splittable_readings(segment)
    if readings is None:
        return None
    splits = [split_terminal_punctuation(reading.text) for reading in readings]
    cores = {core for core, _, _ in splits}
    spacings = {spacing for _, _, spacing in splits}
    if len(cores) != 1 or len(spacings) != 1:
        return None
    core = next(iter(cores))
    if not _plain(core).strip():
        return None
    punctuations = [punctuation for _, punctuation, _ in splits]
    if len(set(punctuations)) <= 1:
        return None
    spacing = next(iter(spacings))
    if spacing and not (
        isinstance(next_segment, LiteralTokenSegment) and next_segment.text.strip()
    ):
        # L'espacement résiduel deviendrait un tail composé uniquement de
        # blancs, réécrit par ET.indent() : conserver le comportement actuel.
        return None
    new_readings = [
        replace(reading, text=punctuation)
        for reading, punctuation in zip(readings, punctuations)
    ]
    result: list[CollatedTokenSegment] = [
        LiteralTokenSegment(text=core),
        replace(segment, lemma=new_readings[0], readings=new_readings[1:]),
    ]
    if spacing:
        result.append(LiteralTokenSegment(text=spacing))
    return result


def normalize_terminal_punctuation_segments(
    segments: list[CollatedTokenSegment],
) -> list[CollatedTokenSegment]:
    """Renvoie une nouvelle liste de segments à ponctuation terminale isolée.

    Fonction pure : les segments d'entrée ne sont jamais mutés ; tout segment
    qui ne satisfait pas strictement l'un des deux cas est renvoyé tel quel.
    """
    result: list[CollatedTokenSegment] = []
    for index, segment in enumerate(segments):
        if isinstance(segment, ApparatusTokenSegment):
            next_segment = segments[index + 1] if index + 1 < len(segments) else None
            replacement = _extract_common_terminal_punctuation(segment)
            if replacement is None:
                replacement = _isolate_punctuation_only_variant(segment, next_segment)
            if replacement is not None:
                result.extend(replacement)
                continue
        result.append(segment)
    return result
