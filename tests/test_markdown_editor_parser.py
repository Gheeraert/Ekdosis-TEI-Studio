from __future__ import annotations

from ets.markdown_editor.models import (
    BibliographyBlock,
    BoldRun,
    CapsRun,
    FootnoteRefRun,
    HeadingBlock,
    ItalicRun,
    ListBlock,
    ParagraphBlock,
    QuoteBlock,
    RuleBlock,
    SmallCapsRun,
    SubRun,
    SupRun,
    UnderlineRun,
)
from ets.markdown_editor.parser import parse_markdown


def test_parser_simple_text_builds_paragraph_block() -> None:
    result = parse_markdown("Texte simple.")
    assert not result.has_errors
    assert len(result.document.blocks) == 1
    assert isinstance(result.document.blocks[0], ParagraphBlock)


def test_parser_supports_headings_styles_lists_quote_and_rule() -> None:
    source = (
        "# Titre principal\n\n"
        "Un *italique*, un **gras**, [u]souligne[/u], [sup]2[/sup], [sub]2[/sub], "
        "[caps]senatus[/caps] et [sc]romanus[/sc].\n\n"
        "> Citation\n\n"
        "- item 1\n"
        "- item 2\n\n"
        "---\n"
    )
    result = parse_markdown(source)
    blocks = result.document.blocks
    assert isinstance(blocks[0], HeadingBlock)
    assert isinstance(blocks[1], ParagraphBlock)
    assert isinstance(blocks[2], QuoteBlock)
    assert isinstance(blocks[3], ListBlock)
    assert blocks[3].ordered is False
    assert isinstance(blocks[4], RuleBlock)

    paragraph_runs = blocks[1].runs
    assert any(isinstance(run, ItalicRun) for run in paragraph_runs)
    assert any(isinstance(run, BoldRun) for run in paragraph_runs)
    assert any(isinstance(run, UnderlineRun) for run in paragraph_runs)
    assert any(isinstance(run, SupRun) for run in paragraph_runs)
    assert any(isinstance(run, SubRun) for run in paragraph_runs)
    assert any(isinstance(run, CapsRun) for run in paragraph_runs)
    assert any(isinstance(run, SmallCapsRun) for run in paragraph_runs)


def test_parser_supports_footnotes_and_bibliography_block() -> None:
    source = (
        "Voici une note[^1].\n\n"
        ":::bibl\n"
        "- Référence A\n"
        "- Référence B\n"
        ":::\n\n"
        "[^1]: Contenu de la note.\n"
    )
    result = parse_markdown(source)
    assert not result.has_errors
    assert "1" in result.document.footnotes
    assert result.document.footnote_reference_order == ("1",)
    assert any(isinstance(block, BibliographyBlock) for block in result.document.blocks)

    first_paragraph = result.document.blocks[0]
    assert isinstance(first_paragraph, ParagraphBlock)
    assert any(isinstance(run, FootnoteRefRun) for run in first_paragraph.runs)


def test_parser_reports_missing_note_definition_and_orphan_definition() -> None:
    source = "Appel manquant[^9].\n\n[^1]: Note orpheline."
    result = parse_markdown(source)
    codes = {diag.code for diag in result.diagnostics}
    assert "E_MD_FOOTNOTE_UNDEFINED" in codes
    assert "W_MD_FOOTNOTE_ORPHAN" in codes


def test_parser_reports_unclosed_bibliography_block() -> None:
    source = ":::bibl\n- Référence sans fermeture\n"
    result = parse_markdown(source)
    codes = {diag.code for diag in result.diagnostics}
    assert "E_MD_BIBL_UNCLOSED" in codes


def test_parser_reports_invalid_link_and_unclosed_custom_tag() -> None:
    source = "Lien [cassé](nota url) et [u]tag ouverte."
    result = parse_markdown(source)
    codes = {diag.code for diag in result.diagnostics}
    assert "E_MD_LINK_INVALID" in codes
    assert "E_MD_CUSTOM_TAG_UNCLOSED" in codes
