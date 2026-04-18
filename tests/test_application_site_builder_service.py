from __future__ import annotations

import json
import shutil
from pathlib import Path
from uuid import uuid4

from lxml import etree

from ets.application import (
    DramaticDocumentInput,
    DramaticPlayInput,
    NoticeInput,
    SiteAssetsInput,
    SiteBuildRequest,
    SiteBuilderService,
    SiteHomepageSectionInput,
    SiteIdentityInput,
    SitePublicationRequest,
    build_site_from_config_dict,
    build_site_from_config_file,
    build_site_from_publication_request,
)


ROOT = Path(__file__).resolve().parents[1]
DRAMATIC_FIXTURES = ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic"
DRAMATIC_MERGE_FIXTURES = ROOT / "fixtures" / "site_builder" / "merge_dramatic"
MINIMAL_NOTICES = ROOT / "fixtures" / "site_builder" / "minimal" / "notices"
REALISTIC_NOTICES = ROOT / "fixtures" / "metopes" / "realistic"
RUNTIME_ROOT = ROOT / "tests" / "_runtime"


def _runtime_dir(prefix: str) -> Path:
    target = RUNTIME_ROOT / f"{prefix}_{uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_site_builder_service_build_from_config_dict_success() -> None:
    base = _runtime_dir("app_site_builder_service_dict")
    output_dir = base / "site"

    result = build_site_from_config_dict(
        {
            "site_title": "ETS Service Build",
            "dramatic_xml_dir": str(DRAMATIC_FIXTURES),
            "notice_xml_dir": str(REALISTIC_NOTICES),
            "output_dir": str(output_dir),
            "publish_notices": True,
            "show_xml_download": True,
            "play_notice_map": {"andromaque": "introduction"},
        }
    )

    assert result.ok is True
    assert result.output_dir == output_dir.resolve()
    assert result.play_count == 2
    assert result.notice_count == 2
    assert "index.html" in result.generated_page_relpaths
    assert "plays/andromaque.html" in result.generated_page_relpaths
    assert "notices/introduction.html" in result.generated_page_relpaths
    assert (output_dir / "xml" / "notices" / "introduction.xml").exists()


def test_site_builder_service_build_from_config_file_success_and_deterministic_paths() -> None:
    base = _runtime_dir("app_site_builder_service_file")
    output_dir = base / "site"
    config_path = base / "site_config.json"
    config_path.write_text(
        json.dumps(
            {
                "site_title": "ETS Service File Build",
                "dramatic_xml_dir": str(DRAMATIC_FIXTURES),
                "notice_xml_dir": str(MINIMAL_NOTICES),
                "output_dir": str(output_dir),
                "publish_notices": True,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    result = build_site_from_config_file(config_path)

    assert result.ok is True
    assert result.generated_page_relpaths == (
        "index.html",
        "plays/andromaque.html",
        "plays/berenice.html",
        "notices/andromaque-notice.html",
    )


def test_site_builder_service_propagates_non_blocking_warnings() -> None:
    base = _runtime_dir("app_site_builder_service_warn")
    output_dir = base / "site"
    service = SiteBuilderService()

    result = service.build(
        SiteBuildRequest(
            source={
                "site_title": "ETS Service Warning Build",
                "dramatic_xml_dir": str(DRAMATIC_FIXTURES),
                "notice_xml_dir": str(MINIMAL_NOTICES),
                "output_dir": str(output_dir),
                "publish_notices": True,
                "play_notice_map": {"unknown-play": "andromaque-notice"},
            }
        )
    )

    assert result.ok is True
    assert any("unknown play slug" in warning for warning in result.warnings)
    assert (output_dir / "index.html").exists()


def test_site_builder_service_fails_cleanly_on_invalid_config() -> None:
    result = build_site_from_config_dict(
        {
            "site_title": "   ",
            "dramatic_xml_dir": str(DRAMATIC_FIXTURES),
            "output_dir": str(ROOT / "tests" / "_runtime" / "unused"),
        }
    )

    assert result.ok is False
    assert result.error_code == "E_SITE_CONFIG"
    assert result.error_detail is not None
    assert "site_title" in result.error_detail


def test_site_builder_service_build_from_publication_request_supports_grouping_order_and_assets() -> None:
    base = _runtime_dir("app_site_builder_service_publication_request")
    output_dir = base / "site"
    dramatic_pool = base / "dramatic_pool"
    dramatic_pool.mkdir(parents=True, exist_ok=True)
    andromaque_a1 = dramatic_pool / "andromaque_A1.xml"
    andromaque_a2 = dramatic_pool / "andromaque_A2.xml"
    berenice_a1 = dramatic_pool / "berenice_A1.xml"
    shutil.copy2(DRAMATIC_MERGE_FIXTURES / "andromaque_act1.xml", andromaque_a1)
    shutil.copy2(DRAMATIC_MERGE_FIXTURES / "andromaque_act2.xml", andromaque_a2)
    shutil.copy2(DRAMATIC_FIXTURES / "berenice.xml", berenice_a1)

    logo_file = base / "logo.txt"
    logo_file.write_text("ETS", encoding="utf-8")
    assets_dir = base / "brand"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "palette.txt").write_text("bleu", encoding="utf-8")

    request = SitePublicationRequest(
        identity=SiteIdentityInput(
            site_title="ETS Publication Request",
            site_subtitle="Service-level request",
            project_name="ETS",
        ),
        output_dir=output_dir,
        plays=(
            DramaticPlayInput(
                play_slug="andromaque",
                documents=(
                    DramaticDocumentInput(source_path=andromaque_a1),
                    DramaticDocumentInput(source_path=andromaque_a2),
                ),
                related_notice_slug="andromaque-notice",
            ),
            DramaticPlayInput(
                play_slug="berenice",
                documents=(DramaticDocumentInput(source_path=berenice_a1),),
            ),
        ),
        play_order=("berenice", "andromaque"),
        notices=(NoticeInput(source_path=MINIMAL_NOTICES / "andromaque-notice.xml"),),
        assets=SiteAssetsInput(
            logo_files=(logo_file,),
            asset_directories=(assets_dir,),
        ),
        show_xml_download=True,
        publish_notices=True,
    )

    result = build_site_from_publication_request(request)

    assert result.ok is True
    assert result.play_count == 2
    assert result.notice_count == 1
    assert "plays/berenice.html" in result.generated_page_relpaths
    assert "plays/andromaque.html" in result.generated_page_relpaths
    assert result.generated_page_relpaths.index("plays/berenice.html") < result.generated_page_relpaths.index(
        "plays/andromaque.html"
    )
    assert not any("only the first file is used" in warning for warning in result.warnings)
    assert (output_dir / "assets" / "logos" / "logo.txt").exists()
    assert (output_dir / "assets" / "brand" / "palette.txt").exists()
    assert (output_dir / "xml" / "dramatic" / "andromaque.xml").exists()
    assert (output_dir / "xml" / "notices" / "andromaque-notice.xml").exists()
    merged_xml = (output_dir / "xml" / "dramatic" / "andromaque.xml").read_text(encoding="utf-8")
    merged_tree = etree.fromstring(merged_xml.encode("utf-8"))
    act_divisions = merged_tree.xpath("//*[local-name()='body']/*[local-name()='div' and @type='act']")
    assert len(act_divisions) == 2


def test_site_builder_service_build_from_publication_request_fails_cleanly_on_invalid_request() -> None:
    base = _runtime_dir("app_site_builder_service_publication_request_invalid")
    request = SitePublicationRequest(
        identity=SiteIdentityInput(site_title="   "),
        output_dir=base / "site",
        plays=(),
    )

    service = SiteBuilderService()
    result = service.build_from_publication_request(request)

    assert result.ok is False
    assert result.error_code == "E_SITE_REQUEST"
    assert result.error_detail is not None
    assert "site title is required" in result.error_detail.lower()


def test_site_builder_service_publication_request_supports_general_notice_and_home_sections() -> None:
    base = _runtime_dir("app_site_builder_service_publication_request_general_notice")
    output_dir = base / "site"
    request = SitePublicationRequest(
        identity=SiteIdentityInput(
            site_title="ETS Publication Request Editorial",
            homepage_sections=(
                SiteHomepageSectionInput(
                    title="Cadre scientifique",
                    paragraphs=("Edition en cours de consolidation.",),
                ),
            ),
        ),
        output_dir=output_dir,
        plays=(
            DramaticPlayInput(
                play_slug="andromaque",
                documents=(DramaticDocumentInput(source_path=DRAMATIC_FIXTURES / "andromaque.xml"),),
                related_notice_slug="introduction",
            ),
        ),
        notices=(
            NoticeInput(source_path=REALISTIC_NOTICES / "Ch01_Introduction.xml"),
            NoticeInput(source_path=REALISTIC_NOTICES / "Heraldique_et_Papaute_volII.xml"),
        ),
        general_notice_slug="heraldique-et-papaute",
        publish_notices=True,
    )

    result = build_site_from_publication_request(request)

    assert result.ok is True
    assert "notices/heraldique-et-papaute.html" in result.generated_page_relpaths
    home_html = (output_dir / "index.html").read_text(encoding="utf-8")
    assert "Cadre scientifique" in home_html
    assert "Introduction générale" in home_html
