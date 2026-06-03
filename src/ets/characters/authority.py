from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from ets.domain import Character


_FINAL_PUNCTUATION_RE = re.compile(r"[\s.,;:!?]+$")
_SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class CharacterAuthority:
    aliases: dict[str, str]
    ambiguous_aliases: frozenset[str]


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


def resolve_character_id(label: str, characters: list[Character]) -> str | None:
    authority = build_character_authority(characters)
    normalized = normalize_character_label(label)
    if normalized in authority.ambiguous_aliases:
        return None
    return authority.aliases.get(normalized)


def is_ambiguous_character_label(label: str, characters: list[Character]) -> bool:
    authority = build_character_authority(characters)
    return normalize_character_label(label) in authority.ambiguous_aliases
