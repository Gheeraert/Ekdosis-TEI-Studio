from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from ets.core import run_pipeline_from_text
from ets.parser import load_config
from ets.validation import default_tei_schema_path, validate_tei_xml


RUNTIME_DIR = Path(__file__).resolve().parents[1] / "tests" / "_runtime"
RUNTIME_DIR.mkdir(exist_ok=True)


def test_validate_tei_xml_accepts_generated_stable_tei() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture_dir = root / "fixtures" / "stable"
    config = load_config(fixture_dir / "config.json")
    input_text = (fixture_dir / "input.txt").read_text(encoding="utf-8")
    tei_xml = run_pipeline_from_text(input_text, config)

    result = validate_tei_xml(tei_xml)
    assert result.is_valid is True
    assert result.schema_name == "tei_all.rng"
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
    assert schema_path.name == "tei_all.rng"


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
