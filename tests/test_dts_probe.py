from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from ets.dts.static_export import export_dts_static
from ets.site_builder.models import PlayEntry


REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE = REPO_ROOT / "tools" / "dts_probe.py"


def _write_tei(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Britannicus</title>
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
          </sp>
        </div>
      </div>
    </body>
  </text>
</TEI>
""",
        encoding="utf-8",
    )


def _play(source: Path) -> PlayEntry:
    return PlayEntry(
        source_path=source,
        slug="britannicus",
        title="Britannicus",
        author="Jean Racine",
        document_type="dramatic_tei",
        has_text_body=True,
    )


def _build_site(tmp_path: Path) -> Path:
    source = tmp_path / "sources" / "britannicus.xml"
    site = tmp_path / "site"
    _write_tei(source)
    warnings = export_dts_static(site, (_play(source),), collection_title="Théâtre complet")
    assert warnings == ()
    return site


def _run_probe(site: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(PROBE), str(site), *args],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def test_dts_probe_text_mode_returns_success_for_generated_site(tmp_path: Path) -> None:
    site = _build_site(tmp_path)

    result = _run_probe(site)

    assert result.returncode == 0
    assert "DTS probe: site" in result.stdout
    assert "EntryPoint: OK" in result.stdout
    assert "Collection: Théâtre complet" in result.stdout
    assert "- britannicus — Britannicus" in result.stdout
    assert "Result: OK" in result.stdout


def test_dts_probe_json_mode_reports_success_for_generated_site(tmp_path: Path) -> None:
    site = _build_site(tmp_path)

    result = _run_probe(site, "--json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["resources"] == 1
    assert payload["citable_units"] == 3
    assert payload["fragments_ok"] == 3
    assert payload["errors"] == []


def test_dts_probe_reports_missing_fragment_without_stopping_early(tmp_path: Path) -> None:
    site = _build_site(tmp_path)
    missing_fragment = site / "api" / "dts" / "document" / "britannicus" / "A1S1L1.xml"
    missing_fragment.unlink()

    result = _run_probe(site)

    assert result.returncode == 1
    assert "ERROR: missing api/dts/document/britannicus/A1S1L1.xml" in result.stdout
    assert "Fragments XML: 2 OK" in result.stdout
    assert "Result: ERROR" in result.stdout
