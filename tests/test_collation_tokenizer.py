from __future__ import annotations

from ets.collation import tokenize_editorial_text


def test_tokenize_editorial_text_splits_on_regular_spaces_only() -> None:
    text = "OUY, puis\u00A0que je retrouve un Amy"
    assert tokenize_editorial_text(text) == ["OUY,", "puis\u00A0que", "je", "retrouve", "un", "Amy"]


def test_tokenize_editorial_text_ignores_outer_padding() -> None:
    assert tokenize_editorial_text("  A  B   C ") == ["A", "B", "C"]
