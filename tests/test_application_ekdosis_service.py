from __future__ import annotations

from pathlib import Path

from ets.application import export_ekdosis, generate_ekdosis_from_text


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "ekdosis"


def _fixture_text(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def _witnesses_ab() -> list[dict[str, str]]:
    return [
        {"abbr": "A", "year": "1670", "desc": "edition originale"},
        {"abbr": "B", "year": "1671", "desc": "deuxieme edition"},
    ]


def test_ekdosis_body_is_generated_for_simple_scene() -> None:
    result = generate_ekdosis_from_text(
        text=_fixture_text("01_simple_scene.txt"),
        witnesses=_witnesses_ab(),
        reference_witness="A",
    )
    assert result.body.strip()
    assert r"\ekddiv{type=act, n=1, depth=2}" in result.body
    assert r"\stage{ACTE I.}" in result.body
    assert r"\speaker{IOCASTE}" in result.body
    assert r"\vnum{1}{" in result.body


def test_ekdosis_word_variant_uses_app_lem_rdg() -> None:
    result = generate_ekdosis_from_text(
        text=_fixture_text("02_word_variant.txt"),
        witnesses=_witnesses_ab(),
        reference_witness="A",
    )
    assert r"\app{" in result.body
    assert r"\lem[wit={A}]" in result.body
    assert r"\rdg[wit={B}]" in result.body


def test_ekdosis_whole_line_variant_uses_app_lem_rdg() -> None:
    result = generate_ekdosis_from_text(
        text=_fixture_text("03_whole_line_variant.txt"),
        witnesses=_witnesses_ab(),
        reference_witness="A",
    )
    assert r"\app{" in result.body
    assert r"\lem[wit={A}]" in result.body
    assert r"\rdg[wit={B}]" in result.body
    assert r"\vnum{1}{" in result.body


def test_ekdosis_shared_verse_numbering_is_preserved() -> None:
    result = generate_ekdosis_from_text(
        text=_fixture_text("04_shared_verse.txt"),
        witnesses=_witnesses_ab(),
        reference_witness="A",
    )
    assert r"\vnum{1.1}{" in result.body
    assert r"\vnum{1.2}{" in result.body


def test_ekdosis_speaker_change_creates_multiple_speeches() -> None:
    result = generate_ekdosis_from_text(
        text=_fixture_text("05_speaker_change.txt"),
        witnesses=_witnesses_ab(),
        reference_witness="A",
    )
    assert result.body.count(r"\begin{speech}") == 2
    assert r"\speaker{IOCASTE}" in result.body
    assert r"\speaker{OLYMPE}" in result.body


def test_ekdosis_act_scene_and_cast_are_rendered() -> None:
    result = generate_ekdosis_from_text(
        text=_fixture_text("06_act_scene_cast.txt"),
        witnesses=_witnesses_ab(),
        reference_witness="A",
    )
    assert r"\ekddiv{type=act, n=1, depth=2}" in result.body
    assert r"\ekddiv{type=scene, n=1, depth=3}" in result.body
    assert r"\stage{SCENE DEUXIEME.}" in result.body
    assert r"\stage{" in result.body


def test_ekdosis_special_characters_are_escaped() -> None:
    result = generate_ekdosis_from_text(
        text=_fixture_text("07_special_chars.txt"),
        witnesses=_witnesses_ab(),
        reference_witness="A",
    )
    assert r"AT\&T" in result.body
    assert r"50\%" in result.body
    assert r"\$prix" in result.body
    assert r"\#hash" in result.body
    assert r"\{bloc\}" in result.body
    assert r"sous\_score~" in result.body
    assert r"\enspace" in result.body
    assert r"\quad" in result.body
    assert r"\qquad" in result.body
    assert r"\hspace*{5em}" in result.body


def test_ekdosis_reference_witness_can_be_non_a() -> None:
    result = generate_ekdosis_from_text(
        text=_fixture_text("08_reference_witness_b.txt"),
        witnesses=[
            {"abbr": "A", "year": "1670", "desc": "edition A"},
            {"abbr": "B", "year": "1671", "desc": "edition B"},
            {"abbr": "C", "year": "1672", "desc": "edition C"},
        ],
        reference_witness="B",
    )
    assert r"\lem[wit={B}]" in result.body


def test_ekdosis_italics_are_rendered_without_alignment_break() -> None:
    result = generate_ekdosis_from_text(
        text=_fixture_text("09_italics.txt"),
        witnesses=_witnesses_ab(),
        reference_witness="A",
    )
    assert r"\textit{mot}" in result.body
    assert r"\_mot\_" not in result.body


def test_ekdosis_multitoken_italics_are_rendered_as_textit() -> None:
    text = """####ACTE I.####
####ACTE I.####

###SCENE PREMIERE.###
###SCENE PREMIERE.###

#IOCASTE#
#IOCASTE#

_la violence_ me gagne.
_la violence_ me gagne.
"""
    result = generate_ekdosis_from_text(
        text=text,
        witnesses=_witnesses_ab(),
        reference_witness="A",
    )
    assert r"\textit{la violence}" in result.body
    assert r"\_la" not in result.body
    assert r"violence\_" not in result.body


def test_ekdosis_full_document_contains_wrappers_and_witnesses() -> None:
    result = generate_ekdosis_from_text(
        text=_fixture_text("01_simple_scene.txt"),
        witnesses=_witnesses_ab(),
        reference_witness="A",
        metadata={"title": "Berenice", "author": "Racine", "editor": "Equipe ETS"},
    )
    assert r"\documentclass{book}" in result.full_document
    assert r"\begin{ekdosis}" in result.full_document
    assert r"\end{ekdosis}" in result.full_document
    assert r"\end{document}" in result.full_document
    assert r"\DeclareWitness{A}{1670}{edition originale}" in result.full_document
    assert r"\DeclareWitness{B}{1671}{deuxieme edition}" in result.full_document


def test_ekdosis_warnings_are_non_blocking_for_implicit_stage_markers() -> None:
    result = generate_ekdosis_from_text(
        text=_fixture_text("10_implicit_stage.txt"),
        witnesses=_witnesses_ab(),
        reference_witness="A",
    )
    assert result.body.strip()
    assert any("Implicit stage marker" in warning for warning in result.warnings)


def test_ekdosis_missing_witness_metadata_generates_warning_but_succeeds() -> None:
    result = generate_ekdosis_from_text(
        text=_fixture_text("01_simple_scene.txt"),
        witnesses=["A", "B"],
        reference_witness=0,
    )
    assert result.body.strip()
    assert result.warnings
    assert r"\DeclareWitness{A}{}{}" in result.full_document
    assert r"\DeclareWitness{B}{}{}" in result.full_document


def test_ekdosis_start_line_number_is_applied() -> None:
    result = generate_ekdosis_from_text(
        text=_fixture_text("01_simple_scene.txt"),
        witnesses=_witnesses_ab(),
        reference_witness="A",
        start_line_number=10,
    )
    assert r"\vnum{10}{" in result.body


def test_export_ekdosis_writes_tex_file() -> None:
    target = Path(__file__).resolve().parents[1] / "tests" / "_runtime" / "output_ekdosis_service.tex"
    written = export_ekdosis(r"\documentclass{book}", target)
    assert written == target.resolve()
    assert target.read_text(encoding="utf-8") == r"\documentclass{book}"
