from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

from ets.site_builder import DramaticTeiMergeError, DramaticTeiMergeRequest, merge_dramatic_tei_acts


ROOT = Path(__file__).resolve().parents[1]
MERGE_FIXTURES = ROOT / "fixtures" / "site_builder" / "merge_dramatic"


def _parse(xml_text: str) -> etree._ElementTree:
    return etree.ElementTree(etree.fromstring(xml_text.encode("utf-8")))


def test_merge_dramatic_tei_acts_merges_in_requested_order() -> None:
    request = DramaticTeiMergeRequest(
        act_xml_paths=(
            MERGE_FIXTURES / "andromaque_act2.xml",
            MERGE_FIXTURES / "andromaque_act1.xml",
        )
    )

    result = merge_dramatic_tei_acts(request)
    tree = _parse(result.merged_xml)

    act_numbers = tree.xpath("//*[local-name()='text']/*[local-name()='body']/*[local-name()='div']/@n")
    assert act_numbers == ["2", "1"]
    assert result.merged_act_count == 2


def test_merge_dramatic_tei_acts_keeps_first_header_and_warns_on_differences() -> None:
    request = DramaticTeiMergeRequest(
        act_xml_paths=(
            MERGE_FIXTURES / "andromaque_act1.xml",
            MERGE_FIXTURES / "andromaque_act2.xml",
        )
    )

    result = merge_dramatic_tei_acts(request)
    tree = _parse(result.merged_xml)

    publication_text = tree.xpath("string((//*[local-name()='teiHeader']//*[local-name()='publicationStmt']//*[local-name()='p'])[1])")
    assert "Acte 1 fixture" in publication_text
    assert any("Header differs" in warning for warning in result.warnings)


def test_merge_dramatic_tei_acts_renames_colliding_xml_ids_and_updates_references() -> None:
    request = DramaticTeiMergeRequest(
        act_xml_paths=(
            MERGE_FIXTURES / "andromaque_act1.xml",
            MERGE_FIXTURES / "andromaque_act2.xml",
        )
    )

    result = merge_dramatic_tei_acts(request)
    tree = _parse(result.merged_xml)

    all_ids = tree.xpath("//*/@xml:id")
    assert len(all_ids) == len(set(all_ids))
    assert "a2_line_1" in all_ids
    target = tree.xpath("string((//*[local-name()='stage']/@target)[1])")
    assert target == "#a2_line_1"


def test_merge_dramatic_tei_acts_fails_on_incompatible_title() -> None:
    request = DramaticTeiMergeRequest(
        act_xml_paths=(
            MERGE_FIXTURES / "andromaque_act1.xml",
            MERGE_FIXTURES / "berenice_act1.xml",
        )
    )

    with pytest.raises(DramaticTeiMergeError, match="title differs"):
        merge_dramatic_tei_acts(request)


def test_merge_dramatic_tei_acts_is_deterministic() -> None:
    request = DramaticTeiMergeRequest(
        act_xml_paths=(
            MERGE_FIXTURES / "andromaque_act1.xml",
            MERGE_FIXTURES / "andromaque_act2.xml",
        )
    )

    first = merge_dramatic_tei_acts(request)
    second = merge_dramatic_tei_acts(request)

    assert first.merged_xml == second.merged_xml
