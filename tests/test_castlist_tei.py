from __future__ import annotations

import xml.etree.ElementTree as ET

from ets.castlist import generate_castlist_tei, parse_castlist_text
from ets.domain import EditionConfig, Witness


NS = {"tei": "http://www.tei-c.org/ns/1.0"}
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"


def _config() -> EditionConfig:
    return EditionConfig(
        title="Phedre",
        author="Jean Racine",
        editor="Editeur",
        witnesses=[
            Witness(siglum="A", year="1677", description="A"),
            Witness(siglum="B", year="1687", description="B"),
        ],
        reference_witness=0,
    )


def _castlist_text(*, head: bool = True, setting: bool = True, desc: bool = True, variant: bool = True) -> str:
    cast_open = '%%cast id=thesee role="ThÃ©sÃ©e"'
    if desc:
        cast_open += ' desc="roi dâ€™AthÃ¨nes"'
    cast_open += ' aliases="THESEE|THESEE."%%'
    second_reading = "ThÃ©sÃ©e, Roi dâ€™AthÃ¨nes" if variant else "ThÃ©sÃ©e, roi dâ€™AthÃ¨nes"
    lines = ["%%castlist%%"]
    if head:
        lines.extend(["%%head%%", "Acteurs", "Acteurs", "%%fin_head%%"])
    lines.extend([cast_open, "ThÃ©sÃ©e, roi dâ€™AthÃ¨nes", second_reading, "%%fin_cast%%"])
    if setting:
        lines.extend(["%%setting%%", "La scÃ¨ne est Ã  TrÃ©zÃ¨ne.", "La Scene est Ã  TrÃ©zÃ¨ne.", "%%fin_setting%%"])
    lines.append("%%fin_castlist%%")
    return "\n".join(lines)


def _root(text: str) -> ET.Element:
    castlist = parse_castlist_text(text, _config())
    return ET.fromstring(generate_castlist_tei(castlist, _config()))


def test_generates_dramatis_personae_div() -> None:
    root = _root(_castlist_text())

    assert root.tag == "{http://www.tei-c.org/ns/1.0}div"
    assert root.attrib["type"] == "dramatis-personae"


def test_generates_head_when_present() -> None:
    root = _root(_castlist_text())

    assert root.findtext("tei:head", namespaces=NS) == "Acteurs"


def test_omits_head_when_absent() -> None:
    root = _root(_castlist_text(head=False))

    assert root.find("tei:head", NS) is None


def test_generates_castlist_and_castitem_xml_id() -> None:
    root = _root(_castlist_text())
    cast_list = root.find("tei:castList", NS)
    cast_item = root.find("tei:castList/tei:castItem", NS)

    assert cast_list is not None
    assert cast_item is not None
    assert cast_item.attrib[XML_ID] == "thesee"


def test_cast_id_is_not_duplicated_on_role() -> None:
    root = _root(_castlist_text())
    role = root.find(".//tei:role", NS)

    assert role is not None
    assert XML_ID not in role.attrib
    assert "xml:id" not in role.attrib


def test_generates_role_text() -> None:
    root = _root(_castlist_text())

    assert root.findtext(".//tei:role", namespaces=NS) == "ThÃ©sÃ©e"


def test_generates_roledesc_when_desc_exists() -> None:
    root = _root(_castlist_text(desc=True))

    assert root.findtext(".//tei:roleDesc", namespaces=NS) == "roi dâ€™AthÃ¨nes"


def test_omits_roledesc_when_desc_absent() -> None:
    root = _root(_castlist_text(desc=False))

    assert root.find(".//tei:roleDesc", NS) is None


def test_preserves_semidiplomatic_readings_in_note() -> None:
    root = _root(_castlist_text())
    note = root.find(".//tei:note[@type='semi-diplomatic']", NS)

    assert note is not None
    note_text = " ".join("".join(note.itertext()).split())
    assert note_text.startswith("ThÃ©sÃ©e,")
    assert "roi" in note_text
    assert note_text.endswith("dâ€™AthÃ¨nes")


def test_differing_readings_generate_apparatus() -> None:
    root = _root(_castlist_text(variant=True))
    app = root.find(".//tei:note[@type='semi-diplomatic']/tei:app", NS)

    assert app is not None
    assert app.findtext("tei:lem", namespaces=NS) == "roi "
    assert app.find("tei:lem", NS).attrib["wit"] == "#A"
    assert app.findtext("tei:rdg", namespaces=NS) == "Roi "
    assert app.find("tei:rdg", NS).attrib["wit"] == "#B"


def test_identical_readings_generate_simple_text() -> None:
    root = _root(_castlist_text(variant=False))
    note = root.find(".//tei:note[@type='semi-diplomatic']", NS)

    assert note is not None
    assert note.find("tei:app", NS) is None
    assert "".join(note.itertext()) == "ThÃ©sÃ©e, roi dâ€™AthÃ¨nes"


def test_generates_setting_stage_when_present() -> None:
    root = _root(_castlist_text(setting=True))
    stage = root.find("tei:stage[@type='setting']", NS)

    assert stage is not None
    assert stage.find("tei:app", NS) is not None


def test_omits_setting_stage_when_absent() -> None:
    root = _root(_castlist_text(setting=False))

    assert root.find("tei:stage[@type='setting']", NS) is None


def test_generated_fragment_is_well_formed_xml() -> None:
    castlist = parse_castlist_text(_castlist_text(), _config())
    xml_text = generate_castlist_tei(castlist, _config())

    parsed = ET.fromstring(xml_text)

    assert parsed.attrib["type"] == "dramatis-personae"
