"""Tests for the site builder Flask blueprint (GET/POST /publish/builder)."""

from __future__ import annotations

import io
import json
import tempfile
import zipfile
from pathlib import Path

import pytest

from ets.web import create_app


# ── Fixture ────────────────────────────────────────────────────────────────────

@pytest.fixture()
def client():
    app = create_app(testing=True)
    with app.test_client() as c:
        yield c


# ── XML minimaliste pour les tests ────────────────────────────────────────────

_HOME_XML = b"<TEI><text><body><div><p>Accueil</p></div></body></text></TEI>"
_PLAY_XML = b"<TEI><text><body/></text></TEI>"


# ── GET /publish/builder ──────────────────────────────────────────────────────

def test_builder_get_returns_200(client) -> None:
    rv = client.get("/publish/builder")
    assert rv.status_code == 200


def test_builder_get_contains_page_title(client) -> None:
    rv = client.get("/publish/builder")
    assert "Constructeur de site statique" in rv.data.decode()


def test_builder_get_contains_form(client) -> None:
    rv = client.get("/publish/builder")
    html = rv.data.decode()
    assert "<form" in html
    assert 'name="play_0_xml"' in html
    assert 'name="home_page_file"' in html


def test_builder_get_does_not_expose_pdf_options(client) -> None:
    rv = client.get("/publish/builder")
    html = rv.data.decode().lower()
    assert "build_latex_pdf" not in html
    assert "latex" not in html or "LaTeX" not in rv.data.decode()


# ── V2 — nouveaux éléments d'interface ───────────────────────────────────────

def test_builder_get_contains_corpus_de_pieces(client) -> None:
    rv = client.get("/publish/builder")
    assert "Corpus de pièces" in rv.data.decode()


def test_builder_get_contains_ajouter_une_piece(client) -> None:
    rv = client.get("/publish/builder")
    assert "Ajouter une pièce" in rv.data.decode()


def test_builder_get_contains_version_2(client) -> None:
    rv = client.get("/publish/builder")
    assert "Mode normal" in rv.data.decode()


def test_builder_get_does_not_contain_une_seule_piece(client) -> None:
    rv = client.get("/publish/builder")
    assert "une seule pièce à la fois" not in rv.data.decode()


def test_builder_get_does_not_expose_ftp_options(client) -> None:
    rv = client.get("/publish/builder")
    html = rv.data.decode()
    # Le mot "FTP" peut figurer dans le bandeau d'avertissement, mais aucun champ de formulaire FTP.
    assert 'name="ftp' not in html.lower()
    assert 'type="text" name="ftp' not in html.lower()


def test_builder_get_does_not_expose_back_privilege_fields(client) -> None:
    rv = client.get("/publish/builder")
    html = rv.data.decode()
    # Aucun champ de saisie pour back ou privilège.
    assert 'name="back' not in html.lower()
    assert 'name="privilege' not in html.lower()
    assert 'name="privileg' not in html.lower()


# ── POST sans page d'accueil ──────────────────────────────────────────────────

def test_builder_post_without_home_page_returns_error(client) -> None:
    rv = client.post(
        "/publish/builder",
        data={
            "corpus_title": "Tragédies",
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode().lower()
    assert "accueil" in html or "erreur" in html


# ── POST sans XML dramatique ──────────────────────────────────────────────────

def test_builder_post_without_play_xml_returns_error(client) -> None:
    rv = client.post(
        "/publish/builder",
        data={
            "corpus_title": "Tragédies",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode().lower()
    assert "xml" in html or "erreur" in html or "pi" in html


# ── POST sans titre de corpus ─────────────────────────────────────────────────

def test_builder_post_without_corpus_title_returns_error(client) -> None:
    rv = client.post(
        "/publish/builder",
        data={
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode().lower()
    assert "titre" in html or "erreur" in html or "corpus" in html


# ── POST avec extension refusée pour le XML dramatique ───────────────────────

def test_builder_post_play_with_bad_extension_returns_error(client) -> None:
    rv = client.post(
        "/publish/builder",
        data={
            "corpus_title": "Tragédies",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_0_xml": (io.BytesIO(b"not xml"), "britannicus.docx"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode().lower()
    assert "extension" in html or "erreur" in html


# ── POST avec extension refusée pour le dramatis ──────────────────────────────

def test_builder_post_dramatis_docx_is_refused(client) -> None:
    rv = client.post(
        "/publish/builder",
        data={
            "corpus_title": "Tragédies",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
            "play_0_dramatis": (io.BytesIO(b"docx content"), "dramatis.docx"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode().lower()
    assert "extension" in html or "erreur" in html


# ── POST avec notice mais sans XML de pièce → erreur lisible ─────────────────

def test_builder_post_notice_without_play_xml_returns_error(client) -> None:
    rv = client.post(
        "/publish/builder",
        data={
            "corpus_title": "Tragédies",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
            # play_1 a une notice mais pas de XML
            "play_1_notice": (io.BytesIO(b"<notice/>"), "notice.xml"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "xml" in html.lower() or "erreur" in html.lower() or "pièce" in html.lower()


# ── POST avec un bloc vide en trop → le bloc est ignoré ──────────────────────

def test_builder_post_empty_extra_block_is_ignored(client, monkeypatch, tmp_path) -> None:
    captured: dict = {}

    class _FakeService:
        def prepare_dialog_config_for_publication(self, config):
            from ets.application.editorial_notice_import.service import PreparedPublicationConfig
            captured["plays"] = config.plays
            return PreparedPublicationConfig(config=config)

    def _fake_request_from_config(config):
        raise ValueError("arrêt anticipé")

    monkeypatch.setattr("ets.web.publication_routes.EditorialNoticeImportService", _FakeService)
    monkeypatch.setattr(
        "ets.web.publication_routes.site_publication_request_from_dialog_config",
        _fake_request_from_config,
    )

    client.post(
        "/publish/builder",
        data={
            "corpus_title": "Tragédies",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
            # play_1 est totalement absent → ignoré
        },
        content_type="multipart/form-data",
    )

    assert len(captured.get("plays", ())) == 1


# ── build_latex_pdf toujours forcé à False ────────────────────────────────────

def test_builder_build_latex_pdf_forced_to_false(client, monkeypatch) -> None:
    captured: dict = {}

    class _FakeService:
        def prepare_dialog_config_for_publication(self, config):
            from ets.application.editorial_notice_import.service import PreparedPublicationConfig
            captured["build_latex_pdf"] = config.build_latex_pdf
            return PreparedPublicationConfig(config=config)

    def _fake_request_from_config(config):
        raise ValueError("arrêt anticipé")

    monkeypatch.setattr("ets.web.publication_routes.EditorialNoticeImportService", _FakeService)
    monkeypatch.setattr(
        "ets.web.publication_routes.site_publication_request_from_dialog_config",
        _fake_request_from_config,
    )

    client.post(
        "/publish/builder",
        data={
            "corpus_title": "Tragédies",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
        },
        content_type="multipart/form-data",
    )

    assert captured.get("build_latex_pdf") is False


# ── POST deux pièces → config contient deux SitePublicationDialogPlayConfig ───

def test_builder_post_two_plays_builds_config_with_two_plays(client, monkeypatch) -> None:
    captured: dict = {}

    class _FakeService:
        def prepare_dialog_config_for_publication(self, config):
            from ets.application.editorial_notice_import.service import PreparedPublicationConfig
            captured["plays"] = config.plays
            return PreparedPublicationConfig(config=config)

    def _fake_request_from_config(config):
        raise ValueError("arrêt anticipé")

    monkeypatch.setattr("ets.web.publication_routes.EditorialNoticeImportService", _FakeService)
    monkeypatch.setattr(
        "ets.web.publication_routes.site_publication_request_from_dialog_config",
        _fake_request_from_config,
    )

    client.post(
        "/publish/builder",
        data={
            "corpus_title": "Tragédies",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
            "play_1_xml": (io.BytesIO(_PLAY_XML), "berenice.xml"),
        },
        content_type="multipart/form-data",
    )

    assert len(captured.get("plays", ())) == 2


# ── POST deux pièces → retourne un ZIP ───────────────────────────────────────

def test_builder_post_two_plays_returns_zip(client, monkeypatch, tmp_path) -> None:
    calls: list[str] = []

    class _FakeService:
        def prepare_dialog_config_for_publication(self, config):
            from ets.application.editorial_notice_import.service import PreparedPublicationConfig
            calls.append("prepare")
            return PreparedPublicationConfig(config=config)

    site_dir = tmp_path / "site_output"

    def _fake_request_from_config(config):
        calls.append("request_from_config")
        from unittest.mock import MagicMock
        req = MagicMock()
        req.output_dir = site_dir
        return req

    def _fake_build(pub_request):
        from ets.application import SiteBuildServiceResult
        calls.append("build")
        site_dir.mkdir(exist_ok=True)
        (site_dir / "index.html").write_text("<html>site</html>", encoding="utf-8")
        return SiteBuildServiceResult(ok=True, output_dir=site_dir, message="ok")

    monkeypatch.setattr("ets.web.publication_routes.EditorialNoticeImportService", _FakeService)
    monkeypatch.setattr(
        "ets.web.publication_routes.site_publication_request_from_dialog_config",
        _fake_request_from_config,
    )
    monkeypatch.setattr(
        "ets.web.publication_routes.build_site_from_publication_request",
        _fake_build,
    )

    rv = client.post(
        "/publish/builder",
        data={
            "corpus_title": "Tragédies",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
            "play_1_xml": (io.BytesIO(_PLAY_XML), "berenice.xml"),
        },
        content_type="multipart/form-data",
    )

    assert rv.status_code == 200
    assert "zip" in rv.content_type.lower()
    assert "prepare" in calls
    assert "request_from_config" in calls
    assert "build" in calls

    with zipfile.ZipFile(io.BytesIO(rv.data)) as zf:
        assert "index.html" in zf.namelist()


# ── Pipeline complet avec mocks → retourne un ZIP contenant index.html ────────

def test_builder_post_valid_input_returns_zip_with_index(client, monkeypatch, tmp_path) -> None:
    calls: list[str] = []

    class _FakeService:
        def prepare_dialog_config_for_publication(self, config):
            from ets.application.editorial_notice_import.service import PreparedPublicationConfig
            calls.append("prepare")
            return PreparedPublicationConfig(config=config)

    site_dir = tmp_path / "site_output"

    def _fake_request_from_config(config):
        calls.append("request_from_config")
        from unittest.mock import MagicMock
        req = MagicMock()
        req.output_dir = site_dir
        return req

    def _fake_build(pub_request):
        from ets.application import SiteBuildServiceResult
        calls.append("build")
        site_dir.mkdir(exist_ok=True)
        (site_dir / "index.html").write_text("<html>site</html>", encoding="utf-8")
        return SiteBuildServiceResult(ok=True, output_dir=site_dir, message="ok")

    monkeypatch.setattr("ets.web.publication_routes.EditorialNoticeImportService", _FakeService)
    monkeypatch.setattr(
        "ets.web.publication_routes.site_publication_request_from_dialog_config",
        _fake_request_from_config,
    )
    monkeypatch.setattr(
        "ets.web.publication_routes.build_site_from_publication_request",
        _fake_build,
    )

    rv = client.post(
        "/publish/builder",
        data={
            "author_first_name": "Jean",
            "author_last_name": "Racine",
            "corpus_title": "Tragédies complètes",
            "editor_first_name": "Dr",
            "editor_last_name": "Martin",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
            "publish_notices": "1",
            "publish_prefaces": "1",
            "include_metadata": "1",
            "resolve_notice_xincludes": "1",
        },
        content_type="multipart/form-data",
    )

    assert rv.status_code == 200
    assert "zip" in rv.content_type.lower()
    assert "prepare" in calls
    assert "request_from_config" in calls
    assert "build" in calls

    with zipfile.ZipFile(io.BytesIO(rv.data)) as zf:
        assert "index.html" in zf.namelist()


# ── Isolation — pas de Tkinter dans le code web ───────────────────────────────

def test_builder_blueprint_does_not_import_tkinter() -> None:
    from pathlib import Path
    web_dir = Path(__file__).parents[2] / "src" / "ets" / "web"
    for py_file in web_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "tkinter" not in content, f"tkinter importé dans {py_file.name}"


# ── GET /publish/builder — éléments de configuration ─────────────────────────

def test_builder_get_contains_config_section(client) -> None:
    rv = client.get("/publish/builder")
    assert "Importations de configurations antérieures" in rv.data.decode()


def test_builder_get_contains_load_config_json(client) -> None:
    rv = client.get("/publish/builder")
    assert "Importer une configuration JSON" in rv.data.decode()


def test_builder_get_contains_download_config_json(client) -> None:
    rv = client.get("/publish/builder")
    assert "Exporter la configuration JSON" in rv.data.decode()


def test_builder_get_contains_download_source_package(client) -> None:
    rv = client.get("/publish/builder")
    assert "Exporter le paquet source de publication" in rv.data.decode()


# ── POST /publish/builder/config ──────────────────────────────────────────────

def test_builder_config_post_returns_json(client) -> None:
    rv = client.post(
        "/publish/builder/config",
        data={
            "corpus_title": "Tragédies",
            "author_first_name": "Jean",
            "author_last_name": "Racine",
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    assert "json" in rv.content_type.lower()


def test_builder_config_json_contains_metadata_and_options(client) -> None:
    rv = client.post(
        "/publish/builder/config",
        data={
            "corpus_title": "Tragédies complètes",
            "author_first_name": "Jean",
            "author_last_name": "Racine",
            "editor_first_name": "Dr",
            "editor_last_name": "Martin",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.docx"),
            "general_intro_file": (io.BytesIO(_HOME_XML), "introduction.docx"),
            "play_0_xml": (io.BytesIO(_PLAY_XML), "Britannicus.xml"),
            "play_0_notice": (io.BytesIO(b"notice"), "britannicus_notice.docx"),
            "publish_notices": "1",
            "publish_prefaces": "1",
            "include_metadata": "1",
            "resolve_notice_xincludes": "1",
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["schema"] == "ets.site_publication_dialog_config"
    assert data["metadata"]["corpus_title"] == "Tragédies complètes"
    assert data["metadata"]["author_name"] == "Jean Racine"
    assert data["metadata"]["scientific_editor"] == "Dr Martin"
    assert data["xml_sources"]["home_page_tei_path"] == "sources/accueil.docx"
    assert data["xml_sources"]["general_intro_tei_path"] == "sources/introduction.docx"
    assert data["plays"][0]["dramatic_xml_path"] == "sources/Britannicus.xml"
    assert data["plays"][0]["notice_xml_path"] == "sources/britannicus_notice.docx"
    assert data["options"]["publish_notices"] is True
    assert data["options"]["publish_prefaces"] is True
    assert data["options"]["include_metadata"] is True
    assert data["options"]["resolve_notice_xincludes"] is True
    assert data["options"]["build_latex_pdf"] is False
    assert data["options"]["hide_minor_variants_in_pdf"] is False


def test_builder_config_export_two_plays(client) -> None:
    rv = client.post(
        "/publish/builder/config",
        data={
            "corpus_title": "Tragédies",
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
            "play_1_xml": (io.BytesIO(_PLAY_XML), "berenice.xml"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert len(data["plays"]) == 2
    assert data["schema"] == "ets.site_publication_dialog_config"
    assert data["plays"][0]["dramatic_xml_path"] == "sources/britannicus.xml"
    assert data["plays"][1]["dramatic_xml_path"] == "sources/berenice.xml"
    assert data["play_order"] == ["britannicus", "berenice"]


# ── POST /publish/builder/source-package ──────────────────────────────────────

def test_builder_source_package_returns_zip(client) -> None:
    rv = client.post(
        "/publish/builder/source-package",
        data={
            "corpus_title": "Tragédies",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    assert "zip" in rv.content_type.lower()


def test_builder_source_package_zip_contains_config(client) -> None:
    rv = client.post(
        "/publish/builder/source-package",
        data={
            "corpus_title": "Tragédies",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
        },
        content_type="multipart/form-data",
    )
    with zipfile.ZipFile(io.BytesIO(rv.data)) as zf:
        assert "publication_config.json" in zf.namelist()


def test_builder_source_package_zip_contains_sources(client) -> None:
    rv = client.post(
        "/publish/builder/source-package",
        data={
            "corpus_title": "Tragédies",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
        },
        content_type="multipart/form-data",
    )
    with zipfile.ZipFile(io.BytesIO(rv.data)) as zf:
        names = zf.namelist()
    assert any("accueil.xml" in n for n in names)
    assert any("britannicus.xml" in n for n in names)


def test_builder_source_package_config_uses_relative_paths(client) -> None:
    rv = client.post(
        "/publish/builder/source-package",
        data={
            "corpus_title": "Tragédies",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
        },
        content_type="multipart/form-data",
    )
    with zipfile.ZipFile(io.BytesIO(rv.data)) as zf:
        config_bytes = zf.read("publication_config.json")
    payload = json.loads(config_bytes.decode("utf-8"))
    home_path = payload["xml_sources"]["home_page_tei_path"]
    play_path = payload["plays"][0]["dramatic_xml_path"]
    assert home_path is not None
    assert not Path(home_path).is_absolute(), f"chemin non relatif : {home_path}"
    assert not Path(play_path).is_absolute(), f"chemin non relatif : {play_path}"


def test_builder_source_package_two_plays_zip_contains_both_xmls(client) -> None:
    rv = client.post(
        "/publish/builder/source-package",
        data={
            "corpus_title": "Tragédies",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
            "play_1_xml": (io.BytesIO(_PLAY_XML), "berenice.xml"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    with zipfile.ZipFile(io.BytesIO(rv.data)) as zf:
        names = zf.namelist()
    assert any("britannicus.xml" in n for n in names)
    assert any("berenice.xml" in n for n in names)


def test_builder_source_package_config_has_two_plays(client) -> None:
    rv = client.post(
        "/publish/builder/source-package",
        data={
            "corpus_title": "Tragédies",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
            "play_1_xml": (io.BytesIO(_PLAY_XML), "berenice.xml"),
        },
        content_type="multipart/form-data",
    )
    with zipfile.ZipFile(io.BytesIO(rv.data)) as zf:
        config_bytes = zf.read("publication_config.json")
    payload = json.loads(config_bytes.decode("utf-8"))
    assert len(payload["plays"]) == 2


def test_builder_source_package_compatible_with_publish_static(client) -> None:
    rv = client.post(
        "/publish/builder/source-package",
        data={
            "corpus_title": "Tragédies",
            "author_first_name": "Jean",
            "author_last_name": "Racine",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
            "publish_notices": "1",
            "publish_prefaces": "1",
            "include_metadata": "1",
            "resolve_notice_xincludes": "1",
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200

    from ets.application import site_publication_dialog_config_from_dict

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        with zipfile.ZipFile(io.BytesIO(rv.data)) as zf:
            for entry in zf.infolist():
                if not entry.filename.endswith("/"):
                    target = tmp / entry.filename
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(zf.read(entry.filename))
            config_bytes = zf.read("publication_config.json")

        payload = json.loads(config_bytes.decode("utf-8"))
        config = site_publication_dialog_config_from_dict(payload, base_dir=tmp)
        assert config.corpus_title == "Tragédies"
        assert config.author_name == "Jean Racine"


# ── JS : le fichier builder.js contient la logique multi-pièces ──────────────

def test_builder_js_contains_multi_play_restore_logic() -> None:
    js_path = Path(__file__).parents[2] / "src" / "ets" / "web" / "static" / "builder.js"
    assert js_path.exists(), "builder.js introuvable"
    content = js_path.read_text(encoding="utf-8")
    assert "plays" in content
    assert "_buildBlock" in content
    assert "expected_xml_filename" in content


def test_builder_js_import_accepts_publication_config_and_windows_basenames() -> None:
    js_path = Path(__file__).parents[2] / "src" / "ets" / "web" / "static" / "builder.js"
    content = js_path.read_text(encoding="utf-8")
    assert "ets.site_publication_dialog_config" in content
    assert "basenameAnyPath" in content
    assert "replace(/\\\\/g, '/')" in content
    assert "home_page_tei_path" in content
    assert "general_intro_tei_path" in content
    assert "dramatic_xml_path" in content
    assert "notice_xml_path" in content
    assert "logo_paths" in content


# ── Helpers pour les tests d'import de paquet source ─────────────────────────

def test_builder_source_package_paths_match_zip_entries(client) -> None:
    rv = client.post(
        "/publish/builder/source-package",
        data={
            "corpus_title": "Tragédies",
            "author_first_name": "Jean",
            "author_last_name": "Racine",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "general_intro_file": (io.BytesIO(_HOME_XML), "introduction.xml"),
            "logos": (io.BytesIO(b"logo"), "logo.svg"),
            "play_0_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
            "play_0_notice": (io.BytesIO(b"<TEI/>"), "britannicus_notice.xml"),
            "play_0_preface": (io.BytesIO(b"<TEI/>"), "britannicus_preface.xml"),
            "play_0_dramatis": (io.BytesIO(b"<TEI/>"), "britannicus_dramatis.xml"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200

    from ets.application import site_publication_dialog_config_from_dict

    with zipfile.ZipFile(io.BytesIO(rv.data)) as zf:
        names = set(zf.namelist())
        payload = json.loads(zf.read("publication_config.json").decode("utf-8"))

    paths = [
        payload["xml_sources"]["home_page_tei_path"],
        payload["xml_sources"]["general_intro_tei_path"],
        *payload["assets"]["logo_paths"],
    ]
    for play in payload["plays"]:
        paths.extend([
            play["dramatic_xml_path"],
            play["notice_xml_path"],
            play["preface_xml_path"],
            play["dramatis_xml_path"],
        ])

    for path in [p for p in paths if p is not None]:
        assert path in names
        assert path.startswith("sources/")
        assert not Path(path).is_absolute()
        assert ".." not in Path(path).parts

    config = site_publication_dialog_config_from_dict(payload, base_dir=Path("."))
    assert config.plays[0].play_slug == "britannicus"


def test_builder_source_package_without_dramatic_xml_is_not_exportable(client) -> None:
    rv = client.post(
        "/publish/builder/source-package",
        data={
            "corpus_title": "Tragédies",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_0_notice": (io.BytesIO(b"<TEI/>"), "notice.xml"),
        },
        content_type="multipart/form-data",
    )

    assert rv.status_code == 200
    assert "zip" not in rv.content_type.lower()
    assert "xml" in rv.data.decode().lower() or "erreur" in rv.data.decode().lower()


_VALID_SOURCE_CONFIG = json.dumps({
    "schema": "ets.site_publication_dialog_config",
    "version": 3,
    "metadata": {
        "author_name": "Jean Racine",
        "corpus_title": "Tragédies",
        "scientific_editor": "Dr Martin",
    },
    "xml_sources": {
        "home_page_tei_path": "sources/accueil.xml",
        "general_intro_tei_path": None,
    },
    "plays": [
        {
            "play_slug": "britannicus",
            "dramatic_xml_path": "sources/britannicus.xml",
            "notice_xml_path": "sources/britannicus_notice.docx",
            "preface_xml_path": None,
            "dramatis_xml_path": None,
        }
    ],
    "options": {
        "show_xml_download": True,
        "build_latex_pdf": False,
        "hide_minor_variants_in_pdf": False,
        "publish_notices": True,
        "publish_prefaces": True,
        "include_metadata": True,
        "resolve_notice_xincludes": True,
    },
})


def _make_source_zip(config_json: str | None = None, extra_entries: list | None = None) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        if config_json is not None:
            zf.writestr("publication_config.json", config_json.encode("utf-8"))
        for name, data in (extra_entries or []):
            zf.writestr(name, data)
    buf.seek(0)
    return buf.read()


# ── POST /publish/builder/import-source-package ───────────────────────────────

def test_builder_import_source_no_json_returns_error(client) -> None:
    zip_data = _make_source_zip(config_json=None)
    rv = client.post(
        "/publish/builder/import-source-package",
        data={"source_package_file": (io.BytesIO(zip_data), "source.zip")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "JSON" in html or "json" in html.lower()
    assert "erreur" in html.lower() or "Erreur" in html


def test_builder_import_source_multiple_json_returns_error(client) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("publication_config.json", b"{}")
        zf.writestr("other.json", b"{}")
    buf.seek(0)
    rv = client.post(
        "/publish/builder/import-source-package",
        data={"source_package_file": (io.BytesIO(buf.read()), "source.zip")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "plusieurs" in html.lower() or "erreur" in html.lower()


def test_builder_import_source_zip_with_too_large_uncompressed_size_returns_error(client, monkeypatch) -> None:
    monkeypatch.setattr("ets.web.publication_routes._MAX_SOURCE_ZIP_UNCOMPRESSED_BYTES", 10)
    zip_data = _make_source_zip(
        config_json=_VALID_SOURCE_CONFIG,
        extra_entries=[("sources/britannicus.xml", b"<TEI>contenu trop long</TEI>")],
    )

    rv = client.post(
        "/publish/builder/import-source-package",
        data={"source_package_file": (io.BytesIO(zip_data), "source.zip")},
        content_type="multipart/form-data",
    )

    assert rv.status_code == 200
    assert "zip" not in rv.content_type.lower()
    html = rv.data.decode().lower()
    assert "taille" in html or "volumineux" in html or "zip" in html


def test_builder_import_source_invalid_json_returns_error(client) -> None:
    zip_data = _make_source_zip(config_json="not valid json {{{")
    rv = client.post(
        "/publish/builder/import-source-package",
        data={"source_package_file": (io.BytesIO(zip_data), "source.zip")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "invalide" in html.lower() or "erreur" in html.lower()


def test_builder_import_source_dangerous_entry_refused(client) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("publication_config.json", b"{}")
        zf.writestr(zipfile.ZipInfo("../secret.txt"), b"danger")
    buf.seek(0)
    rv = client.post(
        "/publish/builder/import-source-package",
        data={"source_package_file": (io.BytesIO(buf.read()), "source.zip")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "dangereux" in html.lower() or "erreur" in html.lower()


def test_builder_import_source_valid_zip_shows_metadata(client) -> None:
    zip_data = _make_source_zip(config_json=_VALID_SOURCE_CONFIG)
    rv = client.post(
        "/publish/builder/import-source-package",
        data={"source_package_file": (io.BytesIO(zip_data), "source.zip")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Tragédies" in html
    assert "Jean Racine" in html


def test_builder_import_source_valid_zip_shows_play_slug(client) -> None:
    zip_data = _make_source_zip(config_json=_VALID_SOURCE_CONFIG)
    rv = client.post(
        "/publish/builder/import-source-package",
        data={"source_package_file": (io.BytesIO(zip_data), "source.zip")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    assert "britannicus" in rv.data.decode()


def test_builder_import_source_valid_zip_shows_source_paths(client) -> None:
    zip_data = _make_source_zip(config_json=_VALID_SOURCE_CONFIG)
    rv = client.post(
        "/publish/builder/import-source-package",
        data={"source_package_file": (io.BytesIO(zip_data), "source.zip")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    assert "sources/britannicus.xml" in rv.data.decode()


def test_builder_import_json_config_still_works(client) -> None:
    rv = client.post(
        "/publish/builder/config",
        data={"corpus_title": "Tragédies", "author_first_name": "Jean"},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    assert "json" in rv.content_type.lower()
    data = json.loads(rv.data)
    assert data["schema"] == "ets.site_publication_dialog_config"
    assert data["metadata"]["corpus_title"] == "Tragédies"
    assert data["metadata"]["author_name"] == "Jean"


def test_publish_static_route_still_reachable(client) -> None:
    rv = client.get("/publish/static")
    assert rv.status_code == 200


def test_builder_import_source_dangerous_json_path_refused(client) -> None:
    config = json.dumps({
        "schema": "ets.site_publication_dialog_config",
        "version": 3,
        "metadata": {"author_name": "Jean Racine", "corpus_title": "Tragédies", "scientific_editor": ""},
        "xml_sources": {"home_page_tei_path": "sources/accueil.xml", "general_intro_tei_path": None},
        "plays": [
            {
                "play_slug": "britannicus",
                "dramatic_xml_path": "../../etc/passwd",
                "notice_xml_path": None,
                "preface_xml_path": None,
                "dramatis_xml_path": None,
            }
        ],
        "options": {},
    })
    zip_data = _make_source_zip(config_json=config)
    rv = client.post(
        "/publish/builder/import-source-package",
        data={"source_package_file": (io.BytesIO(zip_data), "source.zip")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "dangereux" in html.lower() or "erreur" in html.lower()
    assert "etc/passwd" not in html or "dangereux" in html.lower()
