from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

from ets.castlist import build_castlist_tei_element, parse_castlist_text, validate_castlist_text
from ets.characters import characters_from_dramatis_personae
from ets.collation import collate_play
from ets.domain import Character, DramatisPersonae, EditionConfig
from ets.parser import load_config, parse_play
from ets.tei import generate_tei_xml
from ets.validation import InputValidationError, validate_input_text, validate_play_structure


@dataclass(frozen=True)
class CastlistContext:
    front_element: ET.Element
    dramatis_personae: DramatisPersonae
    characters: list[Character]


def load_castlist_context(
    config: EditionConfig,
    base_dir: Path | None,
) -> CastlistContext | None:
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
    return CastlistContext(
        front_element=build_castlist_tei_element(dramatis_personae, config),
        dramatis_personae=dramatis_personae,
        characters=characters_from_dramatis_personae(dramatis_personae),
    )


def run_pipeline_from_text(
    input_text: str,
    config: EditionConfig,
    *,
    validate_input: bool = True,
    castlist_base_dir: str | Path | None = None,
) -> str:
    base_dir = Path(castlist_base_dir) if castlist_base_dir is not None else None
    castlist_context = load_castlist_context(config, base_dir)
    front_elements: list[ET.Element] | None = None
    effective_characters: list[Character] = config.characters
    character_alias_hint = "Complete Personnages > aliases in the configuration if this speaker should receive @who."
    if castlist_context is not None:
        front_elements = [castlist_context.front_element]
        effective_characters = castlist_context.characters
        character_alias_hint = "Ajoutez éventuellement un alias dans le castlist."

    if validate_input:
        report = validate_input_text(
            input_text,
            len(config.witnesses),
            witness_sigla=[w.siglum for w in config.witnesses],
            characters=effective_characters,
            character_alias_hint=character_alias_hint,
        )
        if report.has_errors:
            raise InputValidationError(report.diagnostics)
    parsed = parse_play(input_text, config)
    validate_play_structure(parsed)
    sigla = [w.siglum for w in config.witnesses]
    collated = collate_play(parsed, witness_sigla=sigla, reference_witness=config.reference_witness)
    return generate_tei_xml(collated, config, front_elements=front_elements, characters=effective_characters)


def run_pipeline(input_path: str | Path, config_path: str | Path, reference_witness: int | None = None) -> str:
    resolved_config_path = Path(config_path).resolve()
    config = load_config(resolved_config_path, reference_override=reference_witness)
    input_text = Path(input_path).read_text(encoding="utf-8")
    return run_pipeline_from_text(input_text, config, castlist_base_dir=resolved_config_path.parent)
