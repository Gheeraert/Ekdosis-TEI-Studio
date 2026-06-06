from __future__ import annotations

from pathlib import Path

from ets.latex import tei_peritext_to_latex


def _tei(body: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      {body}
    </body>
  </text>
</TEI>
"""


def test_peritext_paragraph_simple() -> None:
    actual = tei_peritext_to_latex(_tei("<p>Un paragraphe simple.</p>"))

    assert actual == "Un paragraphe simple.\n"


def test_peritext_accepts_path_input(tmp_path: Path) -> None:
    source = tmp_path / "notice.xml"
    source.write_text(_tei("<p>Depuis un fichier.</p>"), encoding="utf-8")

    assert tei_peritext_to_latex(source) == "Depuis un fichier.\n"


def test_peritext_head_and_nested_section() -> None:
    actual = tei_peritext_to_latex(
        _tei(
            """
            <div type="notice">
              <head type="main">Titre porte par le master</head>
              <div>
                <head>Contexte</head>
                <p>Texte.</p>
                <div>
                  <head>Detail</head>
                  <p>Suite.</p>
                </div>
              </div>
            </div>
            """
        )
    )

    assert "Titre porte par le master" not in actual
    assert "\\section*{Contexte}" in actual
    assert "\\subsection*{Detail}" in actual


def test_peritext_inline_styles() -> None:
    actual = tei_peritext_to_latex(
        _tei(
            """
            <p>Un <hi rend="italic">mot</hi>, un <hi rend="bold">gras</hi>,
            <hi rend="underline">souligne</hi>, <hi rend="sup">1</hi>,
            <hi rend="sub">2</hi>, et <hi rend="smallcaps">Racine</hi>.</p>
            """
        )
    )

    assert r"\emph{mot}" in actual
    assert r"\textbf{gras}" in actual
    assert r"\underline{souligne}" in actual
    assert r"\textsuperscript{1}" in actual
    assert r"\textsubscript{2}" in actual
    assert r"\textsc{Racine}" in actual


def test_peritext_inline_footnote() -> None:
    actual = tei_peritext_to_latex(_tei('<p>Texte<note place="foot">Note critique.</note>.</p>'))

    assert actual == r"Texte\footnote{Note critique.}." + "\n"


def test_peritext_noindent_paragraph() -> None:
    actual = tei_peritext_to_latex(_tei('<p rend="noindent">Sans retrait.</p>'))

    assert actual == r"\noindent Sans retrait." + "\n"


def test_peritext_quote() -> None:
    actual = tei_peritext_to_latex(_tei("<quote><p>Une citation.</p></quote>"))

    assert actual == "\\begin{quote}\nUne citation.\n\\end{quote}\n"


def test_peritext_unordered_list() -> None:
    actual = tei_peritext_to_latex(_tei('<list type="unordered"><item>Alpha</item><item>Beta</item></list>'))

    assert actual == "\\begin{itemize}\n\\item Alpha\n\\item Beta\n\\end{itemize}\n"


def test_peritext_ordered_list() -> None:
    actual = tei_peritext_to_latex(_tei('<list type="ordered"><item>Un</item><item>Deux</item></list>'))

    assert actual == "\\begin{enumerate}\n\\item Un\n\\item Deux\n\\end{enumerate}\n"


def test_peritext_bibliography() -> None:
    actual = tei_peritext_to_latex(_tei("<listBibl><bibl>Reference A.</bibl><bibl>Reference B.</bibl></listBibl>"))

    assert actual == "\\begin{itemize}\n\\item Reference A.\n\\item Reference B.\n\\end{itemize}\n"


def test_peritext_preserves_mixed_xml_content() -> None:
    actual = tei_peritext_to_latex(_tei('<p>Avant <hi rend="italic">dedans</hi> apres.</p>'))

    assert actual == r"Avant \emph{dedans} apres." + "\n"


def test_peritext_escapes_latex_reserved_characters() -> None:
    actual = tei_peritext_to_latex(_tei("<p>A &amp; B % $ # _ { }.</p>"))

    assert actual == r"A \& B \% \$ \# \_ \{ \}." + "\n"


def test_peritext_ref_target_keeps_text_and_adds_url_footnote() -> None:
    actual = tei_peritext_to_latex(_tei('<p>Voir <ref target="https://example.test?a=1&amp;b=2">le site</ref>.</p>'))

    assert actual == r"Voir le site\footnote{URL: https://example.test?a=1\&b=2}." + "\n"


def test_peritext_simple_table() -> None:
    actual = tei_peritext_to_latex(
        _tei(
            """
            <table>
              <row><cell>A</cell><cell>B</cell></row>
              <row><cell>1</cell><cell>2</cell></row>
            </table>
            """
        )
    )

    assert actual == (
        "\\noindent\n"
        "\\begingroup\n"
        "\\small\n"
        "\\setlength{\\tabcolsep}{3pt}\n"
        "\\begin{tabularx}{\\linewidth}{@{}*{2}{Y}@{}}\n"
        "A & B \\\\\n"
        "1 & 2 \\\\\n"
        "\\end{tabularx}\n"
        "\\endgroup\n"
    )


def test_peritext_table_uses_tabularx_columns_and_preserves_cell_content() -> None:
    actual = tei_peritext_to_latex(
        _tei(
            """
            <table>
              <row>
                <cell>Colonne longue A avec un texte qui doit pouvoir revenir a la ligne.</cell>
                <cell>Texte avec <hi rend="italic">italique</hi>.</cell>
                <cell>A &amp; B % $ # _ { }</cell>
              </row>
              <row>
                <cell>Deuxieme ligne.</cell>
                <cell>Cellule manquante ensuite.</cell>
              </row>
            </table>
            """
        )
    )

    assert "\\noindent" in actual
    assert "\\begingroup" in actual
    assert "\\small" in actual
    assert "\\setlength{\\tabcolsep}{3pt}" in actual
    assert "\\begin{tabularx}{\\linewidth}{@{}*{3}{Y}@{}}" in actual
    assert "\\begin{tabular}{" not in actual
    assert "Colonne longue A avec un texte qui doit pouvoir revenir a la ligne." in actual
    assert r"Texte avec \emph{italique}." in actual
    assert r"A \& B \% \$ \# \_ \{ \}" in actual
    assert "Cellule manquante ensuite. &  \\\\" in actual
