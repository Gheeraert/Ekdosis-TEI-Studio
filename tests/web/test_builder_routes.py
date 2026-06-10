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
    assert 'name="play_xml"' in html
    assert 'name="home_page_file"' in html


def test_builder_get_does_not_expose_pdf_options(client) -> None:
    rv = client.get("/publish/builder")
    html = rv.data.decode().lower()
    assert "build_latex_pdf" not in html
    assert "latex" not in html or "LaTeX" not in rv.data.decode()


# ── POST sans page d'accueil ──────────────────────────────────────────────────

def test_builder_post_without_home_page_returns_error(client) -> None:
    rv = client.post(
        "/publish/builder",
        data={
            "corpus_title": "Tragédies",
            "play_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
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
            "play_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
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
            "play_xml": (io.BytesIO(b"not xml"), "britannicus.docx"),
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
            "play_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
            "play_dramatis": (io.BytesIO(b"docx content"), "dramatis.docx"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode().lower()
    assert "extension" in html or "erreur" in html


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
            "play_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
        },
        content_type="multipart/form-data",
    )

    assert captured.get("build_latex_pdf") is False


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
            "play_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
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


# ── GET /publish/builder — nouveaux éléments de configuration ─────────────────

def test_builder_get_contains_config_section(client) -> None:
    rv = client.get("/publish/builder")
    assert "Configuration du constructeur" in rv.data.decode()


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
            "publish_notices": "1",
            "include_metadata": "1",
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["corpus_title"] == "Tragédies complètes"
    assert data["author_first_name"] == "Jean"
    assert data["author_last_name"] == "Racine"
    assert data["editor_first_name"] == "Dr"
    assert data["editor_last_name"] == "Martin"
    assert data["options"]["publish_notices"] is True
    assert data["options"]["publish_prefaces"] is False
    assert data["options"]["include_metadata"] is True


# ── POST /publish/builder/source-package ──────────────────────────────────────

def test_builder_source_package_returns_zip(client) -> None:
    rv = client.post(
        "/publish/builder/source-package",
        data={
            "corpus_title": "Tragédies",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
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
            "play_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
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
            "play_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
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
            "play_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
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


def test_builder_source_package_compatible_with_publish_static(client) -> None:
    rv = client.post(
        "/publish/builder/source-package",
        data={
            "corpus_title": "Tragédies",
            "author_first_name": "Jean",
            "author_last_name": "Racine",
            "home_page_file": (io.BytesIO(_HOME_XML), "accueil.xml"),
            "play_xml": (io.BytesIO(_PLAY_XML), "britannicus.xml"),
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
