from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Witness:
    siglum: str
    year: str
    description: str


@dataclass(frozen=True)
class EditionConfig:
    title: str
    author: str
    editor: str
    witnesses: list[Witness]
    reference_witness: int
    start_line_number: int
    act_number: str
    scene_number: str


@dataclass
class VerseLine:
    number: str
    readings: list[str]
    block_index: int
    whole_line_variant: bool = False


@dataclass
class StageDirection:
    readings: list[str]
    block_index: int


SpeechElement = VerseLine | StageDirection


@dataclass
class Speech:
    speaker_readings: list[str]
    elements: list[SpeechElement] = field(default_factory=list)

    @property
    def verses(self) -> list[VerseLine]:
        return [element for element in self.elements if isinstance(element, VerseLine)]

    @property
    def stage_directions(self) -> list[StageDirection]:
        return [element for element in self.elements if isinstance(element, StageDirection)]


@dataclass
class Scene:
    head_readings: list[str]
    cast_readings: list[str]
    speeches: list[Speech] = field(default_factory=list)
    stage_directions: list[StageDirection] = field(default_factory=list)


@dataclass
class Act:
    head_readings: list[str]
    scenes: list[Scene] = field(default_factory=list)


@dataclass
class Play:
    acts: list[Act] = field(default_factory=list)


@dataclass(frozen=True)
class CollatedReading:
    text: str
    witness_sigla: list[str]


@dataclass(frozen=True)
class LiteralLine:
    number: str
    text: str


@dataclass(frozen=True)
class LiteralTokenSegment:
    text: str


@dataclass(frozen=True)
class ApparatusTokenSegment:
    lemma: CollatedReading
    readings: list[CollatedReading]


CollatedTokenSegment = LiteralTokenSegment | ApparatusTokenSegment


@dataclass(frozen=True)
class TokenCollatedLine:
    number: str
    segments: list[CollatedTokenSegment]


@dataclass(frozen=True)
class ApparatusLine:
    number: str
    lemma: CollatedReading
    readings: list[CollatedReading]


CollatedLine = TokenCollatedLine | ApparatusLine | LiteralLine


@dataclass
class CollatedSpeech:
    speaker: str
    elements: list[CollatedLine | "CollatedStageDirection"] = field(default_factory=list)

    @property
    def lines(self) -> list[CollatedLine]:
        return [element for element in self.elements if not isinstance(element, CollatedStageDirection)]


@dataclass(frozen=True)
class CollatedStageDirection:
    text: str


@dataclass
class CollatedScene:
    head: str
    cast: str
    stage_directions: list["CollatedStageDirection"] = field(default_factory=list)
    speeches: list[CollatedSpeech] = field(default_factory=list)


@dataclass
class CollatedAct:
    head_readings: list[CollatedReading]
    reference_head: str
    scenes: list[CollatedScene] = field(default_factory=list)


@dataclass
class CollatedPlay:
    acts: list[CollatedAct] = field(default_factory=list)
