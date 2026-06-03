from __future__ import annotations

from ets.castlist import validate_castlist_text
from ets.domain import EditionConfig, Witness


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


def _codes(text: str) -> set[str]:
    return {diagnostic.code for diagnostic in validate_castlist_text(text, _config()).diagnostics}


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
            '%%cast id=thesee role="Thesee" desc="roi d Athenes" aliases="THESEE|THESEE."%%',
            "Thesee, roi d Athenes",
            "Thesee, Roi d Athenes",
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


def test_valid_castlist_has_no_blocking_error() -> None:
    report = validate_castlist_text(_valid_castlist(), _config())

    assert report.has_errors is False


def test_missing_castlist_open_is_error() -> None:
    assert "E_CASTLIST_MISSING_OPEN" in _codes("%%fin_castlist%%")


def test_missing_castlist_close_is_error() -> None:
    assert "E_CASTLIST_MISSING_CLOSE" in _codes("%%castlist%%")


def test_unclosed_cast_block_is_error() -> None:
    text = "\n".join(
        [
            "%%castlist%%",
            '%%cast id=thesee role="Thesee" desc="roi" aliases="THESEE"%%',
            "Thesee",
            "Thesee",
            "%%fin_castlist%%",
        ]
    )

    assert "E_CASTLIST_BLOCK_UNCLOSED" in _codes(text)


def test_unclosed_head_block_is_error() -> None:
    text = "\n".join(["%%castlist%%", "%%head%%", "Acteurs", "Acteurs", "%%fin_castlist%%"])

    assert "E_CASTLIST_BLOCK_UNCLOSED" in _codes(text)


def test_unclosed_setting_block_is_error() -> None:
    text = "\n".join(["%%castlist%%", "%%setting%%", "Lieu", "Lieu", "%%fin_castlist%%"])

    assert "E_CASTLIST_BLOCK_UNCLOSED" in _codes(text)


def test_unknown_block_marker_is_error() -> None:
    text = "\n".join(["%%castlist%%", "%%foo%%", "%%fin_castlist%%"])

    assert "E_CASTLIST_UNKNOWN_MARKER" in _codes(text)


def test_content_before_castlist_open_is_error() -> None:
    text = "\n".join(["Acteurs", "%%castlist%%", "%%fin_castlist%%"])

    assert "E_CASTLIST_CONTENT_BEFORE_OPEN" in _codes(text)


def test_unknown_alias_attribute_is_error() -> None:
    text = "\n".join(
        [
            "%%castlist%%",
            '%%cast id=thesee role="Thesee" desc="roi" alias="THESEE"%%',
            "Thesee",
            "Thesee",
            "%%fin_cast%%",
            "%%fin_castlist%%",
        ]
    )

    assert "E_CAST_ATTR_UNKNOWN" in _codes(text)


def test_unknown_cast_attribute_is_error() -> None:
    text = "\n".join(
        [
            "%%castlist%%",
            '%%cast id=thesee role="Thesee" desc="roi" aliases="THESEE" foo="bar"%%',
            "Thesee",
            "Thesee",
            "%%fin_cast%%",
            "%%fin_castlist%%",
        ]
    )

    assert "E_CAST_ATTR_UNKNOWN" in _codes(text)


def test_unquoted_role_attribute_is_malformed_error() -> None:
    text = "\n".join(
        [
            "%%castlist%%",
            '%%cast id=thesee role=Thesee desc="roi" aliases="THESEE"%%',
            "Thesee",
            "Thesee",
            "%%fin_cast%%",
            "%%fin_castlist%%",
        ]
    )

    assert "E_CAST_ATTR_MALFORMED" in _codes(text)


def test_unclosed_attribute_quote_is_malformed_error() -> None:
    text = "\n".join(
        [
            "%%castlist%%",
            '%%cast id=thesee role="Thesee desc="roi" aliases="THESEE"%%',
            "Thesee",
            "Thesee",
            "%%fin_cast%%",
            "%%fin_castlist%%",
        ]
    )

    assert "E_CAST_ATTR_MALFORMED" in _codes(text)


def test_duplicate_cast_attribute_is_error() -> None:
    text = "\n".join(
        [
            "%%castlist%%",
            '%%cast id=thesee id=helene role="Thesee" desc="roi" aliases="THESEE"%%',
            "Thesee",
            "Thesee",
            "%%fin_cast%%",
            "%%fin_castlist%%",
        ]
    )

    assert "E_CAST_ATTR_DUPLICATE" in _codes(text)


def test_cast_without_id_is_error() -> None:
    text = "\n".join(
        [
            "%%castlist%%",
            '%%cast role="Thesee" desc="roi" aliases="THESEE"%%',
            "Thesee",
            "Thesee",
            "%%fin_cast%%",
            "%%fin_castlist%%",
        ]
    )

    assert "E_CAST_ID_MISSING" in _codes(text)


def test_cast_without_role_is_error() -> None:
    text = "\n".join(
        [
            "%%castlist%%",
            '%%cast id=thesee desc="roi" aliases="THESEE"%%',
            "Thesee",
            "Thesee",
            "%%fin_cast%%",
            "%%fin_castlist%%",
        ]
    )

    assert "E_CAST_ROLE_MISSING" in _codes(text)


def test_invalid_cast_id_is_error() -> None:
    text = "\n".join(
        [
            "%%castlist%%",
            '%%cast id=1thesee role="Thesee" desc="roi" aliases="THESEE"%%',
            "Thesee",
            "Thesee",
            "%%fin_cast%%",
            "%%fin_castlist%%",
        ]
    )

    assert "E_CAST_ID_INVALID" in _codes(text)


def test_duplicate_cast_id_is_error() -> None:
    text = "\n".join(
        [
            "%%castlist%%",
            '%%cast id=thesee role="Thesee" desc="roi" aliases="THESEE"%%',
            "Thesee",
            "Thesee",
            "%%fin_cast%%",
            '%%cast id=thesee role="Thesee" desc="roi" aliases="THESEE"%%',
            "Thesee",
            "Thesee",
            "%%fin_cast%%",
            "%%fin_castlist%%",
        ]
    )

    assert "E_CAST_ID_DUPLICATE" in _codes(text)


def test_duplicate_head_block_is_error() -> None:
    text = "\n".join(
        [
            "%%castlist%%",
            "%%head%%",
            "Acteurs",
            "Acteurs",
            "%%fin_head%%",
            "%%head%%",
            "Personnages",
            "Personnages",
            "%%fin_head%%",
            '%%cast id=thesee role="Thesee" desc="roi" aliases="THESEE"%%',
            "Thesee",
            "Thesee",
            "%%fin_cast%%",
            "%%fin_castlist%%",
        ]
    )

    assert "E_CASTLIST_DUPLICATE_HEAD" in _codes(text)


def test_duplicate_setting_block_is_error() -> None:
    text = "\n".join(
        [
            "%%castlist%%",
            '%%cast id=thesee role="Thesee" desc="roi" aliases="THESEE"%%',
            "Thesee",
            "Thesee",
            "%%fin_cast%%",
            "%%setting%%",
            "Lieu",
            "Lieu",
            "%%fin_setting%%",
            "%%setting%%",
            "Autre lieu",
            "Autre lieu",
            "%%fin_setting%%",
            "%%fin_castlist%%",
        ]
    )

    assert "E_CASTLIST_DUPLICATE_SETTING" in _codes(text)


def test_no_cast_entry_is_error() -> None:
    text = "\n".join(["%%castlist%%", "%%head%%", "Acteurs", "Acteurs", "%%fin_head%%", "%%fin_castlist%%"])

    assert "E_CASTLIST_NO_CAST_ENTRY" in _codes(text)


def test_cast_reading_count_mismatch_is_error() -> None:
    text = "\n".join(
        [
            "%%castlist%%",
            '%%cast id=thesee role="Thesee" desc="roi" aliases="THESEE"%%',
            "Thesee",
            "%%fin_cast%%",
            "%%fin_castlist%%",
        ]
    )

    assert "E_CAST_READING_COUNT_MISMATCH" in _codes(text)


def test_head_reading_count_mismatch_is_error() -> None:
    text = "\n".join(["%%castlist%%", "%%head%%", "Acteurs", "%%fin_head%%", "%%fin_castlist%%"])

    assert "E_CAST_HEAD_READING_COUNT_MISMATCH" in _codes(text)


def test_setting_reading_count_mismatch_is_error() -> None:
    text = "\n".join(["%%castlist%%", "%%setting%%", "Lieu", "%%fin_setting%%", "%%fin_castlist%%"])

    assert "E_CAST_SETTING_READING_COUNT_MISMATCH" in _codes(text)


def test_blank_lines_inside_block_are_ignored_not_empty_witnesses() -> None:
    text = "\n".join(
        [
            "%%castlist%%",
            '%%cast id=thesee role="Thesee" desc="roi" aliases="THESEE"%%',
            "",
            "Thesee",
            "",
            "%%fin_cast%%",
            "%%fin_castlist%%",
        ]
    )

    assert "E_CAST_READING_COUNT_MISMATCH" in _codes(text)


def test_missing_desc_is_non_blocking_warning() -> None:
    text = "\n".join(
        [
            "%%castlist%%",
            '%%cast id=thesee role="Thesee" aliases="THESEE"%%',
            "Thesee",
            "Thesee",
            "%%fin_cast%%",
            "%%fin_castlist%%",
        ]
    )
    report = validate_castlist_text(text, _config())

    assert report.has_errors is False
    assert "W_CAST_DESC_EMPTY" in {diagnostic.code for diagnostic in report.diagnostics}


def test_missing_aliases_is_non_blocking_warning() -> None:
    text = "\n".join(
        [
            "%%castlist%%",
            '%%cast id=thesee role="Thesee" desc="roi"%%',
            "Thesee",
            "Thesee",
            "%%fin_cast%%",
            "%%fin_castlist%%",
        ]
    )
    report = validate_castlist_text(text, _config())

    assert report.has_errors is False
    assert "W_CAST_ALIASES_EMPTY" in {diagnostic.code for diagnostic in report.diagnostics}
