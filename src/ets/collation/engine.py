from __future__ import annotations

from collections import defaultdict

from ets.collation.tokenizer import tokenize_editorial_text
from ets.domain import (
    ApparatusLine,
    ApparatusTokenSegment,
    CollatedAct,
    CollatedLine,
    CollatedPlay,
    CollatedReading,
    CollatedScene,
    CollatedSpeech,
    CollatedStageDirection,
    LiteralLine,
    LiteralTokenSegment,
    Play,
    StageDirection,
    TokenCollatedLine,
    VerseLine,
)


def _group_readings(readings: list[str], sigla: list[str]) -> list[CollatedReading]:
    grouped: dict[str, list[str]] = {}
    order: list[str] = []
    for text, siglum in zip(readings, sigla):
        if text not in grouped:
            grouped[text] = []
            order.append(text)
        grouped[text].append(siglum)
    return [CollatedReading(text=text, witness_sigla=grouped[text]) for text in order]


def validate_token_matrix(
    token_matrix: list[list[str]],
    witness_sigla: list[str],
    act_label: str,
    scene_label: str,
    speaker_label: str | None,
    block_index: int,
    allow_unbalanced: bool = False,
) -> None:
    lengths = [len(tokens) for tokens in token_matrix]
    if not lengths:
        raise ValueError("Empty token matrix.")
    if allow_unbalanced:
        return
    if len(set(lengths)) != 1:
        speaker_part = speaker_label if speaker_label else "N/A"
        counts = ", ".join(f"{siglum}:{length}" for siglum, length in zip(witness_sigla, lengths))
        raise ValueError(
            "Token count mismatch "
            f"(act={act_label}, scene={scene_label}, speaker={speaker_part}, block={block_index}, counts=[{counts}])."
        )


def align_variants_by_token(
    token_matrix: list[list[str]], witness_sigla: list[str], ref_index: int
) -> list[tuple[CollatedReading, list[CollatedReading], bool]]:
    max_len = max(len(tokens) for tokens in token_matrix)
    aligned: list[tuple[CollatedReading, list[CollatedReading], bool]] = []
    for i in range(max_len):
        mots_colonne: defaultdict[str, list[str]] = defaultdict(list)
        order: list[str] = []
        for j, line in enumerate(token_matrix):
            token = line[i] if i < len(line) else ""
            if token not in mots_colonne:
                order.append(token)
            mots_colonne[token].append(witness_sigla[j])

        lemma_token = token_matrix[ref_index][i] if i < len(token_matrix[ref_index]) else ""
        non_empty_order = [token for token in order if token != ""]

        if lemma_token == "":
            if not non_empty_order:
                continue
            lemma_token = non_empty_order[0]

        lemma = CollatedReading(text=lemma_token, witness_sigla=mots_colonne[lemma_token])
        readings = [
            CollatedReading(text=token, witness_sigla=mots_colonne[token])
            for token in non_empty_order
            if token != lemma_token
        ]
        is_literal = len(non_empty_order) == 1
        aligned.append((lemma, readings, is_literal))
    return aligned


def build_apparatus_from_alignment(
    number: str, alignment: list[tuple[CollatedReading, list[CollatedReading], bool]]
) -> TokenCollatedLine:
    segments: list[LiteralTokenSegment | ApparatusTokenSegment] = []
    for index, (lemma, readings, is_literal) in enumerate(alignment):
        suffix = " " if index < len(alignment) - 1 else ""
        if is_literal:
            segments.append(LiteralTokenSegment(text=lemma.text + suffix))
        else:
            segments.append(
                ApparatusTokenSegment(
                    lemma=CollatedReading(text=lemma.text + suffix, witness_sigla=lemma.witness_sigla),
                    readings=[
                        CollatedReading(text=reading.text + suffix, witness_sigla=reading.witness_sigla)
                        for reading in readings
                    ],
                )
            )
    return TokenCollatedLine(number=number, segments=segments)


def collate_parallel_verse(
    readings: list[str],
    witness_sigla: list[str],
    ref_index: int,
    number: str,
    whole_line_variant: bool,
    act_label: str,
    scene_label: str,
    speaker_label: str | None,
    block_index: int,
) -> CollatedLine:
    if whole_line_variant:
        grouped = _group_readings(readings, witness_sigla)
        if len(grouped) == 1:
            return LiteralLine(number=number, text=grouped[0].text)
        lemma_text = readings[ref_index]
        lemma = next(item for item in grouped if item.text == lemma_text)
        rdgs = [item for item in grouped if item.text != lemma_text]
        return ApparatusLine(number=number, lemma=lemma, readings=rdgs)

    token_matrix = [tokenize_editorial_text(text) for text in readings]
    validate_token_matrix(
        token_matrix=token_matrix,
        witness_sigla=witness_sigla,
        act_label=act_label,
        scene_label=scene_label,
        speaker_label=speaker_label,
        block_index=block_index,
        allow_unbalanced=False,
    )
    alignment = align_variants_by_token(token_matrix, witness_sigla, ref_index)
    return build_apparatus_from_alignment(number=number, alignment=alignment)


def collate_play(play: Play, witness_sigla: list[str], reference_witness: int) -> CollatedPlay:
    collated = CollatedPlay()
    for act_index, act in enumerate(play.acts, start=1):
        act_label = str(act_index)
        act_head = _group_readings(act.head_readings, witness_sigla)
        collated_act = CollatedAct(head_readings=act_head, reference_head=act.head_readings[reference_witness])
        collated.acts.append(collated_act)

        for scene_index, scene in enumerate(act.scenes, start=1):
            scene_label = str(scene_index)
            collated_scene = CollatedScene(
                head=scene.head_readings[reference_witness],
                cast=scene.cast_readings[reference_witness] if scene.cast_readings else "",
            )
            collated_act.scenes.append(collated_scene)

            for scene_stage in scene.stage_directions:
                collated_scene.stage_directions.append(
                    CollatedStageDirection(text=scene_stage.readings[reference_witness])
                )

            for speech in scene.speeches:
                collated_speech = CollatedSpeech(speaker=speech.speaker_readings[reference_witness])
                collated_scene.speeches.append(collated_speech)
                for element in speech.elements:
                    if isinstance(element, StageDirection):
                        collated_speech.elements.append(
                            CollatedStageDirection(text=element.readings[reference_witness])
                        )
                        continue
                    if not isinstance(element, VerseLine):
                        raise TypeError(f"Unsupported speech element type: {type(element)!r}")
                    collated_speech.elements.append(
                        collate_parallel_verse(
                            readings=element.readings,
                            witness_sigla=witness_sigla,
                            ref_index=reference_witness,
                            number=element.number,
                            whole_line_variant=element.whole_line_variant,
                            act_label=act_label,
                            scene_label=scene_label,
                            speaker_label=collated_speech.speaker,
                            block_index=element.block_index,
                        )
                    )
    return collated
