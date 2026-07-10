from __future__ import annotations

from xml.etree import ElementTree as ET

from ets.collation import collate_parallel_verse
from ets.domain import (
    ApparatusTokenSegment,
    CollatedAct,
    CollatedPlay,
    CollatedReading,
    CollatedScene,
    CollatedSpeech,
    CollatedStageDirection,
    CollatedText,
    EditionConfig,
    LiteralTokenSegment,
    TokenCollatedLine,
    Witness,
)
from ets.html import render_html_preview_from_tei
from ets.latex import tei_to_ekdosis
from ets.tei.generator import generate_tei_xml
from ets.tei.terminal_punctuation import (
    normalize_terminal_punctuation_segments,
    split_terminal_punctuation,
)

TEI_NS = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI_NS}

NBSP = " "


def _line(reading_a: str, reading_b: str) -> TokenCollatedLine:
    line = collate_parallel_verse(
        [reading_a, reading_b],
        ["A", "B"],
        ref_index=0,
        number="1",
        whole_line_variant=False,
        act_label="1",
        scene_label="1",
        speaker_label="IOCASTE",
        block_index=1,
    )
    assert isinstance(line, TokenCollatedLine)
    return line


def _line_multi(readings: list[str]) -> TokenCollatedLine:
    line = collate_parallel_verse(
        readings,
        ["A", "B", "C", "D", "E"],
        ref_index=0,
        number="1",
        whole_line_variant=False,
        act_label="1",
        scene_label="1",
        speaker_label="IOCASTE",
        block_index=1,
    )
    assert isinstance(line, TokenCollatedLine)
    return line


def _whole_line(readings: list[str], witness_sigla: list[str] | None = None) -> TokenCollatedLine:
    witnesses = witness_sigla or ["A", "B"]
    line = collate_parallel_verse(
        readings,
        witnesses,
        ref_index=0,
        number="1",
        whole_line_variant=True,
        act_label="1",
        scene_label="1",
        speaker_label="IOCASTE",
        block_index=1,
    )
    assert isinstance(line, TokenCollatedLine)
    return line


def _xml_for_line(line: TokenCollatedLine, witness_sigla: list[str] | None = None) -> str:
    witnesses = witness_sigla or ["A", "B"]
    play = CollatedPlay(
        acts=[
            CollatedAct(
                head=CollatedText(segments=[]),
                scenes=[
                    CollatedScene(
                        head=CollatedText(segments=[]),
                        speeches=[CollatedSpeech(speaker=CollatedText(segments=[]), elements=[line])],
                    )
                ],
            )
        ]
    )
    config = EditionConfig(
        title="Test",
        author="Auteur",
        editor="",
        witnesses=[Witness(siglum, "", "") for siglum in witnesses],
        reference_witness=0,
    )
    return generate_tei_xml(play, config)


def _xml_for_stage_text(stage_text: CollatedText) -> str:
    play = CollatedPlay(
        acts=[
            CollatedAct(
                head=CollatedText(segments=[]),
                scenes=[
                    CollatedScene(
                        head=CollatedText(segments=[]),
                        speeches=[
                            CollatedSpeech(
                                speaker=CollatedText(segments=[]),
                                elements=[CollatedStageDirection(stage_text)],
                            )
                        ],
                    )
                ],
            )
        ]
    )
    config = EditionConfig(
        title="Test",
        author="Auteur",
        editor="",
        witnesses=[Witness("A", "", ""), Witness("B", "", "")],
        reference_witness=0,
    )
    return generate_tei_xml(play, config)


def _l_element(xml: str) -> ET.Element:
    element = ET.fromstring(xml).find(".//tei:l", NS)
    assert element is not None
    return element


def _text_of(element: ET.Element) -> str:
    return "".join(element.itertext())


def _content_text(value: str | None) -> str:
    if value is None:
        return ""
    return "" if value.strip() == "" else value


def _wit_tokens(value: str | None) -> list[str]:
    return [token.lstrip("#") for token in (value or "").split()]


def _reading_for_witness(app: ET.Element, witness: str) -> ET.Element:
    lemma = app.find("tei:lem", NS)
    assert lemma is not None
    if witness in _wit_tokens(lemma.get("wit")):
        return lemma
    for rdg in app.findall("tei:rdg", NS):
        if witness in _wit_tokens(rdg.get("wit")):
            return rdg
    return lemma


def _reconstruct_line_for_witness(line: ET.Element, witness: str) -> str:
    parts = [_content_text(line.text)]
    for child in list(line):
        if child.tag == f"{{{TEI_NS}}}app":
            reading = _reading_for_witness(child, witness)
            parts.append(_text_of(reading))
        else:
            parts.append(_text_of(child))
        parts.append(_content_text(child.tail))
    return "".join(parts)


def _assert_reconstructs_witnesses(line: ET.Element, expected: dict[str, str]) -> None:
    for witness, text in expected.items():
        assert _reconstruct_line_for_witness(line, witness) == text


def _first_app(xml: str) -> ET.Element:
    app = ET.fromstring(xml).find(".//tei:app", NS)
    assert app is not None
    return app


# ---------------------------------------------------------------------------
# Marqueur ETS (lacune)
# ---------------------------------------------------------------------------


def test_lacune_marker_in_rdg_becomes_empty_omission() -> None:
    xml = _xml_for_line(_whole_line(["Texte present.", "(lacune)"]))
    app = _first_app(xml)
    lemma = app.find("tei:lem", NS)
    rdg = app.find("tei:rdg", NS)

    assert lemma is not None
    assert rdg is not None
    assert lemma.get("wit") == "#A"
    assert _text_of(lemma) == "Texte present."
    assert rdg.get("wit") == "#B"
    assert rdg.get("type") == "omission"
    assert _text_of(rdg) == ""
    assert "(lacune)" not in xml
    _assert_reconstructs_witnesses(
        _l_element(xml),
        {"A": "Texte present.", "B": ""},
    )


def test_lacune_marker_in_lemma_becomes_empty_omission() -> None:
    xml = _xml_for_line(_whole_line(["(lacune)", "Texte present."]))
    app = _first_app(xml)
    lemma = app.find("tei:lem", NS)
    rdg = app.find("tei:rdg", NS)

    assert lemma is not None
    assert rdg is not None
    assert lemma.get("wit") == "#A"
    assert lemma.get("type") == "omission"
    assert _text_of(lemma) == ""
    assert rdg.get("wit") == "#B"
    assert _text_of(rdg) == "Texte present."
    assert "(lacune)" not in xml
    _assert_reconstructs_witnesses(
        _l_element(xml),
        {"A": "", "B": "Texte present."},
    )


def test_lacune_marker_groups_multiple_lacunary_witnesses() -> None:
    xml = _xml_for_line(
        _whole_line(
            ["(lacune)", "(lacune)", "Texte present.", "Texte present.", "(lacune)"],
            ["A", "B", "C", "D", "E"],
        ),
        ["A", "B", "C", "D", "E"],
    )
    app = _first_app(xml)
    lemma = app.find("tei:lem", NS)
    rdg = app.find("tei:rdg", NS)

    assert lemma is not None
    assert rdg is not None
    assert _wit_tokens(lemma.get("wit")) == ["A", "B", "E"]
    assert lemma.get("type") == "omission"
    assert _text_of(lemma) == ""
    assert _wit_tokens(rdg.get("wit")) == ["C", "D"]
    assert _text_of(rdg) == "Texte present."
    assert "(lacune)" not in xml
    _assert_reconstructs_witnesses(
        _l_element(xml),
        {
            "A": "",
            "B": "",
            "C": "Texte present.",
            "D": "Texte present.",
            "E": "",
        },
    )


def test_lacune_marker_with_surrounding_spaces_becomes_empty_omission() -> None:
    xml = _xml_for_line(_whole_line(["Texte present.", "   (lacune)   "]))
    rdg = _first_app(xml).find("tei:rdg", NS)

    assert rdg is not None
    assert rdg.get("type") == "omission"
    assert _text_of(rdg) == ""
    assert "(lacune)" not in xml
    _assert_reconstructs_witnesses(
        _l_element(xml),
        {"A": "Texte present.", "B": ""},
    )


def test_lacune_marker_inside_text_stays_textual() -> None:
    xml = _xml_for_line(
        _whole_line(
            [
                "Passage marque (lacune) dans la source",
                "Autre passage",
            ]
        )
    )
    app = _first_app(xml)
    lemma = app.find("tei:lem", NS)

    assert lemma is not None
    assert lemma.get("type") is None
    assert _text_of(lemma) == "Passage marque (lacune) dans la source"
    assert "(lacune)" in xml
    _assert_reconstructs_witnesses(
        _l_element(xml),
        {
            "A": "Passage marque (lacune) dans la source",
            "B": "Autre passage",
        },
    )


def test_lacune_marker_in_stage_app_uses_common_reading_serialization() -> None:
    xml = _xml_for_stage_text(
        CollatedText(
            segments=[
                ApparatusTokenSegment(
                    lemma=CollatedReading("(lacune)", ["A"]),
                    readings=[CollatedReading("Il sort.", ["B"])],
                )
            ]
        )
    )
    app = _first_app(xml)
    stage = ET.fromstring(xml).find(".//tei:stage", NS)
    lemma = app.find("tei:lem", NS)
    rdg = app.find("tei:rdg", NS)

    assert stage is not None
    assert lemma is not None
    assert rdg is not None
    assert lemma.get("type") == "omission"
    assert _text_of(lemma) == ""
    assert _text_of(rdg) == "Il sort."
    assert "(lacune)" not in xml


def test_lacune_omission_is_consumed_by_existing_html_and_ekdosis_renderers() -> None:
    xml = _xml_for_line(_whole_line(["Texte present.", "(lacune)"]))

    html = render_html_preview_from_tei(xml)
    tex = tei_to_ekdosis(xml)

    assert "(lacune)" not in html
    assert 'data-omission="true"' in html
    assert "(lacune)" not in tex
    assert "om." not in tex


# ---------------------------------------------------------------------------
# Helper : split_terminal_punctuation
# ---------------------------------------------------------------------------


def test_split_terminal_punctuation_simple_cases() -> None:
    assert split_terminal_punctuation("Quoy,") == ("Quoy", ",", "")
    assert split_terminal_punctuation("Quoy, ") == ("Quoy", ",", " ")
    assert split_terminal_punctuation("vostre.") == ("vostre", ".", "")
    assert split_terminal_punctuation("cause") == ("cause", "", "")
    assert split_terminal_punctuation("cause ") == ("cause", "", " ")


def test_split_terminal_punctuation_nbsp_double_punctuation() -> None:
    assert split_terminal_punctuation(f"douleurs{NBSP}!") == ("douleurs", f"{NBSP}!", "")
    assert split_terminal_punctuation(f"distance{NBSP}? ") == ("distance", f"{NBSP}?", " ")


def test_split_terminal_punctuation_normalizes_tilde_marker_to_nbsp() -> None:
    # Robustesse uniquement : le marqueur ETS "~" est normalement déjà
    # converti en amont ; il ne doit jamais être réémis tel quel.
    assert split_terminal_punctuation("douleur~!") == ("douleur", f"{NBSP}!", "")
    assert split_terminal_punctuation("mot~?") == ("mot", f"{NBSP}?", "")


def test_split_terminal_punctuation_refuses_composites_and_italic_boundaries() -> None:
    assert split_terminal_punctuation("Helas...") == ("Helas...", "", "")
    assert split_terminal_punctuation("quoi?!") == ("quoi?!", "", "")
    # Le "_" fermant après la ponctuation la garde dans l'italique.
    assert split_terminal_punctuation("_temple,_") == ("_temple,_", "", "")
    assert split_terminal_punctuation("temple,_ ") == ("temple,_", "", " ")
    # Ponctuation hors italique : extraction possible.
    assert split_terminal_punctuation("_temple_,") == ("_temple_", ",", "")
    assert split_terminal_punctuation("temple_, ") == ("temple_", ",", " ")


def test_normalize_segments_preserves_metadata_and_witnesses() -> None:
    segment = ApparatusTokenSegment(
        lemma=CollatedReading(text="Quoy, ", witness_sigla=["A", "C"]),
        readings=[CollatedReading(text="Quoi, ", witness_sigla=["B"])],
        candidate_class="minor_graphic_safe",
        visibility_policy="hide_safe",
        rule_code="punctuation_removed_for_graphic_key+y_i",
    )

    result = normalize_terminal_punctuation_segments([segment])

    assert len(result) == 2
    app, literal = result
    assert isinstance(app, ApparatusTokenSegment)
    assert app.lemma.text == "Quoy"
    assert app.lemma.witness_sigla == ["A", "C"]
    assert app.readings[0].text == "Quoi"
    assert app.readings[0].witness_sigla == ["B"]
    assert app.candidate_class == "minor_graphic_safe"
    assert app.visibility_policy == "hide_safe"
    assert app.rule_code == "punctuation_removed_for_graphic_key+y_i"
    assert isinstance(literal, LiteralTokenSegment)
    assert literal.text == ", "


# ---------------------------------------------------------------------------
# Cas 1 : ponctuation terminale commune
# ---------------------------------------------------------------------------


def test_common_terminal_comma_moved_outside_graphic_app() -> None:
    xml = _xml_for_line(_line("Il repond Quoy,", "Il repond Quoi,"))
    l_element = _l_element(xml)
    app = l_element.find("tei:app", NS)

    assert app is not None
    assert app.get("subtype") == "graphic"
    lem = app.find("tei:lem", NS)
    rdg = app.find("tei:rdg", NS)
    assert _text_of(lem) == "Quoy"
    assert _text_of(rdg) == "Quoi"
    assert app.tail == ","


def test_common_terminal_comma_with_space_preserves_spacing() -> None:
    xml = _xml_for_line(_line("Quoy, il faut partir", "Quoi, il faut partir"))
    l_element = _l_element(xml)
    app = l_element.find("tei:app", NS)

    assert app is not None
    assert _text_of(app.find("tei:lem", NS)) == "Quoy"
    assert app.tail == ", il faut partir"


def test_common_nbsp_exclamation_moved_outside_graphic_app() -> None:
    xml = _xml_for_line(
        _line(f"Ah mortelles douleurs{NBSP}!", f"Ah mortelles douleur{NBSP}!")
    )
    l_element = _l_element(xml)
    app = l_element.find("tei:app", NS)

    assert app is not None
    assert _text_of(app.find("tei:lem", NS)) == "douleurs"
    assert _text_of(app.find("tei:rdg", NS)) == "douleur"
    assert app.tail == f"{NBSP}!"
    assert "~" not in xml


def test_common_nbsp_question_moved_outside_graphic_app() -> None:
    xml = _xml_for_line(
        _line(f"Et quelle distance{NBSP}?", f"Et quelle distances{NBSP}?")
    )
    l_element = _l_element(xml)
    app = l_element.find("tei:app", NS)

    assert app is not None
    assert _text_of(app.find("tei:lem", NS)) == "distance"
    assert app.tail == f"{NBSP}?"
    assert "~" not in xml


# ---------------------------------------------------------------------------
# Cas 2 : variante uniquement ponctuelle
# ---------------------------------------------------------------------------


def test_punctuation_only_comma_creates_punctuation_app() -> None:
    xml = _xml_for_line(_line("Voila la cause,", "Voila la cause"))
    l_element = _l_element(xml)
    app = l_element.find("tei:app", NS)

    assert app is not None
    assert app.get("type") == "minor"
    assert app.get("subtype") == "punctuation"
    assert app.get("ana") == "#punctuation_only"
    assert l_element.text == "Voila la cause"
    lem = app.find("tei:lem", NS)
    rdg = app.find("tei:rdg", NS)
    assert _text_of(lem) == ","
    assert _text_of(rdg) == ""
    assert rdg.get("type") == "omission"


def test_punctuation_only_comma_before_following_word_preserves_spacing() -> None:
    xml = _xml_for_line(_line("Voila la cause, enfin", "Voila la cause enfin"))
    l_element = _l_element(xml)
    app = l_element.find("tei:app", NS)

    assert app is not None
    assert l_element.text == "Voila la cause"
    assert _text_of(app.find("tei:lem", NS)) == ","
    assert app.find("tei:rdg", NS).get("type") == "omission"
    assert app.tail == " enfin"


def test_punctuation_only_nbsp_exclamation_creates_punctuation_app() -> None:
    xml = _xml_for_line(_line(f"Ah quelle douleur{NBSP}!", "Ah quelle douleur"))
    l_element = _l_element(xml)
    app = l_element.find("tei:app", NS)

    assert app is not None
    assert app.get("subtype") == "punctuation"
    assert l_element.text == "Ah quelle douleur"
    assert _text_of(app.find("tei:lem", NS)) == f"{NBSP}!"
    assert app.find("tei:rdg", NS).get("type") == "omission"
    assert "~" not in xml


def test_multiwitness_punctuation_addition_isolates_comma_and_reconstructs_all_witnesses() -> None:
    word = "m\u2019importe"
    readings = [word, word, f"{word},", f"{word},", word]
    xml = _xml_for_line(_line_multi(readings), ["A", "B", "C", "D", "E"])
    l_element = _l_element(xml)
    app = l_element.find("tei:app", NS)

    assert app is not None
    assert l_element.text == word
    assert app.get("type") == "minor"
    assert app.get("subtype") == "punctuation"
    assert app.get("ana") == "#punctuation_only"
    assert "+" not in app.get("ana", "")

    lem = app.find("tei:lem", NS)
    rdg = app.find("tei:rdg", NS)
    assert lem is not None and rdg is not None
    assert _wit_tokens(lem.get("wit")) == ["A", "B", "E"]
    assert _wit_tokens(rdg.get("wit")) == ["C", "D"]
    assert _text_of(lem) == ""
    assert lem.get("type") == "omission"
    assert _text_of(rdg) == ","
    assert rdg.get("type") is None
    assert not any(ch.isalpha() for ch in _text_of(lem))
    assert not any(ch.isalpha() for ch in _text_of(rdg))
    _assert_reconstructs_witnesses(
        l_element,
        {
            "A": word,
            "B": word,
            "C": f"{word},",
            "D": f"{word},",
            "E": word,
        },
    )


def test_multiwitness_punctuation_substitution_isolates_signs_and_reconstructs_all_witnesses() -> None:
    readings = ["mot,", "mot,", "mot.", "mot.", "mot,"]
    xml = _xml_for_line(_line_multi(readings), ["A", "B", "C", "D", "E"])
    l_element = _l_element(xml)
    app = l_element.find("tei:app", NS)

    assert app is not None
    assert l_element.text == "mot"
    assert app.get("type") == "minor"
    assert app.get("subtype") == "punctuation"
    assert app.get("ana") == "#punctuation_only"
    assert "+" not in app.get("ana", "")

    lem = app.find("tei:lem", NS)
    rdg = app.find("tei:rdg", NS)
    assert lem is not None and rdg is not None
    assert _wit_tokens(lem.get("wit")) == ["A", "B", "E"]
    assert _wit_tokens(rdg.get("wit")) == ["C", "D"]
    assert _text_of(lem) == ","
    assert _text_of(rdg) == "."
    assert lem.get("type") is None
    assert rdg.get("type") is None
    assert not any(ch.isalpha() for ch in _text_of(lem))
    assert not any(ch.isalpha() for ch in _text_of(rdg))
    _assert_reconstructs_witnesses(
        l_element,
        {
            "A": "mot,",
            "B": "mot,",
            "C": "mot.",
            "D": "mot.",
            "E": "mot,",
        },
    )


def test_mixed_case_and_punctuation_variant_is_not_isolated_as_punctuation_only() -> None:
    xml = _xml_for_line(_line("Paix,", "paix"))
    l_element = _l_element(xml)
    app = l_element.find("tei:app", NS)

    assert app is not None
    assert app.get("type") == "minor"
    assert app.get("subtype") == "mixed"
    assert app.get("ana") == "#case_only #punctuation_only"
    assert "+" not in app.get("ana", "")
    assert (l_element.text or "").strip() == ""
    assert _text_of(app.find("tei:lem", NS)) == "Paix,"
    assert _text_of(app.find("tei:rdg", NS)) == "paix"


def test_multiwitness_mixed_case_and_punctuation_is_not_isolated_and_reconstructs_all_witnesses() -> None:
    readings = ["Paix,", "paix", "paix", "paix", "Paix,"]
    xml = _xml_for_line(_line_multi(readings), ["A", "B", "C", "D", "E"])
    l_element = _l_element(xml)
    app = l_element.find("tei:app", NS)

    assert app is not None
    assert app.get("type") == "minor"
    assert app.get("subtype") == "mixed"
    assert app.get("ana") == "#case_only #punctuation_only"
    assert "+" not in app.get("ana", "")
    assert (l_element.text or "").strip() == ""

    lem = app.find("tei:lem", NS)
    rdg = app.find("tei:rdg", NS)
    assert lem is not None and rdg is not None
    assert _wit_tokens(lem.get("wit")) == ["A", "E"]
    assert _wit_tokens(rdg.get("wit")) == ["B", "C", "D"]
    assert _text_of(lem) == "Paix,"
    assert _text_of(rdg) == "paix"
    assert any(ch.isalpha() for ch in _text_of(lem))
    assert any(ch.isalpha() for ch in _text_of(rdg))
    _assert_reconstructs_witnesses(
        l_element,
        {
            "A": "Paix,",
            "B": "paix",
            "C": "paix",
            "D": "paix",
            "E": "Paix,",
        },
    )


# ---------------------------------------------------------------------------
# Italiques
# ---------------------------------------------------------------------------


def test_italic_multitoken_punctuation_after_closing_marker_is_extracted() -> None:
    xml = _xml_for_line(
        _line(
            "Oui _je viens en son temple_, adorer l'Eternel",
            "Oui _je viens en son Temple_, adorer l'Eternel",
        )
    )
    l_element = _l_element(xml)
    hi = l_element.find("tei:hi", NS)

    assert hi is not None
    assert "," not in _text_of(hi)
    assert hi.tail is not None and hi.tail.startswith(",")
    app = hi.find("tei:app", NS)
    assert app is not None
    assert _text_of(app.find("tei:lem", NS)).strip() == "temple"
    assert _text_of(app.find("tei:rdg", NS)).strip() == "Temple"


def test_italic_multitoken_punctuation_before_closing_marker_is_not_extracted() -> None:
    xml = _xml_for_line(
        _line(
            "Oui _je viens en son temple,_ adorer l'Eternel",
            "Oui _je viens en son Temple,_ adorer l'Eternel",
        )
    )
    l_element = _l_element(xml)
    hi = l_element.find("tei:hi", NS)

    assert hi is not None
    app = hi.find("tei:app", NS)
    assert app is not None
    # La virgule appartient à l'italique : elle reste dans les leçons.
    assert "," in _text_of(app.find("tei:lem", NS))
    assert "," in _text_of(app.find("tei:rdg", NS))


def test_balanced_single_token_italic_external_punctuation_is_extracted() -> None:
    xml = _xml_for_line(_line("Va au _temple_, seigneur", "Va au _Temple_, seigneur"))
    l_element = _l_element(xml)
    hi = l_element.find("tei:hi", NS)

    assert hi is not None
    assert "," not in _text_of(hi)
    assert hi.tail is not None and hi.tail.startswith(", ")
    assert "seigneur" in hi.tail


def test_balanced_single_token_italic_internal_punctuation_is_not_extracted() -> None:
    xml = _xml_for_line(_line("Va au _temple,_ seigneur", "Va au _Temple,_ seigneur"))
    l_element = _l_element(xml)
    app = l_element.find(".//tei:app", NS)

    assert app is not None
    assert "," in _text_of(app.find("tei:lem", NS))
    assert "," in _text_of(app.find("tei:rdg", NS))


# ---------------------------------------------------------------------------
# Cas ambigus : comportement inchangé
# ---------------------------------------------------------------------------


def test_punctuation_differs_and_core_differs_keeps_existing_behavior() -> None:
    xml = _xml_for_line(_line("Il repond Quoy,", "Il repond Quoi."))
    l_element = _l_element(xml)
    app = l_element.find("tei:app", NS)

    assert app is not None
    assert _text_of(app.find("tei:lem", NS)) == "Quoy,"
    assert _text_of(app.find("tei:rdg", NS)) == "Quoi."
    assert not (app.tail or "").strip()


# ---------------------------------------------------------------------------
# Régression LaTeX / Ekdosis
# ---------------------------------------------------------------------------


def test_ekdosis_hide_minor_keeps_extracted_common_punctuation() -> None:
    xml = _xml_for_line(_line("Il repond Quoy, dit-il", "Il repond Quoi, dit-il"))

    full = tei_to_ekdosis(xml)
    readable = tei_to_ekdosis(xml, apparatus_policy="hide_minor")

    assert "\\app{" in full
    assert "\\app{" not in readable
    assert "Quoy, dit-il" in readable


def test_ekdosis_hide_minor_keeps_punctuation_only_lemma() -> None:
    xml = _xml_for_line(_line("Voila la cause, enfin", "Voila la cause enfin"))

    full = tei_to_ekdosis(xml)
    readable = tei_to_ekdosis(xml, apparatus_policy="hide_minor")

    assert "\\app{" in full
    assert "\\rdg[wit={B}]{}" in full
    assert "\\app{" not in readable
    assert "cause, enfin" in readable
