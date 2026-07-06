from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from ets.core import run_pipeline_from_text
from ets.domain import Character, EditionConfig, Witness
from ets.dts.tei_index import index_tei
from ets.tei.generator import resolve_play_id, slugify_play_id

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI_NS, "xml": XML_NS}


def _xml_id(element: ET.Element) -> str | None:
    return element.get(f"{{{XML_NS}}}id")


def _config(title: str, *, play_id: str = "", characters: list[Character] | None = None) -> EditionConfig:
    return EditionConfig(
        title=title,
        author="Jean Racine",
        editor="Editeur",
        witnesses=[
            Witness(siglum="A", year="1672", description="temoin A"),
            Witness(siglum="B", year="1676", description="temoin B"),
        ],
        reference_witness=0,
        characters=characters or [],
        play_id=play_id,
    )


def _two_witness_text(*, with_stage: bool = False, with_implicit: bool = False) -> str:
    lines = [
        "####ACTE I####",
        "####ACTE I####",
        "",
        "###SCENE I###",
        "###SCENE I###",
        "",
        "#AGRIPPINE#",
        "#AGRIPPINE#",
        "",
    ]
    if with_implicit:
        lines += ["$$EVT$$", "$$EVT$$", ""]
    lines += ["Premier vers", "Premier vers", ""]
    if with_implicit:
        lines += ["$$fin$$", "$$fin$$", ""]
    if with_stage:
        lines += ["**Il entre.**", "**Il entre.**", ""]
    lines += ["Second vers", "Second vers"]
    return "\n".join(lines)


def _generate(title: str, **kwargs: object) -> ET.Element:
    config = _config(title, **kwargs)  # type: ignore[arg-type]
    return ET.fromstring(run_pipeline_from_text(_two_witness_text(), config))


def test_text_has_play_xml_id() -> None:
    root = _generate("Bajazet")
    text = root.find(".//tei:text", NS)

    assert text is not None
    assert _xml_id(text) == "bajazet"


def test_act_scene_line_ids_are_prefixed_with_play_id() -> None:
    root = _generate("Bajazet")

    act = root.find(".//tei:div[@type='act']", NS)
    scene = root.find(".//tei:div[@type='scene']", NS)
    first_line = root.find(".//tei:l[@n='1']", NS)

    assert act is not None and _xml_id(act) == "bajazet-A1"
    assert scene is not None and _xml_id(scene) == "bajazet-A1S1"
    assert first_line is not None and _xml_id(first_line) == "bajazet-A1S1L1"


def test_stage_ids_are_prefixed_with_play_id() -> None:
    config = _config("Bajazet")
    xml = run_pipeline_from_text(
        _two_witness_text(with_stage=True, with_implicit=True), config
    )
    root = ET.fromstring(xml)

    explicit = [
        stage
        for stage in root.findall(".//tei:stage", NS)
        if (stage.get("type") or "") not in {"DI", "personnages"}
    ]
    implicit = root.findall(".//tei:stage[@type='DI']", NS)

    assert explicit and _xml_id(explicit[0]) == "bajazet-A1S1ST1"
    assert implicit and _xml_id(implicit[0]) == "bajazet-implicite1"
    assert implicit[0].get("ana") == "#EVT"


def test_witness_ids_are_not_prefixed() -> None:
    root = _generate("Bajazet")
    witnesses = root.findall(".//tei:listWit/tei:witness", NS)

    assert [witness.get("xml:id") or _xml_id(witness) for witness in witnesses] == ["A", "B"]


def test_character_ids_and_who_are_not_prefixed() -> None:
    root = _generate(
        "Bajazet",
        characters=[Character(id="agrippine", label="AGRIPPINE")],
    )
    speech = root.find(".//tei:sp", NS)

    assert speech is not None
    assert speech.get("who") == "#agrippine"


def test_play_id_slugifies_titles() -> None:
    assert slugify_play_id("Bajazet") == "bajazet"
    assert slugify_play_id("La Thébaïde") == "la-thebaide"
    assert slugify_play_id("Les Plaideurs") == "les-plaideurs"
    assert slugify_play_id("Bérénice") == "berenice"
    assert slugify_play_id("Iphigénie") == "iphigenie"
    assert slugify_play_id("Phèdre") == "phedre"


def test_play_id_never_starts_with_digit_and_never_empty() -> None:
    assert slugify_play_id("1668 Les Plaideurs") == "p-1668-les-plaideurs"
    assert slugify_play_id("!!!") == "piece"


def test_explicit_play_id_wins_over_title() -> None:
    config = _config("La Thébaïde ou les frères ennemis", play_id="thebaide")
    assert resolve_play_id(config) == "thebaide"

    root = ET.fromstring(run_pipeline_from_text(_two_witness_text(), config))
    text = root.find(".//tei:text", NS)
    line = root.find(".//tei:l[@n='1']", NS)
    assert text is not None and _xml_id(text) == "thebaide"
    assert line is not None and _xml_id(line) == "thebaide-A1S1L1"


def test_dts_index_navigates_with_prefixed_identifiers(tmp_path: Path) -> None:
    xml = run_pipeline_from_text(_two_witness_text(), _config("Bajazet"))
    source = tmp_path / "bajazet.xml"
    source.write_text(xml, encoding="utf-8")

    index = index_tei(source, slug="bajazet")

    act = index.navigation[0]
    scene = act.children[0]
    line = scene.children[0]
    assert act.identifier == "bajazet-A1"
    assert scene.identifier == "bajazet-A1S1"
    assert line.identifier == "bajazet-A1S1L1"
    assert line.parent == "bajazet-A1S1"
