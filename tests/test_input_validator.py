from __future__ import annotations

from pathlib import Path

import pytest

from ets.core import run_pipeline
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
          "PrÃƒÂ©nom de l'auteur": "Jean",
          "Nom de l'auteur": "Racine",
          "Titre de la piÃƒÂ¨ce": "Test",
          "NumÃƒÂ©ro de l'acte": "1",
          "NumÃƒÂ©ro de la scÃƒÂ¨ne": "1",
          "NumÃƒÂ©ro du vers de dÃƒÂ©part": 1,
          "Nom de l'ÃƒÂ©diteur (vous)": "Editeur",
          "PrÃƒÂ©nom de l'ÃƒÂ©diteur": "Test",
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
