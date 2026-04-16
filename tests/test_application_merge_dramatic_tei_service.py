from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from ets.application import (
    DramaticTeiMergeRequest,
    DramaticTeiMergeService,
    merge_dramatic_tei_files,
)


ROOT = Path(__file__).resolve().parents[1]
MERGE_FIXTURES = ROOT / "fixtures" / "site_builder" / "merge_dramatic"
RUNTIME_ROOT = ROOT / "tests" / "_runtime"


def _runtime_dir(prefix: str) -> Path:
    target = RUNTIME_ROOT / f"{prefix}_{uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_merge_dramatic_tei_service_writes_output_and_reports_counts() -> None:
    base = _runtime_dir("app_dramatic_tei_merge")
    output_path = base / "andromaque_merged.xml"
    request = DramaticTeiMergeRequest(
        act_xml_paths=(
            MERGE_FIXTURES / "andromaque_act1.xml",
            MERGE_FIXTURES / "andromaque_act2.xml",
        ),
        output_path=output_path,
    )

    service = DramaticTeiMergeService()
    result = service.merge(request)

    assert result.ok is True
    assert result.merged_act_count == 2
    assert result.output_path == output_path.resolve()
    assert output_path.exists()
    assert result.merged_xml is not None
    assert "<TEI" in result.merged_xml


def test_merge_dramatic_tei_service_fails_cleanly_on_incompatible_inputs() -> None:
    result = merge_dramatic_tei_files(
        DramaticTeiMergeRequest(
            act_xml_paths=(
                MERGE_FIXTURES / "andromaque_act1.xml",
                MERGE_FIXTURES / "berenice_act1.xml",
            )
        )
    )

    assert result.ok is False
    assert result.error_code == "E_DRAMATIC_TEI_MERGE"
    assert result.error_detail is not None
    assert "title differs" in result.error_detail
