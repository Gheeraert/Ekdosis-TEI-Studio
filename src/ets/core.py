from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from ets.castlist import build_castlist_tei_element, parse_castlist_text, validate_castlist_text
from ets.collation import collate_play
from ets.domain import EditionConfig
from ets.parser import load_config, parse_play
from ets.tei import generate_tei_xml
from ets.validation import InputValidationError, validate_input_text, validate_play_structure


def _load_castlist_front_element(config: EditionConfig, base_dir: Path | None) -> ET.Element | None:
    if not config.castlist_path.strip():
        return None
    raw_path = Path(config.castlist_path)
    castlist_path = raw_path if raw_path.is_absolute() else (base_dir or Path.cwd()) / raw_path
    if not castlist_path.exists():
        raise FileNotFoundError(f"Castlist file not found: {castlist_path}")

    text = castlist_path.read_text(encoding="utf-8")
    report = validate_castlist_text(text, config)
    if report.has_errors:
        raise InputValidationError(report.diagnostics)
    dramatis_personae = parse_castlist_text(text, config)
    return build_castlist_tei_element(dramatis_personae, config)


def run_pipeline_from_text(
    input_text: str,
    config: EditionConfig,
    *,
    validate_input: bool = True,
    castlist_base_dir: str | Path | None = None,
) -> str:
    if validate_input:
        report = validate_input_text(
            input_text,
            len(config.witnesses),
            witness_sigla=[w.siglum for w in config.witnesses],
            characters=config.characters,
        )
        if report.has_errors:
            raise InputValidationError(report.diagnostics)
    parsed = parse_play(input_text, config)
    validate_play_structure(parsed)
    sigla = [w.siglum for w in config.witnesses]
    collated = collate_play(parsed, witness_sigla=sigla, reference_witness=config.reference_witness)
    base_dir = Path(castlist_base_dir) if castlist_base_dir is not None else None
    front_element = _load_castlist_front_element(config, base_dir)
    return generate_tei_xml(collated, config, front_elements=[front_element] if front_element is not None else None)


def run_pipeline(input_path: str | Path, config_path: str | Path, reference_witness: int | None = None) -> str:
    resolved_config_path = Path(config_path).resolve()
    config = load_config(resolved_config_path, reference_override=reference_witness)
    input_text = Path(input_path).read_text(encoding="utf-8")
    return run_pipeline_from_text(input_text, config, castlist_base_dir=resolved_config_path.parent)
