from __future__ import annotations

import argparse
from pathlib import Path

from ets.core import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Minimal Ekdosis TEI Studio v2 core CLI")
    parser.add_argument("--input", required=True, help="Path to plain-text input file")
    parser.add_argument("--config", required=True, help="Path to fixture/config JSON file")
    parser.add_argument("--output", required=True, help="Output path for TEI XML")
    parser.add_argument(
        "--reference-witness",
        type=int,
        default=None,
        help="Optional zero-based reference witness index (defaults to last witness).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    xml_output = run_pipeline(
        input_path=args.input,
        config_path=args.config,
        reference_witness=args.reference_witness,
    )
    Path(args.output).write_text(xml_output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
