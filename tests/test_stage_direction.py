from __future__ import annotations

import xml.etree.ElementTree as ET

from ets.collation import collate_play
from ets.domain import EditionConfig, Witness
from ets.parser import parse_play
from ets.tei import generate_tei_xml

NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def test_explicit_stage_direction_is_rendered_in_speech_flow() -> None:
    config = EditionConfig(
        title="Test",
        author="Auteur",
        editor="Editeur",
        witnesses=[
            Witness(siglum="A", year="1667", description="A"),
            Witness(siglum="B", year="1671", description="B"),
        ],
        reference_witness=0,
    )
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
            "Je parle ici.",
            "Je parle ici.",
            "",
            "**Il sort.**",
            "**Il sort.**",
            "",
            "Je reviens.",
            "Je reviens.",
        ]
    )

    play = parse_play(text, config)
    collated = collate_play(play, witness_sigla=["A", "B"], reference_witness=0)
    xml_text = generate_tei_xml(collated, config)
    root = ET.fromstring(xml_text)

    sp = root.find(".//tei:sp", NS)
    assert sp is not None
    stage = sp.find("tei:stage", NS)
    assert stage is not None
    assert stage.text == "Il sort."
