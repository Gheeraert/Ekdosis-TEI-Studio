from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from lxml import html as lxml_html

from ets.core import run_pipeline_from_text
from ets.domain import EditionConfig, Witness
from ets.site_builder.builder import build_static_site
from ets.site_builder.models import SiteConfig
from ets.tei.generator import materialize_act_scene_line_xml_ids


ROOT = Path(__file__).resolve().parents[1]
TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI_NS, "xml": XML_NS}


def _tei(tag: str) -> str:
    return f"{{{TEI_NS}}}{tag}"


def _xml_id(element: ET.Element) -> str | None:
    return element.get(f"{{{XML_NS}}}id")


def _mini_config() -> EditionConfig:
    return EditionConfig(
        title="Britannicus",
        author="Jean Racine",
        editor="Editeur",
        witnesses=[
            Witness(siglum="A", year="1670", description="temoin A"),
            Witness(siglum="B", year="1671", description="temoin B"),
        ],
        reference_witness=0,
    )


def _generated_tei_text() -> str:
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "#AGRIPPINE#",
            "#AGRIPPINE#",
            "",
            "Premier vers",
            "Premier vers",
            "",
            "Second vers",
            "Second vers",
        ]
    )
    return run_pipeline_from_text(text, _mini_config())


def test_materialize_act_scene_line_xml_ids_adds_missing_ids_without_touching_other_units() -> None:
    root = ET.fromstring(
        f"""<TEI xmlns="{TEI_NS}">
  <text>
    <body>
      <div type="act" n="1">
        <div type="scene" n="1">
          <sp>
            <speaker>AGRIPPINE</speaker>
            <l n="1">Premier vers</l>
          </sp>
        </div>
      </div>
    </body>
  </text>
</TEI>"""
    )

    materialize_act_scene_line_xml_ids(root)

    act = root.find(".//tei:div[@type='act']", NS)
    scene = root.find(".//tei:div[@type='scene']", NS)
    line = root.find(".//tei:l", NS)
    speaker = root.find(".//tei:speaker", NS)
    speech = root.find(".//tei:sp", NS)

    assert act is not None
    assert scene is not None
    assert line is not None
    assert speaker is not None
    assert speech is not None
    assert _xml_id(act) == "A1"
    assert _xml_id(scene) == "A1S1"
    assert _xml_id(line) == "A1S1L1"
    assert _xml_id(speaker) is None
    assert _xml_id(speech) is None


def test_materialize_act_scene_line_xml_ids_preserves_existing_ids_and_avoids_duplicates() -> None:
    root = ET.fromstring(
        f"""<TEI xmlns="{TEI_NS}">
  <text>
    <body>
      <div type="act" n="1" xml:id="acte-premier">
        <div type="scene" n="1" xml:id="scene-premiere">
          <sp>
            <l n="1" xml:id="vers-princeps">Premier vers</l>
            <l n="2">Second vers</l>
          </sp>
        </div>
      </div>
      <div type="metadata" xml:id="A1S1L2"/>
    </body>
  </text>
</TEI>"""
    )

    materialize_act_scene_line_xml_ids(root)

    act = root.find(".//tei:div[@type='act']", NS)
    scene = root.find(".//tei:div[@type='scene']", NS)
    lines = root.findall(".//tei:l", NS)
    xml_ids = [value for element in root.iter() for value in [_xml_id(element)] if value]

    assert act is not None
    assert scene is not None
    assert _xml_id(act) == "acte-premier"
    assert _xml_id(scene) == "scene-premiere"
    assert _xml_id(lines[0]) == "vers-princeps"
    assert _xml_id(lines[1]) == "A1S1L2-2"
    assert len(xml_ids) == len(set(xml_ids))


def test_generated_tei_materializes_act_scene_line_ids_and_shared_line_ids() -> None:
    root = ET.fromstring(_generated_tei_text())

    act = root.find(".//tei:div[@type='act']", NS)
    scene = root.find(".//tei:div[@type='scene']", NS)
    first_line = root.find(".//tei:l[@n='1']", NS)

    assert act is not None
    assert scene is not None
    assert first_line is not None
    assert _xml_id(act) == "britannicus-A1"
    assert _xml_id(scene) == "britannicus-A1S1"
    assert _xml_id(first_line) == "britannicus-A1S1L1"

    stable_root = ET.fromstring(
        (ROOT / "fixtures" / "stable" / "expected.xml").read_text(encoding="utf-8")
    )
    materialize_act_scene_line_xml_ids(stable_root)
    shared_ids = [_xml_id(line) for line in stable_root.findall(".//tei:l", NS)]

    assert "A1S1L37.1" in shared_ids
    assert "A1S1L37.2" in shared_ids
    assert len(shared_ids) == len(set(shared_ids))


def test_character_id_does_not_collide_with_play_id_and_who_uses_prefixed_id(tmp_path: Path) -> None:
    castlist_path = tmp_path / "britannicus_castlist.txt"
    castlist_path.write_text(
        "\n".join(
            [
                "%%castlist%%",
                '%%cast id=britannicus role="Britannicus" aliases="BRITANNICUS"%%',
                "Britannicus",
                "Britannicus",
                "%%fin_cast%%",
                "%%fin_castlist%%",
            ]
        ),
        encoding="utf-8",
    )
    config = EditionConfig(
        title="Britannicus",
        author="Jean Racine",
        editor="Editeur",
        witnesses=[
            Witness(siglum="A", year="1670", description="temoin A"),
            Witness(siglum="B", year="1671", description="temoin B"),
        ],
        reference_witness=0,
        castlist_path=castlist_path.name,
    )
    text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "#BRITANNICUS#",
            "#BRITANNICUS#",
            "",
            "Premier vers",
            "Premier vers",
        ]
    )
    root = ET.fromstring(run_pipeline_from_text(text, config, castlist_base_dir=tmp_path))

    text_element = root.find(".//tei:text", NS)
    cast_item = root.find(".//tei:castItem", NS)
    speech = root.find(".//tei:sp", NS)
    xml_ids = [value for element in root.iter() for value in [_xml_id(element)] if value]

    assert text_element is not None and _xml_id(text_element) == "britannicus"
    assert cast_item is not None and _xml_id(cast_item) == "char-britannicus"
    assert "britannicus-A1" in xml_ids
    assert "britannicus-A1S1" in xml_ids
    assert "britannicus-A1S1L1" in xml_ids
    assert len(xml_ids) == len(set(xml_ids))
    assert speech is not None and speech.get("who") == "#char-britannicus"


def test_generated_tei_ids_stay_aligned_with_dts_search_and_html(tmp_path: Path) -> None:
    dramatic_dir = tmp_path / "dramatic"
    output_dir = tmp_path / "site"
    source = dramatic_dir / "britannicus.xml"
    dramatic_dir.mkdir(parents=True)
    source.write_text(_generated_tei_text(), encoding="utf-8")

    result = build_static_site(
        SiteConfig(
            site_title="ETS ids",
            dramatic_xml_dir=dramatic_dir,
            output_dir=output_dir,
            publish_notices=False,
            enable_dts=True,
            enable_search_index=True,
        )
    )

    assert result.play_count == 1
    search_entries = json.loads((output_dir / "search" / "index.json").read_text(encoding="utf-8"))
    first_entry = search_entries[0]
    slug = first_entry["slug"]
    dts_navigation = json.loads(
        (output_dir / "api" / "dts" / "navigation" / slug / "index.json").read_text(encoding="utf-8")
    )
    play_html = lxml_html.document_fromstring(
        (output_dir / "plays" / f"{slug}.html").read_text(encoding="utf-8")
    )

    assert first_entry["ref"] == "britannicus-A1S1L1"
    assert any(node["identifier"] == "britannicus-A1S1L1" for node in dts_navigation["member"])
    assert play_html.xpath("//*[@id='britannicus-A1S1L1']")
