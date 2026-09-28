from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from lxml import etree

from ets.core import run_pipeline, run_pipeline_from_text
from ets.domain import Character, EditionConfig, Witness
from ets.parser import load_config
from ets.validation import default_tei_schema_path, validate_tei_xml

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"

RUNTIME_DIR = Path(__file__).resolve().parents[1] / "tests" / "_runtime"
RUNTIME_DIR.mkdir(exist_ok=True)


def _generate_stable_tei() -> str:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "stable"
    config = load_config(fixture_dir / "config.json")
    input_text = (fixture_dir / "input.txt").read_text(encoding="utf-8")
    return run_pipeline_from_text(input_text, config)


def _generate_with_dramatis_personae() -> str:
    """Real generation with a castlist file, producing <front>/dramatis-personae
    and a stage type="setting" — exactly what build_castlist_tei_element() emits."""
    project_dir = RUNTIME_DIR / f"castlist_{uuid4().hex}"
    project_dir.mkdir(parents=True, exist_ok=True)

    input_text = "\n".join(
        [
            "####ACTE I####",
            "####ACTE I####",
            "",
            "###SCENE I###",
            "###SCENE I###",
            "",
            "#THESEE#",
            "#THESEE#",
            "",
            "Je parle.",
            "Je parle.",
        ]
    )
    config_payload = {
        "Prénom de l'auteur": "Jean",
        "Nom de l'auteur": "Racine",
        "Titre de la pièce": "Phedre",
        "Prénom de l'éditeur scientifique": "Test",
        "Nom de l'éditeur scientifique": "Editor",
        "Temoins": [
            {"abbr": "A", "year": "1677", "desc": "A"},
            {"abbr": "B", "year": "1687", "desc": "B"},
        ],
        "reference_witness": 0,
        "castlist_path": "castlist.txt",
    }
    castlist_text = "\n".join(
        [
            "%%castlist%%",
            "%%head%%",
            "Acteurs",
            "Acteurs",
            "%%fin_head%%",
            '%%cast id=thesee role="Thésée" desc="roi d’Athènes" aliases="THESEE|THESEE."%%',
            "Thésée, roi d’Athènes",
            "Thésée, Roi d’Athènes",
            "%%fin_cast%%",
            "%%setting%%",
            "La scène est à Trézène.",
            "La Scene est à Trézène.",
            "%%fin_setting%%",
            "%%fin_castlist%%",
        ]
    )

    input_path = project_dir / "input.txt"
    config_path = project_dir / "config.json"
    input_path.write_text(input_text, encoding="utf-8")
    config_path.write_text(json.dumps(config_payload, ensure_ascii=False), encoding="utf-8")
    (project_dir / "castlist.txt").write_text(castlist_text, encoding="utf-8")

    return run_pipeline(input_path=input_path, config_path=config_path)


def _generate_with_prologue() -> str:
    """Real generation of a play with a PROLOGUE division before act one."""
    config = EditionConfig(
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
    )
    return run_pipeline_from_text(text, config)


def test_validate_tei_xml_accepts_generated_stable_tei() -> None:
    tei_xml = _generate_stable_tei()

    result = validate_tei_xml(tei_xml)
    assert result.is_valid is True
    assert result.schema_name == "ets-racine.rnc"
    assert result.engine_name == "lxml-relaxng"
    assert result.errors == []


def test_validate_tei_xml_rejects_invalid_root() -> None:
    xml_text = "<root/>"
    result = validate_tei_xml(xml_text)
    assert result.is_valid is False
    assert result.errors
    assert any("root" in issue.message for issue in result.errors)


def test_validate_tei_xml_handles_malformed_xml_without_crash() -> None:
    xml_text = "<TEI xmlns='http://www.tei-c.org/ns/1.0'><text></TEI>"
    result = validate_tei_xml(xml_text)
    assert result.is_valid is False
    assert result.errors
    assert result.errors[0].message.startswith("Malformed XML:")


def test_default_schema_path_exists() -> None:
    schema_path = default_tei_schema_path()
    assert schema_path.exists()
    assert schema_path.name == "ets-racine.rnc"


def test_validate_tei_xml_reports_missing_schema_cleanly() -> None:
    missing = RUNTIME_DIR / f"missing_{uuid4().hex}.rng"
    result = validate_tei_xml("<TEI xmlns='http://www.tei-c.org/ns/1.0'/>", schema_path=missing)
    assert result.is_valid is False
    assert result.errors
    assert "Schema not found" in result.errors[0].message


def test_validate_tei_xml_reports_invalid_schema_cleanly() -> None:
    invalid_schema = RUNTIME_DIR / f"invalid_schema_{uuid4().hex}.rng"
    invalid_schema.write_text("<not_rng/>", encoding="utf-8")
    result = validate_tei_xml("<TEI xmlns='http://www.tei-c.org/ns/1.0'/>", schema_path=invalid_schema)
    assert result.is_valid is False
    assert result.errors
    assert "Unable to load schema" in result.errors[0].message


def test_validate_tei_xml_rejects_sourcedesc_mixing_p_and_listwit() -> None:
    xml_text = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Test</title>
      </titleStmt>
      <publicationStmt>
        <p>Test</p>
      </publicationStmt>
      <sourceDesc>
        <p>Description</p>
        <listWit>
          <witness xml:id="A">A</witness>
        </listWit>
      </sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <p>Test</p>
    </body>
  </text>
</TEI>"""
    result = validate_tei_xml(xml_text)
    assert result.is_valid is False
    assert any("sourceDesc must not mix <p> and <listWit> siblings." in issue.message for issue in result.errors)


def test_validate_tei_xml_rejects_generic_prose_body_under_strict_schema() -> None:
    """tei_all.rng accepted a bare <p> in <body>; the ets-racine profile does not."""
    xml_text = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Test</title>
        <author>Test</author>
      </titleStmt>
      <publicationStmt>
        <p>Test</p>
      </publicationStmt>
      <sourceDesc>
        <p>Description</p>
      </sourceDesc>
    </fileDesc>
    <encodingDesc>
      <schemaRef key="ets-racine" type="projectODD" url="ets-racine.odd"/>
    </encodingDesc>
  </teiHeader>
  <text xml:id="test">
    <body>
      <p>Not a dramatic act division.</p>
    </body>
  </text>
</TEI>"""
    result = validate_tei_xml(xml_text)
    assert result.is_valid is False
    assert any('body must contain only div type="act" or div type="prologue".' in issue.message for issue in result.errors)


def test_validate_tei_xml_rejects_ids_not_prefixed_by_play_id() -> None:
    """Schematron-only rule: the RelaxNG grammar accepts any xsd:ID, but
    ets-racine.sch additionally requires structural ids to be prefixed by the
    play's own <text>/@xml:id. This is not expressible in RelaxNG alone, so
    it only surfaces once the Schematron pass runs."""
    tei_xml = _generate_stable_tei()
    doc = etree.fromstring(tei_xml.encode("utf-8"))
    first_act = doc.find(f".//{{{TEI_NS}}}div[@type='act']")
    first_act.set(f"{{{XML_NS}}}id", "not-prefixed-correctly")
    tampered_xml = etree.tostring(doc, encoding="unicode")

    result = validate_tei_xml(tampered_xml)
    assert result.is_valid is False
    assert any(
        'should start with the play id followed by "-"' in issue.message for issue in result.errors
    )


def test_validate_tei_xml_accepts_generated_tei_with_dramatis_personae() -> None:
    """A real <front>/dramatis-personae block (castItem, role, roleDesc, note,
    stage type="setting") must validate: this is genuine ETS output, not a
    generic TEI front matter the profile should reject."""
    tei_xml = _generate_with_dramatis_personae()
    doc = etree.fromstring(tei_xml.encode("utf-8"))

    # Lock in that the fixture actually exercises stage type="setting", the
    # element responsible for the previously-reported Schematron false positive.
    assert doc.find(f".//{{{TEI_NS}}}front//{{{TEI_NS}}}stage[@type='setting']") is not None

    result = validate_tei_xml(tei_xml)
    assert result.is_valid is True
    assert result.errors == []


def test_validate_tei_xml_accepts_generated_tei_with_prologue() -> None:
    tei_xml = _generate_with_prologue()
    doc = etree.fromstring(tei_xml.encode("utf-8"))
    assert doc.find(f".//{{{TEI_NS}}}body/{{{TEI_NS}}}div[@type='prologue']") is not None

    result = validate_tei_xml(tei_xml)
    assert result.is_valid is True
    assert result.errors == []


def test_validate_tei_xml_still_rejects_misprefixed_explicit_stage_in_body() -> None:
    """The front-matter fix for stage type="setting" must not weaken the
    prefix check for a real structural stage inside the dramatic body."""
    tei_xml = _generate_with_prologue()
    doc = etree.fromstring(tei_xml.encode("utf-8"))
    stages = doc.xpath(".//tei:body//tei:stage[@xml:id]", namespaces={"tei": TEI_NS, "xml": XML_NS})
    assert stages
    explicit_stage = stages[0]
    explicit_stage.set(f"{{{XML_NS}}}id", "not-prefixed-correctly")
    tampered_xml = etree.tostring(doc, encoding="unicode")

    result = validate_tei_xml(tampered_xml)
    assert result.is_valid is False
    assert any(
        'should start with the play id followed by "-"' in issue.message for issue in result.errors
    )
