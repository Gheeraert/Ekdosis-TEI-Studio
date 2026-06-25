from __future__ import annotations

import json
from pathlib import Path

from lxml import etree

from ets.dts.static_export import export_dts_static
from ets.site_builder.builder import build_static_site
from ets.site_builder.models import PlayEntry, SiteConfig


def _write_tei(path: Path, *, title: str = "Britannicus") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>{title}</title>
        <author>Jean Racine</author>
      </titleStmt>
      <publicationStmt><p>Test</p></publicationStmt>
      <sourceDesc><p>Test</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <div type="act" n="1" xml:id="acte-premier">
        <div type="scene" n="1" xml:id="scene-premiere">
          <sp>
            <speaker>AGRIPPINE</speaker>
            <l n="1" xml:id="A1S1L1">Quoi&#160;? Tandis que Néron s'abandonne au sommeil</l>
            <l n="2">Faut-il que vous veniez attendre son réveil&#160;?</l>
          </sp>
        </div>
      </div>
    </body>
  </text>
</TEI>
""",
        encoding="utf-8",
    )


def _play(source: Path, *, slug: str = "britannicus") -> PlayEntry:
    return PlayEntry(
        source_path=source,
        slug=slug,
        title="Britannicus",
        author="Jean Racine",
        document_type="dramatic_tei",
        has_text_body=True,
    )


def _write_tei_without_xml_ids(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Britannicus sans identifiants</title>
        <author>Jean Racine</author>
      </titleStmt>
      <publicationStmt><p>Test</p></publicationStmt>
      <sourceDesc><p>Test</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <div type="act" n="1">
        <div type="scene" n="1">
          <sp>
            <speaker>AGRIPPINE</speaker>
            <l n="1">Premier vers sans xml:id</l>
          </sp>
        </div>
      </div>
    </body>
  </text>
</TEI>
""",
        encoding="utf-8",
    )


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_xml(path: Path) -> etree._ElementTree:
    return etree.parse(str(path))


def test_static_export_creates_entry_collection_resource_navigation_and_document(tmp_path: Path) -> None:
    source = tmp_path / "sources" / "piece.xml"
    output = tmp_path / "site"
    _write_tei(source)

    warnings = export_dts_static(output, (_play(source),), collection_title="Théâtre complet")

    assert warnings == ()
    entry_path = output / "api" / "dts" / "index.json"
    collection_path = output / "api" / "dts" / "collection" / "index.json"
    resource_path = output / "api" / "dts" / "collection" / "britannicus.json"
    navigation_path = output / "api" / "dts" / "navigation" / "britannicus" / "index.json"
    document_path = output / "api" / "dts" / "document" / "britannicus" / "full.xml"
    fragment_root = output / "api" / "dts" / "document" / "britannicus"
    act_fragment_path = fragment_root / "acte-premier.xml"
    scene_fragment_path = fragment_root / "scene-premiere.xml"
    first_line_fragment_path = fragment_root / "A1S1L1.xml"
    second_line_fragment_path = fragment_root / "A1S1L2.xml"

    assert entry_path.exists()
    assert collection_path.exists()
    assert resource_path.exists()
    assert navigation_path.exists()
    assert (output / "api" / "dts" / "navigation" / "britannicus" / "acte-premier.json").exists()
    assert (output / "api" / "dts" / "navigation" / "britannicus" / "scene-premiere.json").exists()
    assert (output / "api" / "dts" / "navigation" / "britannicus" / "A1S1L1.json").exists()
    assert (output / "api" / "dts" / "navigation" / "britannicus" / "A1S1L2.json").exists()
    assert act_fragment_path.exists()
    assert scene_fragment_path.exists()
    assert first_line_fragment_path.exists()
    assert second_line_fragment_path.exists()
    assert document_path.read_bytes() == source.read_bytes()

    act_fragment = _parse_xml(act_fragment_path)
    scene_fragment = _parse_xml(scene_fragment_path)
    first_line_fragment = _parse_xml(first_line_fragment_path)
    second_line_fragment = _parse_xml(second_line_fragment_path)
    assert act_fragment.xpath("//*[local-name()='fragment']/*[local-name()='div'][@type='act']")
    assert scene_fragment.xpath("//*[local-name()='fragment']/*[local-name()='div'][@type='scene']")
    assert first_line_fragment.xpath("//*[local-name()='fragment']/*[local-name()='sp']/*[local-name()='speaker']")
    assert first_line_fragment.xpath(
        "//*[local-name()='fragment']/*[local-name()='sp']/*[local-name()='l'][@n='1']"
    )
    assert not first_line_fragment.xpath("//*[local-name()='fragment']//*[local-name()='l'][@n='2']")
    assert second_line_fragment.xpath("//*[local-name()='fragment']//*[local-name()='l'][@n='2']")
    assert not second_line_fragment.xpath("//*[local-name()='fragment']//*[local-name()='l'][@n='1']")

    entry = _load(entry_path)
    collection = _load(collection_path)
    resource = _load(resource_path)
    navigation = _load(navigation_path)

    assert entry["collection"] == "collection/index.json"
    assert collection["title"] == "Théâtre complet"
    assert collection["member"][0]["@id"] == "britannicus"  # type: ignore[index]
    assert resource["@type"] == "Resource"
    assert resource["navigation"] == "../navigation/britannicus/index.json"
    assert resource["document"] == "../document/britannicus/full.xml"
    assert [node["citeType"] for node in navigation["member"]] == ["act", "scene", "line", "line"]  # type: ignore[index]
    assert [node["identifier"] for node in navigation["member"]][:3] == [  # type: ignore[index]
        "acte-premier",
        "scene-premiere",
        "A1S1L1",
    ]
    assert [node["document"] for node in navigation["member"]] == [  # type: ignore[index]
        "../../document/britannicus/acte-premier.xml",
        "../../document/britannicus/scene-premiere.xml",
        "../../document/britannicus/A1S1L1.xml",
        "../../document/britannicus/A1S1L2.xml",
    ]
    line_navigation = _load(
        output / "api" / "dts" / "navigation" / "britannicus" / "A1S1L1.json"
    )
    assert line_navigation["member"][0]["document"] == "../../document/britannicus/A1S1L1.xml"  # type: ignore[index]
    assert line_navigation["ref"]["document"] == "../../document/britannicus/A1S1L1.xml"  # type: ignore[index]


def test_static_export_builds_logical_identifiers_when_xml_ids_are_missing(tmp_path: Path) -> None:
    source = tmp_path / "sources" / "without-xml-ids.xml"
    output = tmp_path / "site"
    slug = "britannicus-sans-identifiants"
    _write_tei_without_xml_ids(source)

    warnings = export_dts_static(
        output,
        (_play(source, slug=slug),),
        collection_title="Théâtre complet",
    )

    navigation_root = output / "api" / "dts" / "navigation" / slug
    document_root = output / "api" / "dts" / "document" / slug
    assert warnings == ()
    assert (navigation_root / "A1.json").exists()
    assert (navigation_root / "A1S1.json").exists()
    assert (navigation_root / "A1S1L1.json").exists()
    assert (document_root / "A1.xml").exists()
    assert (document_root / "A1S1.xml").exists()
    assert (document_root / "A1S1L1.xml").exists()

    navigation = _load(navigation_root / "index.json")
    assert [node["identifier"] for node in navigation["member"]] == ["A1", "A1S1", "A1S1L1"]  # type: ignore[index]
    assert [node["citeType"] for node in navigation["member"]] == ["act", "scene", "line"]  # type: ignore[index]
    assert [node["document"] for node in navigation["member"]] == [  # type: ignore[index]
        f"../../document/{slug}/A1.xml",
        f"../../document/{slug}/A1S1.xml",
        f"../../document/{slug}/A1S1L1.xml",
    ]
    assert _parse_xml(document_root / "A1.xml")
    assert _parse_xml(document_root / "A1S1.xml")
    assert _parse_xml(document_root / "A1S1L1.xml")


def test_static_export_uses_manifest_slug_and_writes_deterministic_unicode_json(tmp_path: Path) -> None:
    first_source = tmp_path / "sources" / "z-source.xml"
    second_source = tmp_path / "sources" / "a-source.xml"
    _write_tei(first_source, title="Néron")
    _write_tei(second_source, title="Bérénice")
    output = tmp_path / "site"
    plays = (
        _play(first_source, slug="z-manifest-slug"),
        _play(second_source, slug="a-manifest-slug"),
    )

    export_dts_static(output, plays, collection_title="Théâtre complet")
    first_render = (output / "api" / "dts" / "collection" / "index.json").read_text(encoding="utf-8")
    export_dts_static(output, tuple(reversed(plays)), collection_title="Théâtre complet")
    second_render = (output / "api" / "dts" / "collection" / "index.json").read_text(encoding="utf-8")

    assert first_render == second_render
    assert "Théâtre complet" in first_render
    assert "\\u00e9" not in first_render
    collection = json.loads(first_render)
    assert [member["@id"] for member in collection["member"]] == ["a-manifest-slug", "z-manifest-slug"]
    assert not (output / "api" / "dts" / "collection" / "z-source.json").exists()


def test_builder_keeps_site_generation_when_one_dts_resource_fails(tmp_path: Path, monkeypatch) -> None:
    dramatic_dir = tmp_path / "dramatic"
    output_dir = tmp_path / "site"
    good_source = dramatic_dir / "good.xml"
    bad_source = dramatic_dir / "bad.xml"
    _write_tei(good_source, title="Bonne pièce")
    _write_tei(bad_source, title="Pièce fautive")

    from ets.dts import static_export

    original_index_tei = static_export.index_tei

    def fail_one(source_path: Path, **kwargs):
        if source_path.name == "bad.xml":
            raise ValueError("isolated test failure")
        return original_index_tei(source_path, **kwargs)

    monkeypatch.setattr(static_export, "index_tei", fail_one)
    result = build_static_site(
        SiteConfig(
            site_title="ETS DTS",
            dramatic_xml_dir=dramatic_dir,
            output_dir=output_dir,
            publish_notices=False,
        )
    )

    assert (output_dir / "index.html").exists()
    assert (output_dir / "plays" / "good.html").exists()
    assert (output_dir / "plays" / "bad.html").exists()
    assert (output_dir / "api" / "dts" / "collection" / "good.json").exists()
    assert not (output_dir / "api" / "dts" / "collection" / "bad.json").exists()
    assert "DTS export skipped for bad: isolated test failure" in result.warnings


def test_static_export_rejects_unsafe_slug_without_writing_outside_output(tmp_path: Path) -> None:
    source = tmp_path / "piece.xml"
    output = tmp_path / "site"
    _write_tei(source)

    warnings = export_dts_static(
        output,
        (_play(source, slug="../escape"),),
        collection_title="ETS DTS",
    )

    assert warnings == ("DTS export skipped for ../escape: slug is not a safe static path segment",)
    assert not (tmp_path / "escape.json").exists()
    assert _load(output / "api" / "dts" / "collection" / "index.json")["member"] == []


def test_fragment_reference_uses_the_same_url_encoding_as_navigation(tmp_path: Path) -> None:
    source = tmp_path / "piece.xml"
    output = tmp_path / "site"
    _write_tei(source)
    source.write_text(
        source.read_text(encoding="utf-8").replace(
            'xml:id="scene-premiere"',
            'xml:id="scène-première"',
        ),
        encoding="utf-8",
    )

    warnings = export_dts_static(
        output,
        (_play(source),),
        collection_title="ETS DTS",
    )

    encoded_ref = "sc%C3%A8ne-premi%C3%A8re"
    assert warnings == ()
    assert (
        output / "api" / "dts" / "navigation" / "britannicus" / f"{encoded_ref}.json"
    ).exists()
    assert (
        output / "api" / "dts" / "document" / "britannicus" / f"{encoded_ref}.xml"
    ).exists()
    navigation = _load(output / "api" / "dts" / "navigation" / "britannicus" / "index.json")
    scene = next(node for node in navigation["member"] if node["identifier"] == "scène-première")  # type: ignore[union-attr]
    assert scene["document"] == f"../../document/britannicus/{encoded_ref}.xml"


def test_fragment_failure_warns_without_stopping_other_exports(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "piece.xml"
    output = tmp_path / "site"
    _write_tei(source)

    from ets.dts import document_fragments

    original_fragment_xml = document_fragments._fragment_xml

    def fail_one_fragment(tree, node, source_element):
        if node.identifier == "A1S1L2":
            raise ValueError("isolated fragment failure")
        return original_fragment_xml(tree, node, source_element)

    monkeypatch.setattr(document_fragments, "_fragment_xml", fail_one_fragment)
    warnings = export_dts_static(
        output,
        (_play(source),),
        collection_title="ETS DTS",
    )

    assert warnings == (
        "DTS fragment export skipped for britannicus/A1S1L2: isolated fragment failure",
    )
    document_root = output / "api" / "dts" / "document" / "britannicus"
    assert (document_root / "full.xml").exists()
    assert (document_root / "A1S1L1.xml").exists()
    assert not (document_root / "A1S1L2.xml").exists()
    assert (output / "api" / "dts" / "navigation" / "britannicus" / "index.json").exists()
