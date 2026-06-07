from __future__ import annotations

from xml.etree import ElementTree as ET

from ets.collation import collate_parallel_verse
from ets.collation.minor_variants import classify_apparatus
from ets.domain import (
    ApparatusTokenSegment,
    CollatedAct,
    CollatedPlay,
    CollatedScene,
    CollatedSpeech,
    CollatedText,
    EditionConfig,
    TokenCollatedLine,
    Witness,
)
from ets.latex import tei_to_ekdosis
from ets.tei.generator import generate_tei_xml

TEI_NS = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI_NS}


def _first_app(line: TokenCollatedLine) -> ApparatusTokenSegment:
    apps = [segment for segment in line.text.segments if isinstance(segment, ApparatusTokenSegment)]
    assert apps
    return apps[0]


def test_classifies_punctuation_as_hide_safe_minor() -> None:
    classification = classify_apparatus("pleurs,", ["pleurs~!"])

    assert classification.candidate_class == "minor_punctuation"
    assert classification.visibility_policy == "hide_safe"


def test_classifies_historic_graphic_variants_as_hide_safe_minor() -> None:
    classification = classify_apparatus("QU’attendez-vous", ["Qv’attendez-vous", "QU’attendés-vous"])

    assert classification.candidate_class == "minor_graphic_safe"
    assert classification.visibility_policy == "hide_safe"


def test_classifies_substantive_variants_as_visible() -> None:
    classification = classify_apparatus("leur", ["mes"])

    assert classification.candidate_class == "substantive"
    assert classification.visibility_policy == "visible"


def test_collation_stores_minor_variant_metadata_on_segments() -> None:
    line = collate_parallel_verse(
        ["Ah mortelles douleurs~!", "Ah mortelles douleurs,"],
        ["A", "B"],
        ref_index=0,
        number="1",
        whole_line_variant=False,
        act_label="1",
        scene_label="1",
        speaker_label="IOCASTE",
        block_index=1,
    )
    assert isinstance(line, TokenCollatedLine)

    app = _first_app(line)
    assert app.candidate_class == "minor_punctuation"
    assert app.visibility_policy == "hide_safe"


def test_generate_tei_marks_hide_safe_minor_apps() -> None:
    line = collate_parallel_verse(
        ["Ah mortelles douleurs~!", "Ah mortelles douleurs,"],
        ["A", "B"],
        ref_index=0,
        number="1",
        whole_line_variant=False,
        act_label="1",
        scene_label="1",
        speaker_label="IOCASTE",
        block_index=1,
    )
    play = CollatedPlay(
        acts=[
            CollatedAct(
                head=CollatedText(segments=[]),
                scenes=[
                    CollatedScene(
                        head=CollatedText(segments=[]),
                        speeches=[CollatedSpeech(speaker=CollatedText(segments=[]), elements=[line])],
                    )
                ],
            )
        ]
    )
    config = EditionConfig(
        title="Test",
        author="Auteur",
        editor="",
        witnesses=[Witness("A", "", ""), Witness("B", "", "")],
        reference_witness=0,
    )

    xml = generate_tei_xml(play, config)
    root = ET.fromstring(xml)
    app = root.find(".//tei:app", NS)
    assert app is not None
    assert app.get("type") == "minor"
    assert app.get("subtype") == "punctuation"


def test_ekdosis_can_hide_minor_apparatus_when_requested() -> None:
    xml = """<?xml version="1.0" encoding="utf-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <div type="act" n="1">
        <div type="scene" n="1">
          <sp>
            <speaker>IOCASTE</speaker>
            <l n="1">Ah mortelles <app type="minor" subtype="punctuation"><lem wit="#A">douleurs~! </lem><rdg wit="#B">douleurs, </rdg></app></l>
          </sp>
        </div>
      </div>
    </body>
  </text>
</TEI>
"""

    full = tei_to_ekdosis(xml)
    readable = tei_to_ekdosis(xml, apparatus_policy="hide_minor")

    assert "\\app{" in full
    assert "\\app{" not in readable
    assert "Ah mortelles douleurs" in readable



def test_ekdosis_keeps_inspect_minor_apparatus_visible() -> None:
    xml = """<?xml version="1.0" encoding="utf-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <div type="act" n="1">
        <div type="scene" n="1">
          <sp>
            <speaker>IOCASTE</speaker>
            <l n="1">Ah <app type="minor" subtype="graphic-probable" cert="low"><lem wit="#A">touchoient </lem><rdg wit="#B">touchoiet </rdg></app></l>
          </sp>
        </div>
      </div>
    </body>
  </text>
</TEI>
"""

    readable = tei_to_ekdosis(xml, apparatus_policy="hide_minor")

    assert "\\app{" in readable


def test_classifies_common_classical_spellings_from_pdf_as_hide_safe_minor() -> None:
    examples = [
        ("vostre", ["vôtre"]),
        ("plûtost", ["plûtôt"]),
        ("presté", ["prêté"]),
        ("peut-estre.", ["peut-être."]),
        ("Maistres,", ["Maîtres,"]),
        ("reconnoistre", ["reconnoître"]),
        ("connoissance", ["connaissance"]),
        ("traisnée.", ["traînée."]),
        ("d’experiance", ["d’experience"]),
        ("audiance.", ["audience."]),
        ("d’Estat ?", ["d’Etat ?"]),
        ("eust", ["eût"]),
    ]

    for lemma, readings in examples:
        classification = classify_apparatus(lemma, readings)
        assert classification.candidate_class == "minor_graphic_safe", (lemma, readings, classification)
        assert classification.visibility_policy == "hide_safe", (lemma, readings, classification)
