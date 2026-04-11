from __future__ import annotations

import pytest

from ets.collation import collate_parallel_verse
from ets.domain import ApparatusLine, ApparatusTokenSegment, TokenCollatedLine


def test_collation_is_token_based_not_whole_line_based() -> None:
    readings = [
        "OUY, puis\u00A0que je retrouve un Amy si fidelle,",
        "OVY, puis\u00A0que ie retrouue vn Amy si fidelle,",
        "OUY, puis\u00A0que je retrouve un Amy si fidelle,",
    ]
    line = collate_parallel_verse(
        readings,
        ["F", "A", "C"],
        ref_index=0,
        number="1",
        whole_line_variant=False,
        act_label="1",
        scene_label="1",
        speaker_label="ORESTE.",
        block_index=10,
    )
    assert isinstance(line, TokenCollatedLine)

    apps = [segment for segment in line.segments if isinstance(segment, ApparatusTokenSegment)]
    assert len(apps) >= 3
    assert apps[0].lemma.text.strip() == "OUY,"
    assert any(rdg.text.strip() == "OVY," for rdg in apps[0].readings)


def test_whole_line_marker_uses_explicit_whole_line_apparatus() -> None:
    readings = [
        "#Ses attraits offensez, & ses yeux sans pouvoir.",
        "#Ses attraits offensez, & ses yeux sans pouuoir.",
        "#Son hymen differé, ses charmes sans pouvoir.",
    ]
    line = collate_parallel_verse(
        readings,
        ["F", "A", "C"],
        ref_index=0,
        number="124",
        whole_line_variant=True,
        act_label="1",
        scene_label="1",
        speaker_label="ORESTE.",
        block_index=124,
    )
    assert isinstance(line, ApparatusLine)
    assert line.lemma.text.startswith("#Ses attraits")
    assert len(line.readings) == 2


def test_collation_rejects_token_spread_when_not_special() -> None:
    readings = ["A B C D E F", "A", "A B C D E F G H I J K"]
    with pytest.raises(ValueError, match=r"act=1, scene=1, speaker=ORESTE., block=88"):
        collate_parallel_verse(
            readings,
            ["A", "B", "C"],
            ref_index=0,
            number="10",
            whole_line_variant=False,
            act_label="1",
            scene_label="1",
            speaker_label="ORESTE.",
            block_index=88,
        )
