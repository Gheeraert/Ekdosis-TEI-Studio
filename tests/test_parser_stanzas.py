from __future__ import annotations

from ets.domain import EditionConfig, Stanza, Witness
from ets.parser import parse_play


def _config() -> EditionConfig:
    return EditionConfig(
        title="Esther",
        author="Jean Racine",
        editor="Editeur",
        witnesses=[
            Witness(siglum="A", year="1689", description="A"),
            Witness(siglum="B", year="1689", description="B"),
            Witness(siglum="C", year="1689", description="C"),
            Witness(siglum="D", year="1689", description="D"),
        ],
        reference_witness=0,
    )


def test_parse_play_produces_heterometric_stanza() -> None:
    text = "\n".join(
        [
            *["####ACTE I####"] * 4,
            "",
            *["###SCENE I###"] * 4,
            "",
            *["#CHOEUR#"] * 4,
            "",
            *["%%strophe subtype=distique rhyme=aa%%"] * 4,
            "",
            "=12=Que vous semble, mes soeurs, de l'etat ou nous sommes~?",
            "=12=Que vous semble, mes soeurs, de l'estat ou nous sommes~?",
            "=12=Que vous semble, mes soeurs, de l'estat ou nous sommes~?",
            "=12=Que vous semble, mes soeurs, de l'etat ou nous sommes~?",
            "",
            *["=10=D'Esther, d'Aman qui tombe dans les pommes~?"] * 4,
            "",
            *["%%fin_strophe%%"] * 4,
        ]
    )

    play = parse_play(text, _config())
    stanza = play.acts[0].scenes[0].speeches[0].elements[0]

    assert isinstance(stanza, Stanza)
    assert stanza.subtype == "distique"
    assert stanza.rhyme == "aa"
    assert len(stanza.lines) == 2
    assert [line.met for line in stanza.lines] == ["12", "10"]


def test_parse_play_preserves_whole_line_variant_in_metered_stanza() -> None:
    text = "\n".join(
        [
            *["####ACTE I####"] * 4,
            "",
            *["###SCENE I###"] * 4,
            "",
            *["#CHOEUR#"] * 4,
            "",
            *["%%strophe%%"] * 4,
            "",
            "#####=12=Un vers entierement variant",
            "#####=12=Un vers tout a fait variant",
            "#####=12=Un vers tout a fait variant",
            "#####=12=Un vers entierement variant",
            "",
            *["%%fin_strophe%%"] * 4,
        ]
    )

    play = parse_play(text, _config())
    stanza = play.acts[0].scenes[0].speeches[0].elements[0]

    assert isinstance(stanza, Stanza)
    assert stanza.lines[0].met == "12"
    assert stanza.lines[0].whole_line_variant is True
    assert stanza.lines[0].readings[0] == "Un vers entierement variant"
