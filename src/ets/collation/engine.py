from __future__ import annotations

from collections import defaultdict

from ets.collation.tokenizer import tokenize_parallel_readings
from ets.domain import (
    ApparatusTokenSegment,
    CollatedAct,
    CollatedImplicitStageSpan,
    CollatedLine,
    CollatedPlay,
    CollatedReading,
    CollatedScene,
    CollatedSpeech,
    CollatedStageDirection,
    CollatedText,
    ImplicitStageSpan,
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
        tokens_by_column: defaultdict[str, list[str]] = defaultdict(list)
        order: list[str] = []
        for j, line in enumerate(token_matrix):
            token = line[i] if i < len(line) else ""
            if token not in tokens_by_column:
                order.append(token)
            tokens_by_column[token].append(witness_sigla[j])

        lemma_token = token_matrix[ref_index][i] if i < len(token_matrix[ref_index]) else ""
        non_empty_order = [token for token in order if token != ""]
        if lemma_token == "":
            if not non_empty_order:
                continue
            lemma_token = non_empty_order[0]

        lemma = CollatedReading(text=lemma_token, witness_sigla=tokens_by_column[lemma_token])
        readings = [
            CollatedReading(text=token, witness_sigla=tokens_by_column[token])
            for token in non_empty_order
            if token != lemma_token
        ]
        is_literal = len(non_empty_order) == 1
        aligned.append((lemma, readings, is_literal))
    return aligned


def build_apparatus_from_alignment(alignment: list[tuple[CollatedReading, list[CollatedReading], bool]]) -> CollatedText:
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
    return CollatedText(segments=segments)


def collate_parallel_text(
    readings: list[str],
    witness_sigla: list[str],
    ref_index: int,
    *,
    whole_line_variant: bool = False,
    strict_validation: bool = False,
    act_label: str = "N/A",
    scene_label: str = "N/A",
    speaker_label: str | None = None,
    block_index: int = -1,
) -> CollatedText:
    if whole_line_variant:
        grouped = _group_readings(readings, witness_sigla)
        if len(grouped) == 1:
            return CollatedText(segments=[LiteralTokenSegment(text=grouped[0].text)])
        lemma_text = readings[ref_index]
        lemma = next(item for item in grouped if item.text == lemma_text)
        rdgs = [item for item in grouped if item.text != lemma_text]
        return CollatedText(segments=[ApparatusTokenSegment(lemma=lemma, readings=rdgs)])

    token_matrix = tokenize_parallel_readings(readings)
    validate_token_matrix(
        token_matrix=token_matrix,
        witness_sigla=witness_sigla,
        act_label=act_label,
        scene_label=scene_label,
        speaker_label=speaker_label,
        block_index=block_index,
        allow_unbalanced=not strict_validation,
    )
    alignment = align_variants_by_token(token_matrix, witness_sigla, ref_index)
    return build_apparatus_from_alignment(alignment=alignment)


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
    return TokenCollatedLine(
        number=number,
        text=collate_parallel_text(
            readings=readings,
            witness_sigla=witness_sigla,
            ref_index=ref_index,
            whole_line_variant=whole_line_variant,
            strict_validation=not whole_line_variant,
            act_label=act_label,
            scene_label=scene_label,
            speaker_label=speaker_label,
            block_index=block_index,
        ),
    )


def collate_play(play: Play, witness_sigla: list[str], reference_witness: int) -> CollatedPlay:
    collated = CollatedPlay()
    for act_index, act in enumerate(play.acts, start=1):
        act_label = str(act_index)
        collated_act = CollatedAct(
            head=collate_parallel_text(
                readings=act.head_readings,
                witness_sigla=witness_sigla,
                ref_index=reference_witness,
                strict_validation=True,
                act_label=act_label,
                scene_label="N/A",
                speaker_label=None,
                block_index=act.head_block_index,
            )
        )
        collated.acts.append(collated_act)

        for scene_index, scene in enumerate(act.scenes, start=1):
            scene_label = str(scene_index)
            collated_scene = CollatedScene(
                head=collate_parallel_text(
                    readings=scene.head_readings,
                    witness_sigla=witness_sigla,
                    ref_index=reference_witness,
                    strict_validation=True,
                    act_label=act_label,
                    scene_label=scene_label,
                    speaker_label=None,
                    block_index=scene.head_block_index,
                ),
                cast=collate_parallel_text(
                    readings=scene.cast_readings,
                    witness_sigla=witness_sigla,
                    ref_index=reference_witness,
                    strict_validation=True,
                    act_label=act_label,
                    scene_label=scene_label,
                    speaker_label=None,
                    block_index=scene.cast_block_index if scene.cast_block_index is not None else -1,
                )
                if scene.cast_readings
                else None,
            )
            collated_act.scenes.append(collated_scene)

            for scene_stage in scene.stage_directions:
                collated_scene.stage_directions.append(
                    CollatedStageDirection(
                        text=collate_parallel_text(
                            readings=scene_stage.readings,
                            witness_sigla=witness_sigla,
                            ref_index=reference_witness,
                            strict_validation=True,
                            act_label=act_label,
                            scene_label=scene_label,
                            speaker_label=None,
                            block_index=scene_stage.block_index,
                        )
                    )
                )

            for speech in scene.speeches:
                collated_speech = CollatedSpeech(
                    speaker=collate_parallel_text(
                        readings=speech.speaker_readings,
                        witness_sigla=witness_sigla,
                        ref_index=reference_witness,
                        strict_validation=True,
                        act_label=act_label,
                        scene_label=scene_label,
                        speaker_label=None,
                        block_index=speech.speaker_block_index,
                    )
                )
                collated_scene.speeches.append(collated_speech)
                for element in speech.elements:
                    if isinstance(element, StageDirection):
                        collated_speech.elements.append(
                            CollatedStageDirection(
                                text=collate_parallel_text(
                                    readings=element.readings,
                                    witness_sigla=witness_sigla,
                                    ref_index=reference_witness,
                                    strict_validation=True,
                                    act_label=act_label,
                                    scene_label=scene_label,
                                    speaker_label=speech.speaker_readings[reference_witness],
                                    block_index=element.block_index,
                                )
                            )
                        )
                        continue
                    if isinstance(element, ImplicitStageSpan):
                        span_lines: list[CollatedLine] = []
                        for verse in element.lines:
                            span_lines.append(
                                collate_parallel_verse(
                                    readings=verse.readings,
                                    witness_sigla=witness_sigla,
                                    ref_index=reference_witness,
                                    number=verse.number,
                                    whole_line_variant=verse.whole_line_variant,
                                    act_label=act_label,
                                    scene_label=scene_label,
                                    speaker_label=speech.speaker_readings[reference_witness],
                                    block_index=verse.block_index,
                                )
                            )
                        collated_speech.elements.append(
                            CollatedImplicitStageSpan(
                                category=element.category,
                                lines=span_lines,
                            )
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
                            speaker_label=speech.speaker_readings[reference_witness],
                            block_index=element.block_index,
                        )
                    )
    return collated
