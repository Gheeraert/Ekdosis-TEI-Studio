from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
import re
import unicodedata

from ets.domain import Character, DramatisPersonae


_FINAL_PUNCTUATION_RE = re.compile(r"[\s.,;:!?]+$")
_SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class CharacterAuthority:
    aliases: dict[str, str]
    ambiguous_aliases: frozenset[str]


@dataclass(frozen=True)
class SpeakerResolution:
    status: Literal["resolved", "unresolved", "ambiguous", "conflict"]
    character_id: str | None = None
    problematic_forms: tuple[str, ...] = ()


def normalize_character_label(label: str) -> str:
    """Normalize a speaker or cast label for cautious authority matching."""
    normalized = _SPACE_RE.sub(" ", label.strip())
    normalized = _FINAL_PUNCTUATION_RE.sub("", normalized)
    normalized = normalized.lower().replace("œ", "oe").replace("æ", "ae")
    decomposed = unicodedata.normalize("NFD", normalized)
    without_accents = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return unicodedata.normalize("NFC", without_accents)


def build_character_authority(characters: list[Character]) -> CharacterAuthority:
    owners_by_alias: dict[str, set[str]] = {}
    for character in characters:
        aliases = [character.label, *character.aliases]
        for alias in aliases:
            normalized = normalize_character_label(alias)
            if not normalized:
                continue
            owners_by_alias.setdefault(normalized, set()).add(character.id)

    ambiguous_aliases = frozenset(
        alias for alias, character_ids in owners_by_alias.items() if len(character_ids) > 1
    )
    aliases = {
        alias: next(iter(character_ids))
        for alias, character_ids in owners_by_alias.items()
        if alias not in ambiguous_aliases and len(character_ids) == 1
    }
    return CharacterAuthority(aliases=aliases, ambiguous_aliases=ambiguous_aliases)


def characters_from_dramatis_personae(dramatis: DramatisPersonae) -> list[Character]:
    return [
        Character(id=entry.id, label=entry.role, aliases=list(entry.aliases))
        for entry in dramatis.entries
    ]


def resolve_character_id(label: str, characters: list[Character]) -> str | None:
    authority = build_character_authority(characters)
    normalized = normalize_character_label(label)
    if normalized in authority.ambiguous_aliases:
        return None
    return authority.aliases.get(normalized)


def is_ambiguous_character_label(label: str, characters: list[Character]) -> bool:
    authority = build_character_authority(characters)
    return normalize_character_label(label) in authority.ambiguous_aliases


def resolve_speaker_block(readings: list[str], characters: list[Character]) -> SpeakerResolution:
    authority = build_character_authority(characters)
    resolved_ids: set[str] = set()
    ambiguous_forms: list[str] = []
    unresolved_forms: list[str] = []

    for raw in readings:
        form = raw.strip()
        normalized = normalize_character_label(form)
        if not normalized:
            continue
        if normalized in authority.ambiguous_aliases:
            ambiguous_forms.append(form)
            continue
        character_id = authority.aliases.get(normalized)
        if character_id is None:
            unresolved_forms.append(form)
            continue
        resolved_ids.add(character_id)

    if ambiguous_forms:
        return SpeakerResolution(status="ambiguous", problematic_forms=tuple(ambiguous_forms))
    if unresolved_forms:
        return SpeakerResolution(status="unresolved", problematic_forms=tuple(unresolved_forms))
    if len(resolved_ids) > 1:
        return SpeakerResolution(
            status="conflict",
            problematic_forms=tuple(form.strip() for form in readings if form.strip()),
        )
    if len(resolved_ids) == 1:
        return SpeakerResolution(status="resolved", character_id=next(iter(resolved_ids)))
    return SpeakerResolution(status="unresolved", problematic_forms=())
