from __future__ import annotations

import pytest

from ets.castlist import parse_castlist_text
from ets.domain import EditionConfig, Witness
from ets.validation import InputValidationError


def _config() -> EditionConfig:
    return EditionConfig(
        title="Phedre",
        author="Jean Racine",
        editor="Editeur",
        witnesses=[
            Witness(siglum="A", year="1677", description="A"),
            Witness(siglum="B", year="1687", description="B"),
        ],
        reference_witness=0,
    )


def _valid_castlist() -> str:
    return "\n".join(
        [
            "%%castlist%%",
            "",
            "%%head%%",
            "Acteurs",
            "Acteurs",
            "%%fin_head%%",
            "",
            '%%cast id=thesee role="Thésée" desc="roi d’Athènes" aliases="THESEE|THESEE.|THÉSÉE"%%',
            "Thésée, roi d’Athènes",
            "Thésée, Roi d’Athènes",
            "%%fin_cast%%",
            "",
            '%%cast id=phedre role="Phedre" desc="femme de Thesee" aliases="PHEDRE|PHEDRE."%%',
            "Phedre, femme de Thesee",
            "Phedre, Femme de Thesee",
            "%%fin_cast%%",
            "",
            "%%setting%%",
            "La scene est a Trezene.",
            "La Scene est a Trezene.",
            "%%fin_setting%%",
            "",
            "%%fin_castlist%%",
        ]
    )


def test_parse_minimal_valid_castlist_with_head_entries_and_setting() -> None:
    castlist = parse_castlist_text(_valid_castlist(), _config())

    assert castlist.head_readings == ["Acteurs", "Acteurs"]
    assert castlist.setting_readings == ["La scene est a Trezene.", "La Scene est a Trezene."]
    assert len(castlist.entries) == 2


def test_parse_cast_entry_attributes() -> None:
    castlist = parse_castlist_text(_valid_castlist(), _config())
    entry = castlist.entries[0]

    assert entry.id == "thesee"
    assert entry.role == "Thésée"
    assert entry.desc == "roi d’Athènes"
    assert entry.aliases == ["THESEE", "THESEE.", "THÉSÉE"]


def test_parse_preserves_semi_diplomatic_readings() -> None:
    castlist = parse_castlist_text(_valid_castlist(), _config())

    assert castlist.entries[0].readings == ["Thésée, roi d’Athènes", "Thésée, Roi d’Athènes"]


def test_parse_aliases_pipe_separator() -> None:
    text = _valid_castlist().replace('aliases="THESEE|THESEE.|THÉSÉE"', 'aliases="A|B|C"')

    castlist = parse_castlist_text(text, _config())

    assert castlist.entries[0].aliases == ["A", "B", "C"]


def test_parse_accepts_missing_desc_and_aliases_when_only_warnings_apply() -> None:
    text = "\n".join(
        [
            "%%castlist%%",
            '%%cast id=thesee role="Thesee"%%',
            "Thesee",
            "Thesee",
            "%%fin_cast%%",
            "%%fin_castlist%%",
        ]
    )

    castlist = parse_castlist_text(text, _config())

    assert castlist.entries[0].desc == ""
    assert castlist.entries[0].aliases == []


def test_parse_raises_on_blocking_structure_error() -> None:
    with pytest.raises(InputValidationError):
        parse_castlist_text("%%castlist%%", _config())
