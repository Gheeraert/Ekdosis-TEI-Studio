from __future__ import annotations

from ets.application.naming import build_default_basename
from ets.domain import EditionConfig, Witness


def _config(*, act: str, scene: str, title: str = "Britannicus") -> EditionConfig:
    return EditionConfig(
        title=title,
        author="Jean Racine",
        editor="Tony Gheeraert",
        witnesses=[Witness(siglum="A", year="1670", description="A")],
        reference_witness=0,
        start_line_number=1,
        act_number=act,
        scene_number=scene,
    )


def test_build_default_basename_with_scene_count() -> None:
    text = """
####ACTE I####

###SCÈNE 1###

###SCÈNE 2###

###SCÈNE 3###

###SCÈNE 4###
""".strip()
    basename = build_default_basename(text, _config(act="1", scene="1"))
    assert basename == "Britannicus_A1_S1of4"


def test_build_default_basename_without_scene_count_uses_fallback() -> None:
    text = "###SCÈNE 1###"
    basename = build_default_basename(text, _config(act="1", scene="1"))
    assert basename == "Britannicus_A1_S1"


def test_build_default_basename_sanitizes_title() -> None:
    text = """
####ACTE 1####

###SCÈNE 1###
""".strip()
    basename = build_default_basename(text, _config(act="1", scene="1", title="Britannicus : Acte I"))
    assert basename == "Britannicus_Acte_I_A1_S1of1"
