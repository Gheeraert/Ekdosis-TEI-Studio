from __future__ import annotations

from pathlib import Path

from ets.collation import collate_play
from ets.parser import load_config, parse_play
from ets.tei import generate_tei_xml
from ets.validation import InputValidationError, validate_input_text, validate_play_structure


def run_pipeline(input_path: str | Path, config_path: str | Path, reference_witness: int | None = None) -> str:
    config = load_config(config_path, reference_override=reference_witness)
    input_text = Path(input_path).read_text(encoding="utf-8")
    report = validate_input_text(input_text, len(config.witnesses))
    if report.has_errors:
        raise InputValidationError(report.diagnostics)
    parsed = parse_play(input_text, config)
    validate_play_structure(parsed)
    sigla = [w.siglum for w in config.witnesses]
    collated = collate_play(parsed, witness_sigla=sigla, reference_witness=config.reference_witness)
    return generate_tei_xml(collated, config)
