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

    report = validate_input_text(text, witness_count=len(config.witnesses))
    assert report.has_errors is False
    assert report.diagnostics == []


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


def test_pipeline_raises_input_validation_error_with_diagnostics() -> None:
    root = Path(__file__).resolve().parents[1]
    with pytest.raises(InputValidationError) as captured:
        run_pipeline(
            input_path=root / "fixtures" / "stable" / "britannicus_I.txt",
            config_path=root / "fixtures" / "known_issues" / "britannicus_scene_2_acte_2" / "config.json",
        )

    assert captured.value.diagnostics
    assert captured.value.diagnostics[0].code == "E_BLOCK_SIZE"
