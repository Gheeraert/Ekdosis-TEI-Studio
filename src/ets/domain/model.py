from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Witness:
    siglum: str
    year: str
    description: str


@dataclass(frozen=True)
class Character:
    id: str
    label: str
    aliases: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EditionConfig:
    title: str
    author: str
    editor: str
    witnesses: list[Witness]
    reference_witness: int
    transcriber: str = ""
    characters: list[Character] = field(default_factory=list)
    transcription_path: str = ""
    castlist_path: str = ""
    # Identifiant court et stable de la pièce (xml:id de <text>). S'il est
    # vide, il est dérivé du titre par slugification à la génération TEI.
    play_id: str = ""


@dataclass
class VerseLine:
    number: str
    readings: list[str]
    block_index: int
    whole_line_variant: bool = False
    met: str | None = None


@dataclass
class StageDirection:
    readings: list[str]
    block_index: int


@dataclass
class ImplicitStageSpan:
    category: str
    block_index_open: int
    lines: list[VerseLine] = field(default_factory=list)


@dataclass
class Stanza:
    subtype: str | None
    rhyme: str | None
    block_index_open: int
    lines: list[VerseLine] = field(default_factory=list)


SpeechElement = VerseLine | StageDirection | ImplicitStageSpan | Stanza


@dataclass
class Speech:
    speaker_readings: list[str]
    speaker_block_index: int
    elements: list[SpeechElement] = field(default_factory=list)

    @property
    def verses(self) -> list[VerseLine]:
        verses: list[VerseLine] = []
        for element in self.elements:
            if isinstance(element, VerseLine):
                verses.append(element)
            elif isinstance(element, ImplicitStageSpan):
                verses.extend(element.lines)
            elif isinstance(element, Stanza):
                verses.extend(element.lines)
        return verses

    @property
    def stage_directions(self) -> list[StageDirection]:
        return [element for element in self.elements if isinstance(element, StageDirection)]


@dataclass
class Scene:
    head_readings: list[str]
    head_block_index: int
    cast_readings: list[str]
    cast_block_index: int | None = None
    speeches: list[Speech] = field(default_factory=list)
    stage_directions: list[StageDirection] = field(default_factory=list)


@dataclass
class Act:
    head_readings: list[str]
    head_block_index: int
    scenes: list[Scene] = field(default_factory=list)
    kind: str = "act"


@dataclass
class Play:
    acts: list[Act] = field(default_factory=list)


@dataclass(frozen=True)
class CastEntry:
    id: str
    role: str
    desc: str = ""
    aliases: list[str] = field(default_factory=list)
    readings: list[str] = field(default_factory=list)
    block_index: int | None = None
    line_number: int | None = None


@dataclass(frozen=True)
class DramatisPersonae:
    head_readings: list[str] = field(default_factory=list)
    entries: list[CastEntry] = field(default_factory=list)
    setting_readings: list[str] = field(default_factory=list)


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
    candidate_class: str = "substantive"
    visibility_policy: str = "visible"
    rule_code: str = "substantive_default"


CollatedTokenSegment = LiteralTokenSegment | ApparatusTokenSegment


@dataclass(frozen=True)
class CollatedText:
    segments: list[CollatedTokenSegment]


@dataclass(frozen=True)
class TokenCollatedLine:
    number: str
    text: CollatedText
    met: str | None = None


@dataclass(frozen=True)
class ApparatusLine:
    number: str
    lemma: CollatedReading
    readings: list[CollatedReading]


CollatedLine = TokenCollatedLine | ApparatusLine | LiteralLine


@dataclass(frozen=True)
class CollatedStanza:
    subtype: str | None
    rhyme: str | None
    lines: list[CollatedLine]


@dataclass
class CollatedSpeech:
    speaker: CollatedText
    speaker_readings: list[str] = field(default_factory=list)
    elements: list[
        CollatedLine | "CollatedStageDirection" | "CollatedImplicitStageSpan" | CollatedStanza
    ] = field(default_factory=list)

    @property
    def lines(self) -> list[CollatedLine]:
        return [element for element in self.elements if isinstance(element, (TokenCollatedLine, ApparatusLine, LiteralLine))]


@dataclass(frozen=True)
class CollatedStageDirection:
    text: CollatedText


@dataclass(frozen=True)
class CollatedImplicitStageSpan:
    category: str
    lines: list[CollatedLine]


@dataclass
class CollatedScene:
    head: CollatedText
    cast: CollatedText | None = None
    stage_directions: list["CollatedStageDirection"] = field(default_factory=list)
    speeches: list[CollatedSpeech] = field(default_factory=list)


@dataclass
class CollatedAct:
    head: CollatedText
    scenes: list[CollatedScene] = field(default_factory=list)
    kind: str = "act"


@dataclass
class CollatedPlay:
    acts: list[CollatedAct] = field(default_factory=list)
