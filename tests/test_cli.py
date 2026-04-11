from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from ets.cli import main


def test_cli_writes_output_file() -> None:
    root = Path(__file__).resolve().parents[1]
    output_dir = root / "out"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "cli_test_output.xml"

    exit_code = main(
        [
            "--input",
            str(root / "fixtures" / "stable" / "input.txt"),
            "--config",
            str(root / "fixtures" / "stable" / "config.json"),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    ET.fromstring(output_path.read_text(encoding="utf-8"))
