from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from lxml import html as lxml_html

from ets.application import (
    DramaticDocumentInput,
    DramaticPlayInput,
    NoticeInput,
    SiteAssetsInput,
    SiteBuildRequest,
    SiteBuilderService,
    SiteHomepageSectionInput,
    SiteIdentityInput,
    SitePublicationDialogConfig,
    SitePublicationDialogPlayConfig,
    SitePublicationRequest,
    build_site_from_config_dict,
    build_site_from_config_file,
    build_site_from_publication_request,
    site_publication_request_from_dialog_config,
)


ROOT = Path(__file__).resolve().parents[1]
DRAMATIC_FIXTURES = ROOT / "fixtures" / "site_builder" / "minimal" / "dramatic"
MINIMAL_NOTICES = ROOT / "fixtures" / "site_builder" / "minimal" / "notices"
REALISTIC_NOTICES = ROOT / "fixtures" / "metopes" / "realistic"
UNITES_FIXTURES = ROOT / "fixtures" / "site_builder" / "unites_editoriales"
RUNTIME_ROOT = ROOT / "tests" / "_runtime"


def _runtime_dir(prefix: str) -> Path:
    target = RUNTIME_ROOT / f"{prefix}_{uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _write_external_dramatis(path: Path) -> None:
    path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <front>
      <castList>
        <castItem>Personnage externe Alpha</castItem>
        <castItem>Personnage externe Beta</castItem>
      </castList>
    </front>
  </text>
</TEI>
""",
        encoding="utf-8",
    )


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


def test_site_builder_service_build_from_publication_request_single_play_uses_one_xml() -> None:
    base = _runtime_dir("app_site_builder_service_publication_request_single")
    output_dir = base / "site"
    source_xml = DRAMATIC_FIXTURES / "andromaque.xml"

    request = SitePublicationRequest(
        identity=SiteIdentityInput(site_title="ETS Publication Request Single Play"),
        output_dir=output_dir,
        plays=(
            DramaticPlayInput(
                play_slug="andromaque",
                document=DramaticDocumentInput(source_path=source_xml),
            ),
        ),
        show_xml_download=True,
        publish_notices=False,
    )

    result = build_site_from_publication_request(request)

    assert result.ok is True
    assert result.play_count == 1
    assert result.notice_count == 0
    assert "plays/andromaque.html" in result.generated_page_relpaths
    copied_xml = output_dir / "xml" / "dramatic" / "andromaque.xml"
    assert copied_xml.exists()
    assert copied_xml.read_text(encoding="utf-8") == source_xml.read_text(encoding="utf-8")


def test_site_builder_service_build_from_publication_request_supports_multiple_plays_order_and_assets() -> None:
    base = _runtime_dir("app_site_builder_service_publication_request")
    output_dir = base / "site"
    andromaque = DRAMATIC_FIXTURES / "andromaque.xml"
    berenice = DRAMATIC_FIXTURES / "berenice.xml"

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
                document=DramaticDocumentInput(source_path=andromaque),
                related_notice_slug="andromaque-notice",
            ),
            DramaticPlayInput(
                play_slug="berenice",
                document=DramaticDocumentInput(source_path=berenice),
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
    assert (output_dir / "xml" / "dramatic" / "berenice.xml").exists()
    assert (output_dir / "xml" / "notices" / "andromaque-notice.xml").exists()


def test_site_builder_service_build_from_publication_request_supports_play_notice_path_mapping() -> None:
    base = _runtime_dir("app_site_builder_service_publication_request_play_notice_path")
    output_dir = base / "site"

    request = SitePublicationRequest(
        identity=SiteIdentityInput(site_title="ETS Publication Request Play Notice Path"),
        output_dir=output_dir,
        plays=(
            DramaticPlayInput(
                play_slug="andromaque",
                document=DramaticDocumentInput(source_path=DRAMATIC_FIXTURES / "andromaque.xml"),
                related_notice_path=MINIMAL_NOTICES / "andromaque-notice.xml",
            ),
        ),
        publish_notices=True,
    )

    result = build_site_from_publication_request(request)

    assert result.ok is True
    assert result.play_count == 1
    assert result.notice_count == 1
    assert "plays/andromaque.html" in result.generated_page_relpaths
    assert "notices/andromaque-notice.html" in result.generated_page_relpaths
    play_html = (output_dir / "plays" / "andromaque.html").read_text(encoding="utf-8")
    assert "Notice de pièce" in play_html


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
                document=DramaticDocumentInput(source_path=DRAMATIC_FIXTURES / "andromaque.xml"),
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


def test_site_builder_service_publication_request_inlines_home_page_tei_notice_on_index() -> None:
    base = _runtime_dir("app_site_builder_service_publication_request_home_page_tei")
    output_dir = base / "site"
    dialog_config = SitePublicationDialogConfig(
        author_name="Jean Racine",
        corpus_title="Théâtre complet",
        output_dir=output_dir,
        home_page_tei=REALISTIC_NOTICES / "Ch01_Introduction.xml",
        general_intro_tei=REALISTIC_NOTICES / "Heraldique_et_Papaute_volII.xml",
        plays=(
            SitePublicationDialogPlayConfig(
                play_slug="andromaque",
                dramatic_xml_path=DRAMATIC_FIXTURES / "andromaque.xml",
            ),
        ),
    )

    request = site_publication_request_from_dialog_config(dialog_config)
    result = build_site_from_publication_request(request)

    assert result.ok is True
    home_html = (output_dir / "index.html").read_text(encoding="utf-8")
    assert 'class="home-page-notice"' in home_html
    assert "Yvan Loskoutoff" in home_html
    assert "Ce deuxième volume" in home_html
    assert "Introduction générale" in home_html
    assert 'class="notice-title-block"' not in home_html
    assert 'class="notice-meta"' not in home_html
    assert 'class="toc-label"' not in home_html
    assert ">SEC<" not in home_html


def test_site_builder_service_publication_request_notice_and_preface_flags_are_independent() -> None:
    base = _runtime_dir("app_site_builder_service_publication_request_independent_flags")
    output_dir = base / "site"
    preface_source = UNITES_FIXTURES / "préface.xml"
    notice_source = MINIMAL_NOTICES / "andromaque-notice.xml"

    request_preface_only = SitePublicationRequest(
        identity=SiteIdentityInput(site_title="ETS Preface Only"),
        output_dir=output_dir,
        plays=(
            DramaticPlayInput(
                play_slug="andromaque",
                document=DramaticDocumentInput(source_path=DRAMATIC_FIXTURES / "andromaque.xml"),
                notice_xml_path=notice_source,
                preface_xml_path=preface_source,
            ),
        ),
        publish_notices=False,
        publish_prefaces=True,
    )
    result_preface_only = build_site_from_publication_request(request_preface_only)
    assert result_preface_only.ok is True
    assert any(path.startswith("notices/") for path in result_preface_only.generated_page_relpaths)
    assert "notices/andromaque-notice.html" not in result_preface_only.generated_page_relpaths

    request_notice_only = SitePublicationRequest(
        identity=SiteIdentityInput(site_title="ETS Notice Only"),
        output_dir=base / "site2",
        plays=(
            DramaticPlayInput(
                play_slug="andromaque",
                document=DramaticDocumentInput(source_path=DRAMATIC_FIXTURES / "andromaque.xml"),
                notice_xml_path=notice_source,
                preface_xml_path=preface_source,
            ),
        ),
        publish_notices=True,
        publish_prefaces=False,
    )
    result_notice_only = build_site_from_publication_request(request_notice_only)
    assert result_notice_only.ok is True
    assert "notices/andromaque-notice.html" in result_notice_only.generated_page_relpaths
    assert all("mithridate-preface-fixture-tei-simplifiee" not in item for item in result_notice_only.generated_page_relpaths)


def test_site_builder_service_publication_request_external_dramatis_has_priority() -> None:
    base = _runtime_dir("app_site_builder_service_external_dramatis_priority")
    output_dir = base / "site"
    external_dramatis = base / "dramatis_externe.xml"
    _write_external_dramatis(external_dramatis)

    request = SitePublicationRequest(
        identity=SiteIdentityInput(site_title="ETS Dramatis Priority"),
        output_dir=output_dir,
        plays=(
            DramaticPlayInput(
                play_slug="la-thebaide",
                document=DramaticDocumentInput(source_path=UNITES_FIXTURES / "piece.xml"),
                dramatis_xml_path=external_dramatis,
            ),
        ),
        publish_notices=False,
    )

    result = build_site_from_publication_request(request)
    assert result.ok is True

    play_page = next(path for path in result.generated_page_relpaths if path.startswith("plays/"))
    play_html = (output_dir / play_page).read_text(encoding="utf-8")
    doc = lxml_html.document_fromstring(play_html)
    items = doc.xpath("//section[contains(@class, 'dramatis-personae-block')]//li/text()")
    assert items == ["Personnage externe Alpha", "Personnage externe Beta"]


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

