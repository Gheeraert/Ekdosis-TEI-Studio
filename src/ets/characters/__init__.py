from .authority import (
    CharacterAuthority,
    SpeakerResolution,
    build_character_authority,
    characters_from_dramatis_personae,
    is_ambiguous_character_label,
    normalize_character_label,
    resolve_character_id,
    resolve_speaker_block,
)

__all__ = [
    "CharacterAuthority",
    "SpeakerResolution",
    "build_character_authority",
    "characters_from_dramatis_personae",
    "is_ambiguous_character_label",
    "normalize_character_label",
    "resolve_character_id",
    "resolve_speaker_block",
]
