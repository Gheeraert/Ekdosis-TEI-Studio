from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from ets.core import run_pipeline_from_text
from ets.domain import Character, EditionConfig, Witness


NS = {"tei": "http://www.tei-c.org/ns/1.0"}
RUNTIME_DIR = Path(__file__).resolve().parents[1] / "tests" / "_runtime" / "tei_character_who"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def _config(characters: list[Character] | None = None, *, castlist_path: str = "") -> EditionConfig:
    return EditionConfig(
        title="Mini",
        author="Auteur",
        editor="Editeur",
        witnesses=[
            Witness(siglum="A", year="1670", description="A"),
            Witness(siglum="B", year="1671", description="B"),
        ],
        reference_witness=0,
        characters=characters or [],
        castlist_path=castlist_path,
    )


def _text(speakers: list[str]) -> str:
    return "\n".join(
        [
            *["####ACTE I####"] * len(speakers),
            "",
            *["###SCENE I###"] * len(speakers),
            "",
            *[f"#{speaker}#" for speaker in speakers],
            "",
            *["Je parle."] * len(speakers),
        ]
    )


def _first_sp(xml_text: str) -> ET.Element:
    root = ET.fromstring(xml_text)
    sp = root.find(".//tei:sp", NS)
    assert sp is not None
    return sp


def _speaker_text(sp: ET.Element) -> str:
    speaker = sp.find("tei:speaker", NS)
    assert speaker is not None
    return "".join(speaker.itertext()).strip()


def _write_castlist(filename: str, *, aliases: str = "NERON|NERON.") -> None:
    (RUNTIME_DIR / filename).write_text(
        "\n".join(
            [
                "%%castlist%%",
                "%%head%%",
                "Acteurs",
                "Acteurs",
                "%%fin_head%%",
                f'%%cast id=neron role="Néron" desc="empereur de Rome" aliases="{aliases}"%%',
                "Néron, empereur de Rome",
                "Néron, empereur de Rome",
                "%%fin_cast%%",
                "%%fin_castlist%%",
            ]
        ),
        encoding="utf-8",
    )


def test_tei_without_declared_characters_keeps_sp_without_who() -> None:
    sp = _first_sp(run_pipeline_from_text(_text(["HERMIONE", "HERMIONE"]), _config()))

    assert "who" not in sp.attrib


def test_tei_known_single_speaker_gets_who() -> None:
    characters = [Character(id="char001", label="Hermione", aliases=["HERMIONE"])]
    sp = _first_sp(run_pipeline_from_text(_text(["HERMIONE", "HERMIONE"]), _config(characters)))

    assert sp.attrib["who"] == "#char001"


def test_tei_castlist_character_authority_sets_who() -> None:
    _write_castlist("castlist_neron.txt")
    xml_text = run_pipeline_from_text(
        _text(["NERON.", "NERON."]),
        _config(castlist_path="castlist_neron.txt"),
        castlist_base_dir=RUNTIME_DIR,
    )
    sp = _first_sp(xml_text)

    assert sp.attrib["who"] == "#neron"


def test_tei_castlist_character_authority_leaves_unresolved_speaker_without_who() -> None:
    _write_castlist("castlist_neron_unresolved.txt")
    xml_text = run_pipeline_from_text(
        _text(["INCONNU", "INCONNU"]),
        _config(castlist_path="castlist_neron_unresolved.txt"),
        castlist_base_dir=RUNTIME_DIR,
    )
    sp = _first_sp(xml_text)

    assert "who" not in sp.attrib


def test_tei_speaker_variants_resolved_to_same_character_get_who() -> None:
    characters = [Character(id="char001", label="Hermione", aliases=["HERMIONNE.", "HERMIONE"])]
    sp = _first_sp(run_pipeline_from_text(_text(["HERMIONNE.", "HERMIONE"]), _config(characters)))

    assert sp.attrib["who"] == "#char001"


def test_tei_unknown_speaker_form_gets_no_who() -> None:
    characters = [Character(id="char001", label="Hermione", aliases=["HERMIONE"])]
    sp = _first_sp(run_pipeline_from_text(_text(["HERMIONE", "INCONNU"]), _config(characters)))

    assert "who" not in sp.attrib


def test_tei_ambiguous_speaker_alias_gets_no_who() -> None:
    characters = [
        Character(id="char001", label="Hermione", aliases=["REINE"]),
        Character(id="char002", label="Andromaque", aliases=["REINE."]),
    ]
    sp = _first_sp(run_pipeline_from_text(_text(["REINE", "REINE"]), _config(characters)))

    assert "who" not in sp.attrib


def test_tei_conflicting_speaker_ids_get_no_who() -> None:
    characters = [
        Character(id="char001", label="Hermione", aliases=["HERMIONE"]),
        Character(id="char002", label="Andromaque", aliases=["ANDROMAQUE"]),
    ]
    sp = _first_sp(run_pipeline_from_text(_text(["HERMIONE", "ANDROMAQUE"]), _config(characters)))

    assert "who" not in sp.attrib


def test_tei_speaker_content_is_not_replaced_by_canonical_label() -> None:
    characters = [Character(id="char001", label="Hermione", aliases=["HERMIONNE."])]
    sp = _first_sp(run_pipeline_from_text(_text(["HERMIONNE.", "HERMIONNE."]), _config(characters)))

    assert sp.attrib["who"] == "#char001"
    assert _speaker_text(sp) == "HERMIONNE."
