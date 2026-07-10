from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from ets.collation import collate_parallel_verse
from ets.collation.minor_variants import classify_apparatus, format_ana_rule_code
from ets.core import run_pipeline
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


def test_classifies_simple_minor_feature_combinations_precisely() -> None:
    paix = classify_apparatus("Paix,", ["paix"])
    assert paix.candidate_class == "minor_mixed"
    assert paix.visibility_policy == "hide_safe"
    assert paix.rule_code == "case_only+punctuation_only"

    punctuation = classify_apparatus("m'importe", ["m'importe,"])
    assert punctuation.candidate_class == "minor_punctuation"
    assert punctuation.rule_code == "punctuation_only"

    case = classify_apparatus("Fils", ["fils"])
    assert case.candidate_class == "minor_case"
    assert case.rule_code == "case_only"

    spacing = classify_apparatus("bien-tost", ["bientost"])
    assert spacing.candidate_class == "minor_spacing"
    assert spacing.rule_code == "spacing_or_hyphen_only"

    quoy = classify_apparatus("QUOY ?", ["QUoy ?", "Quoy !"])
    assert quoy.candidate_class == "minor_mixed"
    assert "case_only" in quoy.rule_code.split("+")
    assert "punctuation_only" in quoy.rule_code.split("+")


def test_format_ana_rule_code_uses_tei_pointer_list() -> None:
    assert format_ana_rule_code("case_only+punctuation_only") == "#case_only #punctuation_only"
    assert format_ana_rule_code("#accent+final_zx_s+u_v") == "#accent #final_zx_s #u_v"


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
    assert app.get("ana") == "#punctuation_only"
    assert "+" not in app.get("ana", "")
    taxonomy = root.find(".//tei:taxonomy[@xml:id='ets-variant-taxonomy']", {"tei": TEI_NS, "xml": "http://www.w3.org/XML/1998/namespace"})
    assert taxonomy is not None
    assert taxonomy.find("tei:category[@xml:id='punctuation_only']", {"tei": TEI_NS, "xml": "http://www.w3.org/XML/1998/namespace"}) is not None


def test_generate_tei_serializes_mixed_ana_as_pointer_list() -> None:
    line = collate_parallel_verse(
        ["Paix,", "paix"],
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

    root = ET.fromstring(generate_tei_xml(play, config))
    app = root.find(".//tei:app", NS)

    assert app is not None
    assert app.get("type") == "minor"
    assert app.get("subtype") == "mixed"
    assert app.get("ana") == "#case_only #punctuation_only"
    assert "+" not in app.get("ana", "")


def test_realistic_generated_tei_uses_declared_ana_pointer_lists() -> None:
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "implied_stage_directions" / "berenice"
    root = ET.fromstring(run_pipeline(input_path=fixture / "input.txt", config_path=fixture / "config.json"))

    apps = [app for app in root.findall(".//tei:app", NS) if app.get("ana")]
    assert apps
    declared = {
        category.get(f"{{http://www.w3.org/XML/1998/namespace}}id")
        for category in root.findall(".//tei:taxonomy[@xml:id='ets-variant-taxonomy']/tei:category", {"tei": TEI_NS, "xml": "http://www.w3.org/XML/1998/namespace"})
    }
    assert declared

    for app in apps:
        ana = app.get("ana") or ""
        assert "+" not in ana
        tokens = ana.split()
        assert tokens
        for token in tokens:
            assert token.startswith("#")
            assert token != "#"
            assert token[1:] in declared


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
