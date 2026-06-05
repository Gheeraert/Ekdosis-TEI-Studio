from __future__ import annotations

from pathlib import Path

from ets.latex import tei_castlist_to_latex


def _tei(front: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <front>
      {front}
    </front>
    <body/>
  </text>
</TEI>
"""


def test_castlist_simple_items() -> None:
    actual = tei_castlist_to_latex(
        _tei(
            """
            <castList>
              <castItem><role>Oreste</role></castItem>
              <castItem><role>Hermione</role></castItem>
            </castList>
            """
        )
    )

    assert actual == "\\begin{description}\n\\item[Oreste]\n\\item[Hermione]\n\\end{description}\n"


def test_cast_item_with_role_and_role_desc() -> None:
    actual = tei_castlist_to_latex(_tei("<castList><castItem><role>Pyrrhus</role><roleDesc>roi d'Epire</roleDesc></castItem></castList>"))

    assert "\\item[Pyrrhus] roi d'Epire" in actual


def test_cast_item_with_role_and_actor() -> None:
    actual = tei_castlist_to_latex(_tei("<castList><castItem><role>Andromaque</role><actor>Mlle Du Parc</actor></castItem></castList>"))

    assert "\\item[Andromaque] Mlle Du Parc" in actual


def test_cast_item_with_role_desc_and_actor() -> None:
    actual = tei_castlist_to_latex(
        _tei(
            """
            <castList>
              <castItem>
                <role>Pylade</role>
                <roleDesc>ami d'Oreste</roleDesc>
                <actor>La Thorilliere</actor>
              </castItem>
            </castList>
            """
        )
    )

    assert "\\item[Pylade] ami d'Oreste -- La Thorilliere" in actual


def test_cast_group_with_head_and_item() -> None:
    actual = tei_castlist_to_latex(
        _tei(
            """
            <castList>
              <castGroup>
                <head>Grecs</head>
                <castItem><role>Oreste</role></castItem>
              </castGroup>
            </castList>
            """
        )
    )

    assert "\\item[] \\textbf{Grecs}" in actual
    assert "\\item[Oreste]" in actual


def test_castlist_head_is_rendered_as_subsection() -> None:
    actual = tei_castlist_to_latex(_tei("<castList><head>Acteurs</head><castItem><role>Aricie</role></castItem></castList>"))

    assert actual.startswith("\\subsection*{Acteurs}\n\n\\begin{description}")


def test_castlist_preserves_mixed_role_desc_content() -> None:
    actual = tei_castlist_to_latex(
        _tei("<castList><castItem><role>Thesee</role><roleDesc>roi <persName>d'Athenes</persName> exile</roleDesc></castItem></castList>")
    )

    assert "\\item[Thesee] roi d'Athenes exile" in actual


def test_castlist_inline_italic_and_bold() -> None:
    actual = tei_castlist_to_latex(
        _tei(
            """
            <castList>
              <castItem>
                <role><hi rend="bold">Neron</hi></role>
                <roleDesc>empereur <hi rend="italic">romain</hi></roleDesc>
              </castItem>
            </castList>
            """
        )
    )

    assert r"\item[\textbf{Neron}] empereur \emph{romain}" in actual


def test_castlist_inline_footnote() -> None:
    actual = tei_castlist_to_latex(_tei('<castList><castItem><role>Junie</role><roleDesc>princesse<note place="foot">Note.</note></roleDesc></castItem></castList>'))

    assert r"\item[Junie] princesse\footnote{Note.}" in actual


def test_castlist_escapes_latex_reserved_characters() -> None:
    actual = tei_castlist_to_latex(_tei("<castList><castItem><role>A &amp; B</role><roleDesc>% $ # _ { }</roleDesc></castItem></castList>"))

    assert r"\item[A \& B] \% \$ \# \_ \{ \}" in actual


def test_castlist_accepts_path_input(tmp_path: Path) -> None:
    source = tmp_path / "dramatis.xml"
    source.write_text(_tei("<castList><castItem><role>Path Role</role></castItem></castList>"), encoding="utf-8")

    assert "\\item[Path Role]" in tei_castlist_to_latex(source)


def test_castlist_without_castlist_returns_stable_comment() -> None:
    actual = tei_castlist_to_latex(_tei("<div><p>Aucun dramatis.</p></div>"))

    assert actual == "% DRAMATIS PERSONAE: no castList found.\n"
