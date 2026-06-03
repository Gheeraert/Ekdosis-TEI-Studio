from __future__ import annotations

from ets.characters import (
    is_ambiguous_character_label,
    normalize_character_label,
    resolve_character_id,
    resolve_speaker_block,
)
from ets.domain import Character


def test_normalize_character_label_is_cautious_and_predictable() -> None:
    assert normalize_character_label("  HERMIONNE.  ") == "hermionne"
    assert normalize_character_label("CHŒUR !") == "choeur"
    assert normalize_character_label("ÉRIPHILE") == "eriphile"


def test_declared_aliases_resolve_hermione_variants() -> None:
    characters = [
        Character(
            id="char001",
            label="Hermione",
            aliases=["HERMIONNE.", "HERMIONE", "Hermione"],
        )
    ]

    assert resolve_character_id("HERMIONNE.", characters) == "char001"
    assert resolve_character_id("HERMIONE", characters) == "char001"
    assert resolve_character_id("Hermione", characters) == "char001"


def test_declared_aliases_resolve_iocaste_and_jocaste() -> None:
    characters = [
        Character(
            id="char002",
            label="Jocaste",
            aliases=["IOCASTE", "JOCASTE"],
        )
    ]

    assert resolve_character_id("IOCASTE", characters) == "char002"
    assert resolve_character_id("JOCASTE", characters) == "char002"


def test_no_resolution_without_declared_characters() -> None:
    assert resolve_character_id("HERMIONE", []) is None


def test_ambiguous_alias_is_detected_and_not_resolved() -> None:
    characters = [
        Character(id="char001", label="Hermione", aliases=["Reine"]),
        Character(id="char002", label="Andromaque", aliases=["REINE."]),
    ]

    assert is_ambiguous_character_label("reine", characters)
    assert resolve_character_id("REINE.", characters) is None


def test_resolve_speaker_block_requires_all_forms_to_share_one_id() -> None:
    characters = [Character(id="char001", label="Hermione", aliases=["HERMIONNE.", "HERMIONE"])]

    resolution = resolve_speaker_block(["HERMIONNE.", "HERMIONE"], characters)

    assert resolution.status == "resolved"
    assert resolution.character_id == "char001"


def test_resolve_speaker_block_reports_unresolved_form() -> None:
    characters = [Character(id="char001", label="Hermione", aliases=["HERMIONE"])]

    resolution = resolve_speaker_block(["HERMIONE", "INCONNU"], characters)

    assert resolution.status == "unresolved"
    assert resolution.problematic_forms == ("INCONNU",)


def test_resolve_speaker_block_reports_conflict_between_ids() -> None:
    characters = [
        Character(id="char001", label="Hermione", aliases=["HERMIONE"]),
        Character(id="char002", label="Andromaque", aliases=["ANDROMAQUE"]),
    ]

    resolution = resolve_speaker_block(["HERMIONE", "ANDROMAQUE"], characters)

    assert resolution.status == "conflict"
