from __future__ import annotations

import xml.etree.ElementTree as ET

from ets.core import run_pipeline_from_text
from ets.domain import Character, EditionConfig, Witness

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI_NS, "xml": XML_NS}


def _config() -> EditionConfig:
    return EditionConfig(
        title="Esther",
        author="Jean Racine",
        editor="Éditeur",
        witnesses=[
            Witness(siglum="A", year="1689", description="Édition princeps"),
            Witness(siglum="B", year="1697", description="Témoin de référence"),
        ],
        reference_witness=0,
        characters=[Character(id="piete", label="La Piété")],
    )


def _ordinary_act() -> list[str]:
    return [
        "####ACTE I####",
        "####ACTE I####",
        "",
        "###SCENE I###",
        "###SCENE I###",
        "",
        "#ESTHER#",
        "#ESTHER#",
        "",
        "Premier vers de l'acte",
        "Premier vers de l'acte",
    ]


def test_prologue_is_a_special_division_before_act_one() -> None:
    text = "\n".join(
        [
            "####PROLOGUE####",
            "####PROLOGUE####",
            "",
            "La Piété fait le prologue",
            "La Piété fait le prologue",
            "",
            "La Piété, seule",
            "La Piété, seule",
            "",
            "#La Piété#",
            "#La Piété#",
            "",
            "Du séjour bienheureux de la divinité",
            "Du séjour bienheureux de la divinité",
            "",
            "Je descends dans ce lieu par la grâce habité",
            "Je descends dans ce lieu par la grâce habité",
            "",
            *_ordinary_act(),
        ]
    )

    root = ET.fromstring(run_pipeline_from_text(text, _config()))
    prologue = root.find(".//tei:body/tei:div[@type='prologue']", NS)
    assert prologue is not None
    assert prologue.findtext("tei:head", namespaces=NS) == "PROLOGUE"
    assert [stage.text for stage in prologue.findall("tei:stage", NS)] == [
        "La Piété fait le prologue",
        "La Piété, seule",
    ]
    assert prologue.find("tei:div[@type='scene']", NS) is None
    assert prologue.find("tei:sp", NS).get("who") == "#piete"  # type: ignore[union-attr]
    lines = prologue.findall(".//tei:l", NS)
    assert [line.get(f"{{{XML_NS}}}id") for line in lines] == [
        "esther-prologue-L1",
        "esther-prologue-L2",
    ]
    assert all("S" not in line.get(f"{{{XML_NS}}}id", "") for line in lines)

    act = root.find(".//tei:body/tei:div[@type='act']", NS)
    assert act is not None
    assert act.get(f"{{{XML_NS}}}id") == "esther-A1"
    first_act_line = act.find(".//tei:l", NS)
    assert first_act_line is not None
    assert first_act_line.get(f"{{{XML_NS}}}id") == "esther-A1S1L1"


def test_ordinary_play_identifiers_are_unchanged_without_prologue() -> None:
    root = ET.fromstring(run_pipeline_from_text("\n".join(_ordinary_act()), _config()))

    assert root.find(".//tei:div[@xml:id='esther-A1']", NS) is not None
    assert root.find(".//tei:div[@xml:id='esther-A1S1']", NS) is not None
    assert root.find(".//tei:l[@xml:id='esther-A1S1L1']", NS) is not None
