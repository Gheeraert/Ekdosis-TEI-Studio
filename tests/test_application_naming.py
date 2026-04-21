from __future__ import annotations

from ets.application.naming import build_default_basename
from ets.domain import EditionConfig, Witness


def _config(*, title: str = "Britannicus") -> EditionConfig:
    return EditionConfig(
        title=title,
        author="Jean Racine",
        editor="Tony Gheeraert",
        witnesses=[Witness(siglum="A", year="1670", description="A")],
        reference_witness=0,
    )


def test_build_default_basename_uses_title_only() -> None:
    text = """
####ACTE I####

###SCÈNE 1###

###SCÈNE 2###

###SCÈNE 3###

###SCÈNE 4###
""".strip()
    basename = build_default_basename(text, _config())
    assert basename == "Britannicus"


def test_build_default_basename_sanitizes_title() -> None:
    text = """
####ACTE 1####

###SCÈNE 1###
""".strip()
    basename = build_default_basename(text, _config(title="Britannicus : Acte I"))
    assert basename == "Britannicus_Acte_I"
