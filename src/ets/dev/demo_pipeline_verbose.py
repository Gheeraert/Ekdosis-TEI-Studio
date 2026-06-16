from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import textwrap
import xml.etree.ElementTree as ET

from ets.collation import collate_play
from ets.collation.tokenizer import tokenize_parallel_readings
from ets.domain import (
    ApparatusTokenSegment,
    Character,
    CollatedImplicitStageSpan,
    CollatedLine,
    CollatedPlay,
    CollatedStanza,
    CollatedStageDirection,
    CollatedText,
    EditionConfig,
    ImplicitStageSpan,
    LiteralTokenSegment,
    Play,
    Speech,
    StageDirection,
    Stanza,
    TokenCollatedLine,
    VerseLine,
    Witness,
)
from ets.parser import parse_play
from ets.tei import generate_tei_xml
from ets.validation import DiagnosticLevel, validate_input_text, validate_play_structure


ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = ROOT / "fixtures" / "demo_pipeline_verbose" / "input.txt"
TEI_NS = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI_NS}
BAR = "=" * 60

PARSE_CODE = """
dramatic_play = parse_play(input_text, config)
validate_play_structure(dramatic_play)
"""

PARSE_ENGINE_CODE = """
fichier : src/ets/parser/text_parser.py
fonction : parse_play(...)

if _SCENE_RE.match(first) and not first.startswith("####"):
    current_scene = Scene(head_readings=_extract_wrapped(block, _SCENE_RE), head_block_index=block_index, cast_readings=[])
    current_act.scenes.append(current_scene)

if _SPEAKER_RE.match(first) and not first.startswith("##"):
    current_speech = Speech(speaker_readings=_extract_wrapped(block, _SPEAKER_RE), speaker_block_index=block_index)
    current_scene.speeches.append(current_speech)

direction = StageDirection(readings=readings, block_index=block_index)
current_scene.stage_directions.append(direction)

verse = VerseLine(
    number=number,
    readings=cleaned,
    block_index=block_index,
    whole_line_variant=whole_line_variant,
    met=met,
)
current_speech.elements.append(verse)
"""

VERSE_DUMP_CODE = """
return {
    "class": "VerseLine",
    "number": line.number,
    "part_equivalent": _shared_part_label(line.number),
    "whole_line_variant": line.whole_line_variant,
    "met": line.met,
    "readings": dict(zip(witness_sigla, line.readings)),
}
"""

STAGE_DUMP_CODE = """
return {
    "class": "StageDirection",
    "readings": dict(zip(witness_sigla, stage.readings)),
}
"""

IMPLICIT_DUMP_CODE = """
[_dump_verse_line(line, witness_sigla) for line in span.lines]
"""

TOKEN_CODE = """
token_matrix = tokenize_parallel_readings(readings)
return {
    siglum: tokens
    for siglum, tokens in zip(witness_sigla, token_matrix)
}
"""

TOKEN_ENGINE_CODE = """
fichier : src/ets/collation/tokenizer.py
fonction : tokenize_editorial_text(...) / tokenize_parallel_readings(...)

_SPACE_RE = re.compile(r"[ ]+")

def tokenize_editorial_text(text: str) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    return [token for token in _SPACE_RE.split(stripped) if token]

def tokenize_parallel_readings(readings: list[str]) -> list[list[str]]:
    return [tokenize_editorial_text(text) for text in readings]
"""

COLLATE_CODE = """
collated_play = collate_play(
    dramatic_play,
    witness_sigla=witness_sigla,
    reference_witness=config.reference_witness,
)
return [
    _dump_apparatus_segment(segment)
    if isinstance(segment, ApparatusTokenSegment)
    else _dump_literal_segment(segment)
    for segment in text.segments
]
"""

COLLATION_ENGINE_CODE = """
fichier : src/ets/collation/engine.py
fonction : align_variants_by_token(...) / build_apparatus_from_alignment(...)

for j, line in enumerate(token_matrix):
    token = line[i] if i < len(line) else ""
    if token not in tokens_by_column:
        order.append(token)
    tokens_by_column[token].append(witness_sigla[j])

lemma = CollatedReading(text=lemma_token, witness_sigla=tokens_by_column[lemma_token])
readings = [
    CollatedReading(text=token, witness_sigla=tokens_by_column[token])
    for token in non_empty_order
    if token != lemma_token
]

if is_literal:
    segments.append(LiteralTokenSegment(text=lemma.text + suffix))
else:
    classification = classify_apparatus(lemma.text, [reading.text for reading in readings])
    segments.append(
        ApparatusTokenSegment(
            lemma=CollatedReading(text=lemma.text + suffix, witness_sigla=lemma.witness_sigla),
            readings=classified_readings,
            candidate_class=classification.candidate_class,
            visibility_policy=classification.visibility_policy,
            rule_code=classification.rule_code,
        )
    )
"""

MINOR_VARIANT_ENGINE_CODE = """
fichier : src/ets/collation/minor_variants.py
fonction : classify_pair(...) / aggregate_pair_classifications(...)

if letters_and_numbers(left_norm) == letters_and_numbers(right_norm) and has_punctuation_difference(left_norm, right_norm):
    return VariantClassification("minor_punctuation", "hide_safe", "punctuation_only", "punctuation_only")

if (
    letters_and_numbers_unaccented(left_norm) == letters_and_numbers_unaccented(right_norm)
    and letters_and_numbers(left_norm) != letters_and_numbers(right_norm)
):
    return VariantClassification("minor_graphic_safe", "hide_safe", "accent", "accent_only")

left_graphic, left_rules = apply_historic_graphic_rules(left_norm)
right_graphic, right_rules = apply_historic_graphic_rules(right_norm)
if left_graphic == right_graphic and left_graphic:
    rules = sorted(set(left_rules) | set(right_rules))
    rule_code = "+".join(rules) if rules else "historic_graphic_key_identity"
    return VariantClassification(
        "minor_graphic_safe", "hide_safe", rule_code, "historic_graphic_key_identity"
    )
"""

APPARATUS_DUMP_CODE = """
return {
    "type": "apparatus",
    "lemma": {
        "wit": segment.lemma.witness_sigla,
        "text": segment.lemma.text,
    },
    "readings": [
        {
            "wit": reading.witness_sigla,
            "text": reading.text,
        }
        for reading in segment.readings
    ],
    "candidate_class": segment.candidate_class,
    "visibility_policy": segment.visibility_policy,
    "rule_code": segment.rule_code,
}
"""

GENERATE_CODE = """
xml_text = generate_tei_xml(collated_play, config, characters=config.characters)
xml_root = ET.fromstring(xml_text)
"""

TEI_ENGINE_CODE = """
fichier : src/ets/tei/generator.py
fonction : _append_collated_line(...) / _append_collated_text(...) / _append_text(...)

attrs = {"n": line.number}
if line_xml_id:
    attrs["xml:id"] = line_xml_id
l_element = ET.SubElement(parent, _tei("l"), attrs)
if isinstance(line, TokenCollatedLine):
    _append_collated_text(l_element, line.text)
    return

app = ET.SubElement(app_parent, _tei("app"), app_attrs)
_append_reading(app, "lem", segment.lemma)
for rdg in segment.readings:
    _append_reading(app, "rdg", rdg)

def _append_text(container: ET.Element, last_child: ET.Element | None, text: str) -> None:
    if last_child is None:
        container.text = (container.text or "") + text
    else:
        last_child.tail = (last_child.tail or "") + text
"""

ELEMENTTREE_PRINCIPLE_CODE = """
tei = ET.Element(_tei("TEI"))
tei_header = ET.SubElement(tei, _tei("teiHeader"))
l_element = ET.SubElement(parent, _tei("l"), attrs)
app = ET.SubElement(parent, _tei("app"), app_attrs)
last_child.tail = (last_child.tail or "") + text
"""

XML_DUMP_CODE = """
return {
    "tag": element.tag,
    "attrib": dict(element.attrib),
    "text": element.text,
    "tail": element.tail,
    "children": [
        {"tag": child.tag, "attrib": dict(child.attrib), "text": child.text, "tail": child.tail}
        for child in list(element)
    ],
}
"""


@dataclass(frozen=True)
class DemoRun:
    report: str
    xml_text: str


@dataclass(frozen=True)
class PipelineState:
    input_text: str
    config: EditionConfig
    witness_sigla: list[str]
    validation_report: object
    dramatic_play: Play
    collated_play: CollatedPlay
    xml_text: str
    xml_root: ET.Element
    raw_blocks: list[list[str]]


def build_demo_config() -> EditionConfig:
    return EditionConfig(
        title="Démonstration Ekdosis-TEI Studio",
        author="Exemple pédagogique",
        editor="Atelier ETS",
        witnesses=[
            Witness(siglum="A", year="1670", description="Témoin de référence"),
            Witness(siglum="B", year="1671", description="Témoin collationné"),
        ],
        reference_witness=0,
        transcriber="Démonstration",
        characters=[
            Character(id="iocaste", label="Iocaste", aliases=["IOCASTE", "JOCASTE"]),
            Character(id="olympe", label="Olympe", aliases=["OLYMPE"]),
        ],
    )


def load_demo_transcription() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


def build_demo_run(*, deep: bool = False, with_code: bool = False) -> DemoRun:
    state = _build_pipeline_state()
    deep = deep or with_code
    report_sections = [
        _section_source(state.input_text),
        _section_validation(state.validation_report),
        _section_dramatic_tree(state.dramatic_play),
        _section_collated_tree(state.collated_play),
        _section_tei_tree(state.xml_text),
    ]
    if deep:
        report_sections.append(_section_engine_zoom(state, with_code=with_code))
    report_sections.append(_section_synthesis())
    return DemoRun(report="\n\n".join(report_sections), xml_text=state.xml_text)


def build_deep_demo_run(*, with_code: bool = False) -> DemoRun:
    return build_demo_run(deep=True, with_code=with_code)


def _build_pipeline_state() -> PipelineState:
    input_text = load_demo_transcription()
    config = build_demo_config()
    witness_sigla = [witness.siglum for witness in config.witnesses]

    validation_report = validate_input_text(
        input_text,
        len(config.witnesses),
        witness_sigla=witness_sigla,
        characters=config.characters,
    )
    if validation_report.has_errors:
        messages = "; ".join(item.message for item in validation_report.diagnostics[:5])
        raise ValueError(f"La fixture verbose doit rester valide: {messages}")

    dramatic_play = parse_play(input_text, config)
    validate_play_structure(dramatic_play)
    collated_play = collate_play(
        dramatic_play,
        witness_sigla=witness_sigla,
        reference_witness=config.reference_witness,
    )
    xml_text = generate_tei_xml(collated_play, config, characters=config.characters)
    return PipelineState(
        input_text=input_text,
        config=config,
        witness_sigla=witness_sigla,
        validation_report=validation_report,
        dramatic_play=dramatic_play,
        collated_play=collated_play,
        xml_text=xml_text,
        xml_root=ET.fromstring(xml_text),
        raw_blocks=_split_raw_blocks(input_text),
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Démonstration verbose du pipeline ETS -> TEI.")
    parser.add_argument(
        "--deep",
        action="store_true",
        help="Afficher des zooms moteur sur les readings, tokens, segments collationnés et éléments XML.",
    )
    parser.add_argument(
        "--deep-with-code",
        action="store_true",
        help="Afficher les zooms moteur avec les extraits de code qui réalisent les transformations.",
    )
    args = parser.parse_args(argv)
    print(build_demo_run(deep=args.deep, with_code=args.deep_with_code).report)


def _section(title: str) -> list[str]:
    return [BAR, title, BAR, ""]


def _section_source(input_text: str) -> str:
    lines = _section("ÉTAPE 0 - TRANSCRIPTION ETS")
    lines.extend(
        [
            "Fonction :",
            "  Texte source fourni par l'éditeur scientifique.",
            "",
            "Rôle :",
            "  La transcription reste lisible dans un simple fichier texte.",
            "  Les témoins sont saisis en parallèle, bloc par bloc.",
            "",
            "Extrait :",
        ]
    )
    source_lines = input_text.splitlines()
    excerpt = source_lines[:22]
    lines.extend(f"  {line}" for line in excerpt)
    if len(source_lines) > len(excerpt):
        lines.append("  ...")
    return "\n".join(lines)


def _section_validation(report) -> str:
    error_count = sum(1 for item in report.diagnostics if item.level == DiagnosticLevel.ERROR)
    warning_count = sum(1 for item in report.diagnostics if item.level == DiagnosticLevel.WARNING)
    lines = _section("ÉTAPE 1 - VALIDATION DU PROTOCOLE")
    lines.extend(
        [
            "Classe / méthode :",
            "  validate_input_text(...)",
            "",
            "Fonction :",
            "  Vérifier que le pseudo-markdown ETS est bien formé avant toute génération.",
            "",
            "Résultat :",
            "  Validation réussie.",
            f"  Nombre d'erreurs : {error_count}",
            f"  Nombre d'avertissements : {warning_count}",
        ]
    )
    return "\n".join(lines)


def _section_dramatic_tree(play: Play) -> str:
    stats = _dramatic_stats(play)
    lines = _section("ÉTAPE 2 - ARBRE DRAMATIQUE")
    lines.extend(
        [
            "Classe / méthode :",
            "  parse_play(...)",
            "  Play / Act / Scene / Speech / VerseLine",
            "",
            "Fonction :",
            "  Transformer la transcription en modèle dramatique structuré.",
            "",
            "Résultat :",
            f"  Actes : {stats['acts']}",
            f"  Scènes : {stats['scenes']}",
            f"  Discours : {stats['speeches']}",
            f"  Vers : {stats['verses']}",
            f"  Didascalies explicites : {stats['explicit_stages']}",
            f"  Didascalies implicites : {stats['implicit_stages']}",
            f"  Vers partagés : {stats['shared_verses']}",
            "",
            "Extrait d'arbre :",
        ]
    )
    lines.extend(f"  {line}" for line in _dramatic_tree_excerpt(play))
    return "\n".join(lines)


def _section_collated_tree(collated: CollatedPlay) -> str:
    stats = _collated_stats(collated)
    example = _first_apparatus_example(collated)
    lines = _section("ÉTAPE 3 - ARBRE CRITIQUE COLLATIONNÉ")
    lines.extend(
        [
            "Classe / méthode :",
            "  collate_play(...)",
            "  CollatedText / ApparatusTokenSegment / CollatedReading",
            "",
            "Fonction :",
            "  Aligner les témoins, produire les lemmes et les lectures variantes,",
            "  distinguer variantes substantielles et variantes mineures.",
            "",
            "Résultat :",
            f"  Lignes collationnées : {stats['lines']}",
            f"  Segments littéraux : {stats['literal_segments']}",
            f"  Segments d'apparat : {stats['apparatus_segments']}",
            f"  Variantes mineures repérées : {stats['minor_variants']}",
            f"  Variantes substantielles : {stats['substantive_variants']}",
            "",
            "Exemple :",
        ]
    )
    if example is None:
        lines.append("  Aucun segment d'apparat dans la fixture.")
    else:
        lines.extend(
            [
                f"  ligne {example['line']} - lem {example['lemma_wit']} : {example['lemma']}",
                f"  ligne {example['line']} - rdg {example['rdg_wit']} : {example['rdg']}",
                f"  classification : {_classification_label(example['class'])}",
            ]
        )
    return "\n".join(lines)


def _section_tei_tree(xml_text: str) -> str:
    root = ET.fromstring(xml_text)
    stats = {
        "root": _local_name(root.tag),
        "header": root.find("tei:teiHeader", NS) is not None,
        "body": root.find(".//tei:body", NS) is not None,
        "acts": len(root.findall(".//tei:div[@type='act']", NS)),
        "scenes": len(root.findall(".//tei:div[@type='scene']", NS)),
        "sp": len(root.findall(".//tei:sp", NS)),
        "l": len(root.findall(".//tei:l", NS)),
        "app": len(root.findall(".//tei:app", NS)),
        "lem": len(root.findall(".//tei:lem", NS)),
        "rdg": len(root.findall(".//tei:rdg", NS)),
    }
    lines = _section("ÉTAPE 4 - ARBRE XML-TEI")
    lines.extend(
        [
            "Classe / méthode :",
            "  generate_tei_xml(...)",
            "  xml.etree.ElementTree.Element / ElementTree",
            "",
            "Fonction :",
            "  Transformer le modèle critique en arbre XML-TEI, puis sérialiser l'XML final.",
            "",
            "Résultat :",
            f"  Racine : <{stats['root']}>",
            f"  Header : {_present(stats['header'])}",
            f"  Body : {_present(stats['body'])}",
            f"  <div type=\"act\"> : {stats['acts']}",
            f"  <div type=\"scene\"> : {stats['scenes']}",
            f"  <sp> : {stats['sp']}",
            f"  <l> : {stats['l']}",
            f"  <app> : {stats['app']}",
            f"  <lem> : {stats['lem']}",
            f"  <rdg> : {stats['rdg']}",
            "",
            "Extrait XML :",
        ]
    )
    lines.extend(f"  {line}" for line in _xml_excerpt(root).splitlines())
    return "\n".join(lines)


def _section_engine_zoom(state: PipelineState, *, with_code: bool = False) -> str:
    act = state.dramatic_play.acts[0]
    scene = act.scenes[0]
    first_speech = scene.speeches[0]
    second_speech = scene.speeches[1]
    collated_scene = state.collated_play.acts[0].scenes[0]
    first_collated_speech = collated_scene.speeches[0]
    second_collated_speech = collated_scene.speeches[1]

    graphic_verse = _speech_element(first_speech, 0, VerseLine)
    punctuation_verse = _speech_element(first_speech, 1, VerseLine)
    implicit_span = _speech_element(first_speech, 2, ImplicitStageSpan)
    shared_start = _speech_element(first_speech, 3, VerseLine)
    shared_end = _speech_element(second_speech, 0, VerseLine)

    graphic_line = _collated_element(first_collated_speech, 0, TokenCollatedLine)
    punctuation_line = _collated_element(first_collated_speech, 1, TokenCollatedLine)
    collated_implicit = _collated_element(first_collated_speech, 2, CollatedImplicitStageSpan)
    shared_start_line = _collated_element(first_collated_speech, 3, TokenCollatedLine)
    shared_end_line = _collated_element(second_collated_speech, 0, TokenCollatedLine)

    sections = [
        _zoom_verse(
            title="ZOOM MOTEUR 1 - UN VERS AVEC VARIANTE GRAPHIQUE",
            witness_sigla=state.witness_sigla,
            raw_block=_raw_block(state, graphic_verse.block_index),
            verse=graphic_verse,
            collated_line=graphic_line,
            xml_element=_xml_line(state.xml_root, graphic_verse.number),
            with_code=with_code,
        ),
        _zoom_verse(
            title="ZOOM MOTEUR 2 - UN VERS AVEC VARIANTE DE PONCTUATION",
            witness_sigla=state.witness_sigla,
            raw_block=_raw_block(state, punctuation_verse.block_index),
            verse=punctuation_verse,
            collated_line=punctuation_line,
            xml_element=_xml_line(state.xml_root, punctuation_verse.number),
            with_code=with_code,
        ),
        _zoom_explicit_stage(
            witness_sigla=state.witness_sigla,
            raw_block=_raw_block(state, scene.stage_directions[0].block_index),
            stage=scene.stage_directions[0],
            collated_stage=collated_scene.stage_directions[0],
            xml_element=_explicit_stage_element(state.xml_root),
            with_code=with_code,
        ),
        _zoom_implicit_stage(
            witness_sigla=state.witness_sigla,
            raw_open=_raw_block(state, implicit_span.block_index_open),
            raw_line=_raw_block(state, implicit_span.lines[0].block_index),
            raw_close=_raw_block(state, implicit_span.lines[0].block_index + 1),
            span=implicit_span,
            collated_span=collated_implicit,
            xml_element=_implicit_stage_element(state.xml_root),
            with_code=with_code,
        ),
        _zoom_shared_verse(
            witness_sigla=state.witness_sigla,
            raw_start=_raw_block(state, shared_start.block_index),
            raw_end=_raw_block(state, shared_end.block_index),
            start_verse=shared_start,
            end_verse=shared_end,
            start_line=shared_start_line,
            end_line=shared_end_line,
            start_xml=_xml_line(state.xml_root, shared_start.number),
            end_xml=_xml_line(state.xml_root, shared_end.number),
            with_code=with_code,
        ),
    ]
    return "\n\n".join(sections)


def _zoom_verse(
    *,
    title: str,
    witness_sigla: list[str],
    raw_block: list[str],
    verse: VerseLine,
    collated_line: TokenCollatedLine,
    xml_element: ET.Element,
    with_code: bool,
) -> str:
    lines = _section(title)
    lines.extend(_raw_lines("Transcription brute :", witness_sigla, raw_block))
    lines.extend(
        [
            "",
            "Après parse_play(...) :",
            *_maybe_code(with_code, "Code exécuté ou cœur de la transformation :", PARSE_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur, abrégé :", PARSE_ENGINE_CODE),
            *_maybe_code(with_code, "Code de représentation pédagogique :", VERSE_DUMP_CODE),
            "  Classe : VerseLine",
            f"  number : {verse.number}",
            "  readings :",
            _indent(_json(_dump_verse_line(verse, witness_sigla)), 4),
            "",
            "Après tokenisation explicite (chaîne brute -> tokens) :",
            *_maybe_code(with_code, "Code exécuté ou cœur de la transformation :", TOKEN_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur :", TOKEN_ENGINE_CODE),
            _indent(_json(_dump_tokens(verse.readings, witness_sigla)), 4),
            "",
            "Après collate_play(...) :",
            *_maybe_code(with_code, "Code exécuté ou cœur de la transformation :", COLLATE_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur, abrégé :", COLLATION_ENGINE_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur, classement des variantes :", MINOR_VARIANT_ENGINE_CODE),
            *_maybe_code(with_code, "Construction du dictionnaire d’apparat :", APPARATUS_DUMP_CODE),
            "  Segments collationnés :",
            _indent(_json(_dump_collated_text(collated_line.text)), 4),
            "",
            "Après generate_tei_xml(...) :",
            *_maybe_code(with_code, "Code exécuté ou cœur de la transformation :", GENERATE_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur, abrégé :", TEI_ENGINE_CODE),
            *_maybe_code(with_code, "Principe ElementTree :", ELEMENTTREE_PRINCIPLE_CODE),
            _indent(_element_xml(xml_element), 2),
            "",
            "ElementTree :",
            *_maybe_code(with_code, "Code de dump ElementTree :", XML_DUMP_CODE),
            _indent(_element_tree_debug(xml_element), 2),
        ]
    )
    return "\n".join(lines)


def _zoom_explicit_stage(
    *,
    witness_sigla: list[str],
    raw_block: list[str],
    stage: StageDirection,
    collated_stage: CollatedStageDirection,
    xml_element: ET.Element,
    with_code: bool,
) -> str:
    lines = _section("ZOOM MOTEUR 3 - UNE DIDASCALIE EXPLICITE")
    lines.extend(_raw_lines("Transcription brute :", witness_sigla, raw_block))
    lines.extend(
        [
            "",
            "Après parse_play(...) :",
            *_maybe_code(with_code, "Code exécuté ou cœur de la transformation :", PARSE_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur, abrégé :", PARSE_ENGINE_CODE),
            *_maybe_code(with_code, "Code de représentation pédagogique :", STAGE_DUMP_CODE),
            "  Classe : StageDirection",
            "  readings :",
            _indent(_json(_dump_stage_direction(stage, witness_sigla)), 4),
            "",
            "Après tokenisation explicite (chaîne brute -> tokens) :",
            *_maybe_code(with_code, "Code exécuté ou cœur de la transformation :", TOKEN_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur :", TOKEN_ENGINE_CODE),
            _indent(_json(_dump_tokens(stage.readings, witness_sigla)), 4),
            "",
            "Après collate_play(...) :",
            *_maybe_code(with_code, "Code exécuté ou cœur de la transformation :", COLLATE_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur, abrégé :", COLLATION_ENGINE_CODE),
            "  CollatedStageDirection.text :",
            _indent(_json(_dump_collated_text(collated_stage.text)), 4),
            "",
            "Après generate_tei_xml(...) :",
            *_maybe_code(with_code, "Code exécuté ou cœur de la transformation :", GENERATE_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur, abrégé :", TEI_ENGINE_CODE),
            *_maybe_code(with_code, "Principe ElementTree :", ELEMENTTREE_PRINCIPLE_CODE),
            _indent(_element_xml(xml_element), 2),
            "",
            "ElementTree :",
            *_maybe_code(with_code, "Code de dump ElementTree :", XML_DUMP_CODE),
            _indent(_element_tree_debug(xml_element), 2),
        ]
    )
    return "\n".join(lines)


def _zoom_implicit_stage(
    *,
    witness_sigla: list[str],
    raw_open: list[str],
    raw_line: list[str],
    raw_close: list[str],
    span: ImplicitStageSpan,
    collated_span: CollatedImplicitStageSpan,
    xml_element: ET.Element,
    with_code: bool,
) -> str:
    lines = _section("ZOOM MOTEUR 4 - UNE DIDASCALIE IMPLICITE TYPÉE")
    lines.extend(["Transcription brute :"])
    for label, block in [("ouverture", raw_open), ("ligne", raw_line), ("fermeture", raw_close)]:
        lines.append(f"  {label} :")
        lines.extend(f"    {siglum} : {value}" for siglum, value in zip(witness_sigla, block))
    lines.extend(
        [
            "",
            "Après parse_play(...) :",
            *_maybe_code(with_code, "Code exécuté ou cœur de la transformation :", PARSE_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur, abrégé :", PARSE_ENGINE_CODE),
            *_maybe_code(with_code, "Code de représentation pédagogique :", IMPLICIT_DUMP_CODE),
            "  Classe : ImplicitStageSpan",
            f"  category : {span.category}",
            "  lines :",
            _indent(_json([_dump_verse_line(line, witness_sigla) for line in span.lines]), 4),
            "",
            "Après tokenisation explicite de la ligne contenue (chaîne brute -> tokens) :",
            *_maybe_code(with_code, "Code exécuté ou cœur de la transformation :", TOKEN_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur :", TOKEN_ENGINE_CODE),
            _indent(_json(_dump_tokens(span.lines[0].readings, witness_sigla)), 4),
            "",
            "Après collate_play(...) :",
            *_maybe_code(with_code, "Code exécuté ou cœur de la transformation :", COLLATE_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur, abrégé :", COLLATION_ENGINE_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur, classement des variantes :", MINOR_VARIANT_ENGINE_CODE),
            *_maybe_code(with_code, "Construction du dictionnaire d’apparat :", APPARATUS_DUMP_CODE),
            "  Classe : CollatedImplicitStageSpan",
            "  lines :",
            _indent(_json([_dump_collated_line(line) for line in collated_span.lines]), 4),
            "",
            "Après generate_tei_xml(...) :",
            *_maybe_code(with_code, "Code exécuté ou cœur de la transformation :", GENERATE_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur, abrégé :", TEI_ENGINE_CODE),
            *_maybe_code(with_code, "Principe ElementTree :", ELEMENTTREE_PRINCIPLE_CODE),
            _indent(_element_xml(xml_element), 2),
            "",
            "ElementTree :",
            *_maybe_code(with_code, "Code de dump ElementTree :", XML_DUMP_CODE),
            _indent(_element_tree_debug(xml_element), 2),
        ]
    )
    return "\n".join(lines)


def _zoom_shared_verse(
    *,
    witness_sigla: list[str],
    raw_start: list[str],
    raw_end: list[str],
    start_verse: VerseLine,
    end_verse: VerseLine,
    start_line: TokenCollatedLine,
    end_line: TokenCollatedLine,
    start_xml: ET.Element,
    end_xml: ET.Element,
    with_code: bool,
) -> str:
    lines = _section("ZOOM MOTEUR 5 - UN VERS PARTAGÉ")
    lines.extend(["Transcription brute :"])
    lines.append("  fragment initial :")
    lines.extend(f"    {siglum} : {value}" for siglum, value in zip(witness_sigla, raw_start))
    lines.append("  fragment final :")
    lines.extend(f"    {siglum} : {value}" for siglum, value in zip(witness_sigla, raw_end))
    lines.extend(
        [
            "",
            "Après parse_play(...) :",
            *_maybe_code(with_code, "Code exécuté ou cœur de la transformation :", PARSE_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur, abrégé :", PARSE_ENGINE_CODE),
            *_maybe_code(with_code, "Code de représentation pédagogique :", VERSE_DUMP_CODE),
            "  Le modèle courant encode le partage dans le numéro de vers.",
            "  part équivalent : 4.1 = fragment initial ; 4.2 = fragment final.",
            "  objets :",
            _indent(_json([_dump_verse_line(start_verse, witness_sigla), _dump_verse_line(end_verse, witness_sigla)]), 4),
            "",
            "Après tokenisation explicite (chaîne brute -> tokens) :",
            *_maybe_code(with_code, "Code exécuté ou cœur de la transformation :", TOKEN_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur :", TOKEN_ENGINE_CODE),
            _indent(
                _json(
                    {
                        "fragment_initial": _dump_tokens(start_verse.readings, witness_sigla),
                        "fragment_final": _dump_tokens(end_verse.readings, witness_sigla),
                    }
                ),
                4,
            ),
            "",
            "Après collate_play(...) :",
            *_maybe_code(with_code, "Code exécuté ou cœur de la transformation :", COLLATE_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur, abrégé :", COLLATION_ENGINE_CODE),
            "  fragments collationnés :",
            _indent(_json([_dump_collated_line(start_line), _dump_collated_line(end_line)]), 4),
            "",
            "Après generate_tei_xml(...) :",
            *_maybe_code(with_code, "Code exécuté ou cœur de la transformation :", GENERATE_CODE),
            *_maybe_code(with_code, "Extrait réel du moteur, abrégé :", TEI_ENGINE_CODE),
            *_maybe_code(with_code, "Principe ElementTree :", ELEMENTTREE_PRINCIPLE_CODE),
            _indent(_element_xml(start_xml), 2),
            _indent(_element_xml(end_xml), 2),
            "",
            "ElementTree :",
            *_maybe_code(with_code, "Code de dump ElementTree :", XML_DUMP_CODE),
            _indent(_element_tree_debug(start_xml), 2),
            _indent(_element_tree_debug(end_xml), 2),
        ]
    )
    return "\n".join(lines)


def _section_synthesis() -> str:
    lines = _section("SYNTHÈSE")
    lines.extend(
        [
            "La TEI n'est pas produite directement par substitution de chaînes.",
            "Elle est la sérialisation finale d'un modèle intermédiaire :",
            "",
            "  1. arbre dramatique ;",
            "  2. arbre critique collationné ;",
            "  3. arbre XML-TEI.",
            "",
            "Cette architecture rend la chaîne plus contrôlable, plus testable,",
            "et plus facilement extensible.",
        ]
    )
    return "\n".join(lines)


def _dramatic_stats(play: Play) -> dict[str, int]:
    speeches = [speech for act in play.acts for scene in act.scenes for speech in scene.speeches]
    verses = list(_iter_verse_lines(play))
    return {
        "acts": len(play.acts),
        "scenes": sum(len(act.scenes) for act in play.acts),
        "speeches": len(speeches),
        "verses": len(verses),
        "explicit_stages": sum(
            len(scene.stage_directions) + sum(len(speech.stage_directions) for speech in scene.speeches)
            for act in play.acts
            for scene in act.scenes
        ),
        "implicit_stages": sum(
            1
            for speech in speeches
            for element in speech.elements
            if isinstance(element, ImplicitStageSpan)
        ),
        "shared_verses": sum(1 for verse in verses if "." in verse.number),
    }


def _iter_verse_lines(play: Play):
    for act in play.acts:
        for scene in act.scenes:
            for speech in scene.speeches:
                for element in speech.elements:
                    if isinstance(element, VerseLine):
                        yield element
                    elif isinstance(element, ImplicitStageSpan):
                        yield from element.lines
                    elif isinstance(element, Stanza):
                        yield from element.lines


def _dramatic_tree_excerpt(play: Play) -> list[str]:
    if not play.acts:
        return ["Play"]
    lines = ["Play"]
    act = play.acts[0]
    lines.append(f"+-- Act n=1 head={_readings(act.head_readings)}")
    if not act.scenes:
        return lines
    scene = act.scenes[0]
    lines.append(f"    +-- Scene n=1 head={_readings(scene.head_readings)}")
    if scene.cast_readings:
        lines.append(f"        +-- Cast readings={_readings(scene.cast_readings)}")
    for stage in scene.stage_directions[:1]:
        lines.append(f"        +-- StageDirection readings={len(stage.readings)}")
    for speech in scene.speeches[:2]:
        lines.extend(_speech_tree_excerpt(speech))
    return lines


def _speech_tree_excerpt(speech: Speech) -> list[str]:
    lines = [f"        +-- Speech speaker={_readings(speech.speaker_readings)}"]
    for element in speech.elements[:4]:
        if isinstance(element, VerseLine):
            part = " shared" if "." in element.number else ""
            lines.append(f"            +-- VerseLine n={element.number}{part} readings={len(element.readings)}")
        elif isinstance(element, StageDirection):
            lines.append(f"            +-- StageDirection readings={len(element.readings)}")
        elif isinstance(element, ImplicitStageSpan):
            lines.append(f"            +-- ImplicitStageSpan category={element.category}")
            for verse in element.lines[:1]:
                lines.append(f"                +-- VerseLine n={verse.number} readings={len(verse.readings)}")
        elif isinstance(element, Stanza):
            lines.append(f"            +-- Stanza lines={len(element.lines)}")
    return lines


def _collated_stats(collated: CollatedPlay) -> dict[str, int]:
    segments = [segment for text in _iter_collated_texts(collated) for segment in text.segments]
    apparatus = [segment for segment in segments if isinstance(segment, ApparatusTokenSegment)]
    return {
        "lines": sum(1 for _ in _iter_collated_lines(collated)),
        "literal_segments": sum(1 for segment in segments if isinstance(segment, LiteralTokenSegment)),
        "apparatus_segments": len(apparatus),
        "minor_variants": sum(1 for segment in apparatus if segment.visibility_policy in {"hide_safe", "inspect"}),
        "substantive_variants": sum(1 for segment in apparatus if segment.visibility_policy == "visible"),
    }


def _iter_collated_texts(collated: CollatedPlay):
    for act in collated.acts:
        yield act.head
        for scene in act.scenes:
            yield scene.head
            if scene.cast:
                yield scene.cast
            for stage in scene.stage_directions:
                yield stage.text
            for speech in scene.speeches:
                yield speech.speaker
                for element in speech.elements:
                    if isinstance(element, CollatedStageDirection):
                        yield element.text
                    elif isinstance(element, TokenCollatedLine):
                        yield element.text
                    elif isinstance(element, CollatedImplicitStageSpan):
                        for line in element.lines:
                            if isinstance(line, TokenCollatedLine):
                                yield line.text
                    elif isinstance(element, CollatedStanza):
                        for line in element.lines:
                            if isinstance(line, TokenCollatedLine):
                                yield line.text


def _iter_collated_lines(collated: CollatedPlay):
    for act in collated.acts:
        for scene in act.scenes:
            for speech in scene.speeches:
                for element in speech.elements:
                    if isinstance(element, (TokenCollatedLine,)):
                        yield element
                    elif isinstance(element, CollatedImplicitStageSpan):
                        yield from element.lines
                    elif isinstance(element, CollatedStanza):
                        yield from element.lines


def _dump_verse_line(line: VerseLine, witness_sigla: list[str]) -> dict:
    return {
        "class": "VerseLine",
        "number": line.number,
        "part_equivalent": _shared_part_label(line.number),
        "whole_line_variant": line.whole_line_variant,
        "met": line.met,
        "readings": dict(zip(witness_sigla, line.readings)),
    }


def _dump_stage_direction(stage: StageDirection, witness_sigla: list[str]) -> dict:
    return {
        "class": "StageDirection",
        "readings": dict(zip(witness_sigla, stage.readings)),
    }


def _dump_tokens(readings: list[str], witness_sigla: list[str]) -> dict:
    token_matrix = tokenize_parallel_readings(readings)
    return {
        siglum: tokens
        for siglum, tokens in zip(witness_sigla, token_matrix)
    }


def _dump_collated_line(line: CollatedLine) -> dict:
    if isinstance(line, TokenCollatedLine):
        return {
            "class": "TokenCollatedLine",
            "number": line.number,
            "met": line.met,
            "text": _dump_collated_text(line.text),
        }
    return {
        "class": type(line).__name__,
        "number": getattr(line, "number", None),
    }


def _dump_collated_text(text: CollatedText) -> list[dict]:
    return [
        _dump_apparatus_segment(segment)
        if isinstance(segment, ApparatusTokenSegment)
        else _dump_literal_segment(segment)
        for segment in text.segments
    ]


def _dump_apparatus_segment(segment: ApparatusTokenSegment) -> dict:
    return {
        "type": "apparatus",
        "lemma": {
            "wit": segment.lemma.witness_sigla,
            "text": segment.lemma.text,
        },
        "readings": [
            {
                "wit": reading.witness_sigla,
                "text": reading.text,
            }
            for reading in segment.readings
        ],
        "candidate_class": segment.candidate_class,
        "visibility_policy": segment.visibility_policy,
        "rule_code": segment.rule_code,
    }


def _dump_literal_segment(segment: LiteralTokenSegment) -> dict:
    return {
        "type": "literal",
        "text": segment.text,
    }


def _dump_xml_element(element: ET.Element) -> dict:
    return {
        "tag": element.tag,
        "attrib": dict(element.attrib),
        "text": element.text,
        "tail": element.tail,
        "children": [
            {
                "index": index,
                "tag": child.tag,
                "attrib": dict(child.attrib),
                "text": child.text,
                "tail": child.tail,
            }
            for index, child in enumerate(list(element))
        ],
    }


def _first_apparatus_example(collated: CollatedPlay) -> dict[str, str] | None:
    for line in _iter_collated_lines(collated):
        if not isinstance(line, TokenCollatedLine):
            continue
        for segment in line.text.segments:
            if isinstance(segment, ApparatusTokenSegment) and segment.readings:
                rdg = segment.readings[0]
                return {
                    "line": line.number,
                    "lemma": segment.lemma.text.strip(),
                    "lemma_wit": "+".join(segment.lemma.witness_sigla),
                    "rdg": rdg.text.strip(),
                    "rdg_wit": "+".join(rdg.witness_sigla),
                    "class": segment.candidate_class,
                }
    return None


def _split_raw_blocks(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        if line.strip() == "":
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)
    if current:
        blocks.append(current)
    return blocks


def _raw_block(state: PipelineState, block_index: int) -> list[str]:
    return state.raw_blocks[block_index]


def _speech_element(speech: Speech, index: int, expected_type):
    element = speech.elements[index]
    if not isinstance(element, expected_type):
        raise TypeError(f"Expected {expected_type.__name__}, got {type(element).__name__}.")
    return element


def _collated_element(speech, index: int, expected_type):
    element = speech.elements[index]
    if not isinstance(element, expected_type):
        raise TypeError(f"Expected {expected_type.__name__}, got {type(element).__name__}.")
    return element


def _xml_line(root: ET.Element, number: str) -> ET.Element:
    element = root.find(f".//tei:l[@n='{number}']", NS)
    if element is None:
        raise ValueError(f"Missing TEI line n={number}.")
    return element


def _explicit_stage_element(root: ET.Element) -> ET.Element:
    for element in root.findall(".//tei:stage", NS):
        xml_id = element.attrib.get("{http://www.w3.org/XML/1998/namespace}id", "")
        if xml_id.endswith("ST1"):
            return element
    raise ValueError("Missing explicit stage element.")


def _implicit_stage_element(root: ET.Element) -> ET.Element:
    element = root.find(".//tei:stage[@type='DI']", NS)
    if element is None:
        raise ValueError("Missing implicit stage element.")
    return element


def _raw_lines(title: str, witness_sigla: list[str], raw_block: list[str]) -> list[str]:
    return [title, *[f"  {siglum} : {value}" for siglum, value in zip(witness_sigla, raw_block)]]


def _maybe_code(with_code: bool, title: str, code: str) -> list[str]:
    if not with_code:
        return []
    stripped = textwrap.dedent(code).strip()
    if not stripped:
        return []
    return [
        "",
        title,
        *[f"  {line}" for line in stripped.splitlines()],
        "",
    ]


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _indent(value: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(f"{prefix}{line}" if line else "" for line in value.splitlines())


def _element_xml(element: ET.Element) -> str:
    clone = deepcopy(element)
    for child in clone.iter():
        child.tag = _local_name(child.tag)
    ET.indent(clone, "  ")
    return ET.tostring(clone, encoding="unicode")


def _element_tree_debug(element: ET.Element) -> str:
    dumped = _dump_xml_element(element)
    lines = [
        f"element.tag    = {dumped['tag']!r}",
        f"element.attrib = {dumped['attrib']!r}",
        f"element.text   = {dumped['text']!r}",
        f"element.tail   = {dumped['tail']!r}",
    ]
    for child in dumped["children"]:
        index = child["index"]
        lines.extend(
            [
                f"child[{index}].tag    = {child['tag']!r}",
                f"child[{index}].attrib = {child['attrib']!r}",
                f"child[{index}].text   = {child['text']!r}",
                f"child[{index}].tail   = {child['tail']!r}",
            ]
        )
    lines.extend(["", "Dictionnaire pédagogique :", _json(dumped)])
    return "\n".join(lines)


def _shared_part_label(number: str) -> str | None:
    if "." not in number:
        return None
    _, part = number.split(".", maxsplit=1)
    if part == "1":
        return "fragment initial"
    return "fragment final" if part == "2" else f"fragment {part}"


def _xml_excerpt(root: ET.Element) -> str:
    line = root.find(".//tei:l[tei:app]", NS)
    if line is None:
        return "Aucune ligne avec apparat."
    clone = deepcopy(line)
    for element in clone.iter():
        element.tag = _local_name(element.tag)
    ET.indent(clone, "  ")
    xml = ET.tostring(clone, encoding="unicode")
    return textwrap.shorten(xml.replace("\n", " "), width=420, placeholder=" ...")


def _readings(values: list[str]) -> str:
    return "[" + " | ".join(values) + "]"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _present(value: bool) -> str:
    return "présent" if value else "absent"


def _classification_label(candidate_class: str) -> str:
    labels = {
        "minor_punctuation": "variante de ponctuation mineure",
        "minor_spacing": "variante d'espacement mineure",
        "minor_case": "variante de casse mineure",
        "minor_graphic_safe": "variante graphique mineure",
        "minor_graphic_probable": "variante graphique probable",
        "substantive": "variante substantielle",
        "whole_line_variant": "variante de vers entier",
    }
    return labels.get(candidate_class, candidate_class.replace("_", " "))


if __name__ == "__main__":
    main()
