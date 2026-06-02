from __future__ import annotations

import xml.etree.ElementTree as ET

from ets.core import run_pipeline_from_text
from ets.domain import EditionConfig, Witness

NS = {"tei": "http://www.tei-c.org/ns/1.0"}


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


def _stanza_input() -> str:
    return "\n".join(
        [
            *["####ACTE I####"] * 4,
            "",
            *["###SCENE I###"] * 4,
            "",
            *["#CHOEUR#"] * 4,
            "",
            *["%%strophe subtype=distique rhyme=aa%%"] * 4,
            "",
            "=12=Que vous semble, mes soeurs, de l’état où nous sommes~?",
            "=12=Que vous semble, mes soeurs, de l’estat où nous sommes~?",
            "=12=Que vous semble, mes soeurs, de l’estat où nous sommes~?",
            "=12=Que vous semble, mes soeurs, de l’état où nous sommes~?",
            "",
            *["=10=D’Esther, d’Aman qui tombe dans les pommes~?"] * 4,
            "",
            *["%%fin_strophe%%"] * 4,
        ]
    )


def test_complete_chain_generates_stanza_lg_and_metered_lines() -> None:
    tei_xml = run_pipeline_from_text(_stanza_input(), _config())
    root = ET.fromstring(tei_xml)

    lg = root.find(".//tei:lg[@type='stanza']", NS)
    assert lg is not None
    assert lg.get("subtype") == "distique"
    assert lg.get("rhyme") == "aa"

    lines = lg.findall("tei:l", NS)
    assert [line.get("met") for line in lines] == ["12", "10"]
    assert all(line.get("n") for line in lines)
    assert all(line.get("{http://www.w3.org/XML/1998/namespace}id") for line in lines)


def test_complete_chain_preserves_etat_estat_variant_in_stanza() -> None:
    tei_xml = run_pipeline_from_text(_stanza_input(), _config())
    root = ET.fromstring(tei_xml)

    app = root.find(".//tei:lg[@type='stanza']/tei:l[@met='12']/tei:app", NS)
    assert app is not None
    lem = app.find("tei:lem", NS)
    rdg = app.find("tei:rdg", NS)
    assert lem is not None
    assert rdg is not None
    assert lem.get("wit") == "#A #D"
    assert rdg.get("wit") == "#B #C"
    assert "état" in "".join(lem.itertext())
    assert "estat" in "".join(rdg.itertext())
