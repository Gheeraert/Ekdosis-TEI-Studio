from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ets.dev.demo_pipeline_verbose import build_deep_demo_run, build_demo_run


def test_demo_pipeline_verbose_builds_xml_and_report() -> None:
    demo = build_demo_run()

    for expected in ["<TEI", "<body>", "<sp", "<l", "<app", "<lem", "<rdg"]:
        assert expected in demo.xml_text

    for title in [
        "ÉTAPE 0 - TRANSCRIPTION ETS",
        "ÉTAPE 1 - VALIDATION DU PROTOCOLE",
        "ÉTAPE 2 - ARBRE DRAMATIQUE",
        "ÉTAPE 3 - ARBRE CRITIQUE COLLATIONNÉ",
        "ÉTAPE 4 - ARBRE XML-TEI",
        "SYNTHÈSE",
    ]:
        assert title in demo.report


def test_demo_pipeline_verbose_script_runs() -> None:
    root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, "scripts/demo_pipeline_verbose.py"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "ÉTAPE 0 - TRANSCRIPTION ETS" in completed.stdout
    assert "Validation réussie." in completed.stdout


def test_demo_pipeline_verbose_deep_mode_builds_engine_zoom() -> None:
    demo = build_deep_demo_run()

    for expected in [
        "ZOOM MOTEUR",
        "readings",
        "tokens",
        "Segments collationnés",
        "candidate_class",
        "visibility_policy",
        "ElementTree",
        ".text",
        "tail",
        "<app",
        "<lem",
        "<rdg",
    ]:
        assert expected in demo.report


def test_demo_pipeline_verbose_deep_script_runs() -> None:
    root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, "scripts/demo_pipeline_verbose.py", "--deep"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "ZOOM MOTEUR" in completed.stdout
    assert "ElementTree" in completed.stdout


def test_demo_pipeline_verbose_deep_with_code_mode_builds_code_zoom() -> None:
    demo = build_deep_demo_run(with_code=True)

    for expected in [
        "Code exécuté ou cœur de la transformation",
        "parse_play(input_text, config)",
        "tokenize_parallel_readings(readings)",
        "collate_play(",
        "generate_tei_xml(",
        "ET.SubElement",
        "child.tail",
    ]:
        assert expected in demo.report


def test_demo_pipeline_verbose_deep_with_code_script_runs() -> None:
    root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, "scripts/demo_pipeline_verbose.py", "--deep-with-code"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "ZOOM MOTEUR" in completed.stdout
    assert "Code exécuté ou cœur de la transformation" in completed.stdout
    assert "ET.Element" in completed.stdout
