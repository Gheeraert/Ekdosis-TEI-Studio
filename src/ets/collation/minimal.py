from __future__ import annotations

from collections import OrderedDict

from ets.domain import (
    ApparatusLine,
    CollatedAct,
    CollatedLine,
    CollatedPlay,
    CollatedReading,
    CollatedScene,
    CollatedSpeech,
    LiteralLine,
    Play,
)


def _group_readings(readings: list[str], sigla: list[str]) -> list[CollatedReading]:
    grouped: OrderedDict[str, list[str]] = OrderedDict()
    for text, siglum in zip(readings, sigla):
        grouped.setdefault(text, []).append(siglum)
    return [CollatedReading(text=text, witness_sigla=wits) for text, wits in grouped.items()]


def _collate_line(readings: list[str], sigla: list[str], ref_index: int, number: str) -> CollatedLine:
    grouped = _group_readings(readings, sigla)
    if len(grouped) == 1:
        return LiteralLine(number=number, text=grouped[0].text)

    lemma_text = readings[ref_index]
    lemma_group = next(item for item in grouped if item.text == lemma_text)
    rdg_groups = [item for item in grouped if item.text != lemma_text]
    return ApparatusLine(number=number, lemma=lemma_group, readings=rdg_groups)


def collate_play(play: Play, witness_sigla: list[str], reference_witness: int) -> CollatedPlay:
    collated = CollatedPlay()
    for act in play.acts:
        act_head = _group_readings(act.head_readings, witness_sigla)
        collated_act = CollatedAct(head_readings=act_head, reference_head=act.head_readings[reference_witness])
        collated.acts.append(collated_act)

        for scene in act.scenes:
            collated_scene = CollatedScene(
                head=scene.head_readings[reference_witness],
                cast=scene.cast_readings[reference_witness] if scene.cast_readings else "",
            )
            collated_act.scenes.append(collated_scene)

            for speech in scene.speeches:
                collated_speech = CollatedSpeech(speaker=speech.speaker_readings[reference_witness])
                collated_scene.speeches.append(collated_speech)
                for verse in speech.verses:
                    collated_line = _collate_line(
                        readings=verse.readings,
                        sigla=witness_sigla,
                        ref_index=reference_witness,
                        number=verse.number,
                    )
                    collated_speech.lines.append(collated_line)
    return collated
