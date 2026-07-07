from __future__ import annotations

from pathlib import Path

import pytest

from ets.core import run_pipeline
from ets.domain import Character
from ets.parser import load_config
from ets.validation import InputValidationError, validate_input_text


def test_input_validator_reports_no_errors_on_stable_fixture() -> None:
    root = Path(__file__).resolve().parents[1]
    config = load_config(root / "fixtures" / "stable" / "config.json")
    text = (root / "fixtures" / "stable" / "input.txt").read_text(encoding="utf-8")

    report = validate_input_text(
        text,
        witness_count=len(config.witnesses),
        witness_sigla=[w.siglum for w in config.witnesses],
    )
    assert report.has_errors is False
    assert [diag for diag in report.diagnostics if diag.level.value == "ERROR"] == []


def _minimal_speaker_text(speaker_lines: list[str]) -> str:
    return "\n".join(
        [
            *["####ACTE I####"] * len(speaker_lines),
            "",
            *["###SCENE I###"] * len(speaker_lines),
            "",
            *[f"#{speaker}#" for speaker in speaker_lines],
            "",
            *["Je parle."] * len(speaker_lines),
        ]
    )


def test_character_validator_without_characters_emits_no_character_warning() -> None:
    report = validate_input_text(_minimal_speaker_text(["INCONNU", "INCONNU"]), witness_count=2)

    assert not [diag for diag in report.diagnostics if diag.code.startswith("W_CHARACTER_WHO_")]


def test_character_validator_known_speaker_emits_no_character_warning() -> None:
    characters = [Character(id="char001", label="Hermione", aliases=["HERMIONE"])]
    report = validate_input_text(
        _minimal_speaker_text(["HERMIONE", "HERMIONE"]),
        witness_count=2,
        characters=characters,
    )

    assert not [diag for diag in report.diagnostics if diag.code.startswith("W_CHARACTER_WHO_")]


def test_character_validator_unknown_speaker_emits_unresolved_warning() -> None:
    characters = [Character(id="char001", label="Hermione", aliases=["HERMIONE"])]
    report = validate_input_text(
        _minimal_speaker_text(["INCONNU", "INCONNU"]),
        witness_count=2,
        characters=characters,
    )

    warnings = [diag for diag in report.diagnostics if diag.code == "W_CHARACTER_WHO_UNRESOLVED"]
    assert warnings
    assert warnings[0].level.value == "WARNING"
    assert warnings[0].block_type == "speaker"
    assert "INCONNU" in warnings[0].message
    assert "Personnages > aliases" in warnings[0].message


def test_character_validator_ambiguous_speaker_emits_ambiguous_warning() -> None:
    characters = [
        Character(id="char001", label="Hermione", aliases=["REINE"]),
        Character(id="char002", label="Andromaque", aliases=["REINE."]),
    ]
    report = validate_input_text(
        _minimal_speaker_text(["REINE", "REINE"]),
        witness_count=2,
        characters=characters,
    )

    assert "W_CHARACTER_WHO_AMBIGUOUS" in {diag.code for diag in report.diagnostics}


def test_character_validator_conflicting_speaker_readings_emit_conflict_warning() -> None:
    characters = [
        Character(id="char001", label="Hermione", aliases=["HERMIONE"]),
        Character(id="char002", label="Andromaque", aliases=["ANDROMAQUE"]),
    ]
    report = validate_input_text(
        _minimal_speaker_text(["HERMIONE", "ANDROMAQUE"]),
        witness_count=2,
        characters=characters,
    )

    assert "W_CHARACTER_WHO_CONFLICT" in {diag.code for diag in report.diagnostics}


def test_input_validator_reports_malformed_parallel_block_with_context() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "fixtures" / "stable" / "britannicus_I.txt").read_text(encoding="utf-8")
    report = validate_input_text(text, witness_count=5)

    malformed = [diag for diag in report.diagnostics if diag.code == "E_BLOCK_SIZE"]
    assert malformed
    first = malformed[0]
    assert first.block_index == 159
    assert first.line_number is not None
    assert first.message.startswith("Malformed parallel block at index 159")
    assert first.act is not None
    assert first.scene is not None


def test_input_validator_detects_implicit_span_errors() -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "##ORESTE##",
            "##ORESTE##",
            "",
            "#ORESTE#",
            "#ORESTE#",
            "",
            "$$SET$$",
            "$$SET$$",
            "",
            "$$EVT$$",
            "$$EVT$$",
        ]
    )
    report = validate_input_text(text, witness_count=2)
    codes = {diag.code for diag in report.diagnostics}
    assert "E_IMPLICIT_NESTED" in codes
    assert "E_IMPLICIT_SPAN_UNCLOSED" in codes


def test_token_count_validation_accepts_balanced_ordinary_parallel_verse() -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "##A##",
            "##A##",
            "",
            "#A#",
            "#A#",
            "",
            "A B C",
            "X Y Z",
        ]
    )
    report = validate_input_text(text, witness_count=2, witness_sigla=["A", "B"])
    assert "E_TOKEN_COUNT_MISMATCH" not in {diag.code for diag in report.diagnostics}


def test_token_count_validation_rejects_unbalanced_ordinary_parallel_verse() -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "##A##",
            "##A##",
            "",
            "#A#",
            "#A#",
            "",
            "A B C",
            "A B",
        ]
    )
    report = validate_input_text(text, witness_count=2, witness_sigla=["A", "B"])
    mismatch = [diag for diag in report.diagnostics if diag.code == "E_TOKEN_COUNT_MISMATCH"]
    assert mismatch
    diag = mismatch[0]
    assert diag.block_type == "verse"
    assert diag.token_counts == [3, 2]
    assert diag.witness_labels == ["A", "B"]
    assert diag.line_number == 13
    assert diag.block_index == 4
    assert diag.scene == "SCENE I"
    assert diag.speaker == "A"
    assert diag.block_lines == ["A B C", "A B"]


def test_token_count_validation_skips_whole_line_variant_blocks() -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "##A##",
            "##A##",
            "",
            "#A#",
            "#A#",
            "",
            "##### A B C D",
            "##### A",
        ]
    )
    report = validate_input_text(text, witness_count=2, witness_sigla=["A", "B"])
    assert "E_TOKEN_COUNT_MISMATCH" not in {diag.code for diag in report.diagnostics}


def test_token_count_validation_handles_tildes_as_non_split_spaces() -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "##A##",
            "##A##",
            "",
            "#A#",
            "#A#",
            "",
            "Le~crime~en~sa~famille A",
            "Le~crime~en~sa~famille B",
        ]
    )
    report = validate_input_text(text, witness_count=2, witness_sigla=["A", "B"])
    assert "E_TOKEN_COUNT_MISMATCH" not in {diag.code for diag in report.diagnostics}


def test_token_count_validation_handles_multiple_spaces_stably() -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "##A##",
            "##A##",
            "",
            "#A#",
            "#A#",
            "",
            "A  B   C",
            "A B C",
        ]
    )
    report = validate_input_text(text, witness_count=2, witness_sigla=["A", "B"])
    assert "E_TOKEN_COUNT_MISMATCH" not in {diag.code for diag in report.diagnostics}


def test_token_count_validation_applies_to_non_verse_collatable_blocks() -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "##ALPHA## ##BETA##",
            "##ALPHA##",
            "",
            "#ALPHA#",
            "#ALPHA#",
            "",
            "Bonjour",
            "Bonjour",
        ]
    )
    report = validate_input_text(text, witness_count=2, witness_sigla=["A", "B"])
    mismatch = [diag for diag in report.diagnostics if diag.code == "E_TOKEN_COUNT_MISMATCH"]
    assert mismatch
    assert mismatch[0].block_type == "cast"
    assert mismatch[0].token_counts == [2, 1]


def test_pipeline_raises_input_validation_error_with_diagnostics() -> None:
    root = Path(__file__).resolve().parents[1]
    with pytest.raises(InputValidationError) as captured:
        run_pipeline(
            input_path=root / "fixtures" / "stable" / "britannicus_I.txt",
            config_path=root / "fixtures" / "known_issues" / "britannicus_scene_2_acte_2" / "config.json",
        )

    assert captured.value.diagnostics
    assert captured.value.diagnostics[0].code == "E_BLOCK_SIZE"


def test_pipeline_surfaces_token_count_mismatch_during_input_validation() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = root / "tests" / "_runtime"
    runtime.mkdir(exist_ok=True)
    config_path = runtime / "validator_token_mismatch_config.json"
    input_path = runtime / "validator_token_mismatch_input.txt"
    config_path.write_text(
        """
        {
          "Prénom de l'auteur": "Jean",
          "Nom de l'auteur": "Racine",
          "Titre de la pièce": "Test",
          "Nom de l'éditeur (vous)": "Editeur",
          "Prénom de l'éditeur": "Test",
          "Temoins": [
            {"abbr": "A", "year": "1667", "desc": "A"},
            {"abbr": "B", "year": "1671", "desc": "B"}
          ],
          "reference_witness": 0
        }
        """.strip(),
        encoding="utf-8",
    )
    input_path.write_text(
        "\n".join(
            [
                "####ACTE I####",
                "####ACTE I####",
                "",
                "###SCENE I###",
                "###SCENE I###",
                "",
                "##A##",
                "##A##",
                "",
                "#A#",
                "#A#",
                "",
                "Un deux trois",
                "Un deux",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(InputValidationError) as captured:
        run_pipeline(input_path=input_path, config_path=config_path)
    assert any(diag.code == "E_TOKEN_COUNT_MISMATCH" for diag in captured.value.diagnostics)


def test_minimal_valid_markers_remain_valid() -> None:
    text = "\n".join(
        [
            "####ACTE I.####",
            "####ACTE I.####",
            "",
            "###SCENE PREMIERE.###",
            "###SCENE PREMIERE.###",
            "",
            "##IOCASTE,## ##OLYMPE.##",
            "##IOCASTE,## ##OLYMPE.##",
            "",
            "#IOCASTE.#",
            "#IOCASTE.#",
            "",
            "Oui je viens en son _temple_ adorer l'Eternel",
            "Oui je viens en son _temple_ adorer l'Eternel",
        ]
    )
    report = validate_input_text(text, witness_count=2)
    assert report.has_errors is False


def test_detects_speaker_with_two_hashes_before_verse_without_speaker() -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "##ORESTE##",
            "##ORESTE##",
            "",
            "Je parle.",
            "Je parle.",
        ]
    )
    report = validate_input_text(text, witness_count=2)
    codes = [diag.code for diag in report.diagnostics]
    assert "E_SPEAKER_MARKER_TOO_MANY_HASHES" in codes
    assert "E_VERSE_WITHOUT_SPEAKER" not in codes
    diag = next(diag for diag in report.diagnostics if diag.code == "E_SPEAKER_MARKER_TOO_MANY_HASHES")
    assert diag.line_number == 7


def test_detects_mixed_marker_block() -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "#ORESTE#",
            "##ORESTE##",
        ]
    )
    report = validate_input_text(text, witness_count=2)
    assert "E_MARKER_MIXED_BLOCK" in {diag.code for diag in report.diagnostics}


@pytest.mark.parametrize("bad_line", ["**entre", "entre**", "***entre***"])
def test_rejects_malformed_stage_markers(bad_line: str) -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "#ORESTE#",
            "#ORESTE#",
            "",
            bad_line,
            bad_line,
        ]
    )
    report = validate_input_text(text, witness_count=2)
    assert "E_STAGE_MARKER_MALFORMED" in {diag.code for diag in report.diagnostics}


def test_whole_line_variant_remains_valid() -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "#ORESTE#",
            "#ORESTE#",
            "",
            "##### (lacune)",
            "##### (lacune)",
        ]
    )
    report = validate_input_text(text, witness_count=2)
    assert "E_WHOLE_LINE_VARIANT_MALFORMED" not in {diag.code for diag in report.diagnostics}


def test_shared_verse_valid_case_still_valid() -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "#ORESTE#",
            "#ORESTE#",
            "",
            "Mais en sont-ils aux mains~?***",
            "Mais en sont-ils aux mains~?***",
            "",
            "***Du haut de la muraille,",
            "***Du haut de la muraille,",
        ]
    )
    report = validate_input_text(text, witness_count=2)
    assert report.has_errors is False


def test_shared_verse_three_fragments_valid_case_still_valid() -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "#A#",
            "#A#",
            "",
            "Fragment d'ouverture***",
            "Fragment d'ouverture***",
            "",
            "#B#",
            "#B#",
            "",
            "***fragment du milieu***",
            "***fragment du milieu***",
            "",
            "#C#",
            "#C#",
            "",
            "***fragment de fermeture",
            "***fragment de fermeture",
        ]
    )
    report = validate_input_text(text, witness_count=2)
    assert report.has_errors is False


def test_rejects_malformed_shared_verse_marker() -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "#ORESTE#",
            "#ORESTE#",
            "",
            "****Du haut de la muraille,",
            "****Du haut de la muraille,",
        ]
    )
    report = validate_input_text(text, witness_count=2)
    assert "E_SHARED_VERSE_MARKER_MALFORMED" in {diag.code for diag in report.diagnostics}


@pytest.mark.parametrize(
    "bad_line,expected_code",
    [
        ("#ORESTE##", "E_HASH_MARKER_MALFORMED"),
        ("##ORESTE###", "E_HASH_MARKER_MALFORMED"),
        ("###SCENE I####", "E_HASH_MARKER_MALFORMED"),
        ("####ACTE I#####", "E_HASH_MARKER_MALFORMED"),
        ("##NOM#", "E_HASH_MARKER_MALFORMED"),
        ("#NOM##", "E_HASH_MARKER_MALFORMED"),
        ("NOM#", "E_HASH_MARKER_MALFORMED"),
    ],
)
def test_rejects_hash_marker_with_parasitic_hashes(bad_line: str, expected_code: str) -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            bad_line,
            bad_line,
        ]
    )
    report = validate_input_text(text, witness_count=2)
    assert expected_code in {diag.code for diag in report.diagnostics}


def test_plain_verse_without_hash_remains_accepted() -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "#ORESTE#",
            "#ORESTE#",
            "",
            "Je parle sans dièse.",
            "Je parle sans dièse.",
        ]
    )
    report = validate_input_text(text, witness_count=2)
    codes = {diag.code for diag in report.diagnostics}
    assert "E_HASH_MARKER_MALFORMED" not in codes


@pytest.mark.parametrize("bad_line", ["######foo", "######foo bar", "##### foo#bar"])
def test_rejects_whole_line_variant_with_parasitic_hashes(bad_line: str) -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "#A#",
            "#A#",
            "",
            bad_line,
            bad_line,
        ]
    )
    report = validate_input_text(text, witness_count=2)
    assert "E_HASH_MARKER_MALFORMED" in {diag.code for diag in report.diagnostics}


@pytest.mark.parametrize("bad_line", ["**entre***", "***entre**", "****entre****"])
def test_rejects_hybrid_stage_and_shared_verse_markers(bad_line: str) -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "#A#",
            "#A#",
            "",
            bad_line,
            bad_line,
        ]
    )
    report = validate_input_text(text, witness_count=2)
    codes = {diag.code for diag in report.diagnostics}
    assert ("E_STAGE_MARKER_MALFORMED" in codes) or ("E_SHARED_VERSE_MARKER_MALFORMED" in codes)


def test_single_name_cast_before_verse_is_suspect_even_after_previous_speaker() -> None:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "#A#",
            "#A#",
            "",
            "Bonjour",
            "Bonjour",
            "",
            "##B##",
            "##B##",
            "",
            "Je parle",
            "Je parle",
        ]
    )
    report = validate_input_text(text, witness_count=2)
    codes = {diag.code for diag in report.diagnostics}
    assert "E_SPEAKER_MARKER_TOO_MANY_HASHES" in codes


def _stanza_text(stanza_blocks: list[str], witness_count: int = 4) -> str:
    prefix = [
        *["####ACTE I####"] * witness_count,
        "",
        *["###SCENE I###"] * witness_count,
        "",
        *["#CHOEUR#"] * witness_count,
        "",
    ]
    return "\n".join(prefix + stanza_blocks)


def test_accepts_valid_distique_stanza() -> None:
    text = _stanza_text(
        [
            *["%%strophe subtype=distique rhyme=aa%%"] * 4,
            "",
            *["=12=Que vous semble, mes soeurs"] * 4,
            "",
            *["=10=D'Esther qui tombe"] * 4,
            "",
            *["%%fin_strophe%%"] * 4,
        ]
    )
    report = validate_input_text(text, witness_count=4, witness_sigla=["A", "B", "C", "D"])
    assert report.has_errors is False


def test_rejects_forbidden_stanza_type_attribute() -> None:
    text = _stanza_text([*["%%strophe type=distique%%"] * 4])
    report = validate_input_text(text, witness_count=4)
    assert "E_STANZA_TYPE_ATTRIBUTE_FORBIDDEN" in {diag.code for diag in report.diagnostics}


def test_rejects_metrical_marker_outside_stanza() -> None:
    text = _stanza_text([*["=12=Je parle"] * 4])
    report = validate_input_text(text, witness_count=4)
    assert "E_METRICAL_MARKER_OUTSIDE_STANZA" in {diag.code for diag in report.diagnostics}


def test_rejects_stanza_verse_without_meter() -> None:
    text = _stanza_text(
        [
            *["%%strophe subtype=distique rhyme=aa%%"] * 4,
            "",
            *["Je parle"] * 4,
        ]
    )
    report = validate_input_text(text, witness_count=4)
    assert "E_STANZA_VERSE_WITHOUT_MET" in {diag.code for diag in report.diagnostics}


def test_rejects_unclosed_stanza() -> None:
    text = _stanza_text(
        [
            *["%%strophe subtype=distique rhyme=aa%%"] * 4,
            "",
            *["=12=Je parle"] * 4,
        ]
    )
    report = validate_input_text(text, witness_count=4)
    assert "E_STANZA_UNCLOSED" in {diag.code for diag in report.diagnostics}


def test_rejects_stanza_close_without_open() -> None:
    text = _stanza_text([*["%%fin_strophe%%"] * 4])
    report = validate_input_text(text, witness_count=4)
    assert "E_STANZA_CLOSE_WITHOUT_OPEN" in {diag.code for diag in report.diagnostics}


def test_rejects_distique_with_three_verses() -> None:
    text = _stanza_text(
        [
            *["%%strophe subtype=distique%%"] * 4,
            "",
            *["=12=Un"] * 4,
            "",
            *["=10=Deux"] * 4,
            "",
            *["=08=Trois"] * 4,
            "",
            *["%%fin_strophe%%"] * 4,
        ]
    )
    report = validate_input_text(text, witness_count=4)
    assert "E_STANZA_SUBTYPE_COUNT_MISMATCH" in {diag.code for diag in report.diagnostics}


def test_rejects_rhyme_with_three_verses() -> None:
    text = _stanza_text(
        [
            *["%%strophe rhyme=aa%%"] * 4,
            "",
            *["=12=Un"] * 4,
            "",
            *["=10=Deux"] * 4,
            "",
            *["=08=Trois"] * 4,
            "",
            *["%%fin_strophe%%"] * 4,
        ]
    )
    report = validate_input_text(text, witness_count=4)
    assert "E_STANZA_RHYME_COUNT_MISMATCH" in {diag.code for diag in report.diagnostics}


def test_rejects_stanza_metrical_value_variation_between_witnesses() -> None:
    text = _stanza_text(
        [
            *["%%strophe subtype=distique rhyme=aa%%"] * 4,
            "",
            "=12=Un vers",
            "=10=Un vers",
            "=12=Un vers",
            "=12=Un vers",
        ]
    )
    report = validate_input_text(text, witness_count=4, witness_sigla=["A", "B", "C", "D"])
    assert "E_STANZA_METRICAL_VALUE_VARIATION" in {diag.code for diag in report.diagnostics}


def test_accepts_whole_line_variant_with_meter_inside_stanza() -> None:
    text = _stanza_text(
        [
            *["%%strophe%%"] * 4,
            "",
            *["#####=12=Un vers variant"] * 4,
            "",
            *["%%fin_strophe%%"] * 4,
        ]
    )
    report = validate_input_text(text, witness_count=4)
    assert report.has_errors is False


def test_accepts_whole_line_lacuna_with_meter_inside_stanza() -> None:
    for lacuna in ["#####=12=(lacune)", "#####=12= (lacune)"]:
        text = _stanza_text(
            [
                *["%%strophe%%"] * 4,
                "",
                *[lacuna] * 4,
                "",
                *["%%fin_strophe%%"] * 4,
            ]
        )
        report = validate_input_text(text, witness_count=4)
        assert report.has_errors is False


def test_rejects_empty_metered_whole_line_variant_inside_stanza() -> None:
    for empty_variant in ["#####=12=", "#####=12=   "]:
        text = _stanza_text(
            [
                *["%%strophe%%"] * 4,
                "",
                *[empty_variant] * 4,
                "",
                *["%%fin_strophe%%"] * 4,
            ]
        )
        report = validate_input_text(text, witness_count=4)
        assert "E_WHOLE_LINE_VARIANT_MALFORMED" in {diag.code for diag in report.diagnostics}


def test_rejects_meter_before_whole_line_variant_marker_inside_stanza() -> None:
    text = _stanza_text(
        [
            *["%%strophe%%"] * 4,
            "",
            *["=12=#####Un vers variant"] * 4,
            "",
            *["%%fin_strophe%%"] * 4,
        ]
    )
    report = validate_input_text(text, witness_count=4)
    assert report.has_errors is True


def test_rejects_stanza_whole_line_variant_with_parasitic_hash() -> None:
    text = _stanza_text(
        [
            *["%%strophe%%"] * 4,
            "",
            *["#####=12=foo#bar"] * 4,
            "",
            *["%%fin_strophe%%"] * 4,
        ]
    )
    report = validate_input_text(text, witness_count=4)
    assert "E_HASH_MARKER_MALFORMED" in {diag.code for diag in report.diagnostics}
