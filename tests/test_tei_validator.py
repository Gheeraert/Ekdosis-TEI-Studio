from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from lxml import etree

from ets.core import run_pipeline_from_text
from ets.parser import load_config
from ets.validation import default_tei_schema_path, validate_tei_xml

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"


def _generate_stable_tei() -> str:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "stable"
    config = load_config(fixture_dir / "config.json")
    input_text = (fixture_dir / "input.txt").read_text(encoding="utf-8")
    return run_pipeline_from_text(input_text, config)


RUNTIME_DIR = Path(__file__).resolve().parents[1] / "tests" / "_runtime"
RUNTIME_DIR.mkdir(exist_ok=True)


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
    assert any('body must contain only div type="act".' in issue.message for issue in result.errors)


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
