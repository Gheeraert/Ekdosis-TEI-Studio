"""Tests for the static publication Flask blueprint (/publish/static)."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest

from ets.web import create_app


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_zip(files: dict[str, bytes | str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            if isinstance(content, str):
                content = content.encode("utf-8")
            zf.writestr(name, content)
    return buf.getvalue()


def _pub_config(
    *,
    author: str = "Racine",
    corpus: str = "Theatre de Racine",
    output_dir: str | None = None,
    build_latex_pdf: bool = False,
    dramatic_path: str = "dramatic/britannicus.xml",
) -> dict:
    return {
        "schema": "ets.site_publication_dialog_config",
        "version": 3,
        "metadata": {
            "author_name": author,
            "corpus_title": corpus,
            "scientific_editor": "Editeur",
        },
        "xml_sources": {
            "home_page_tei_path": None,
            "general_intro_tei_path": None,
        },
        "plays": [
            {
                "play_slug": "britannicus",
                "dramatic_xml_path": dramatic_path,
                "notice_xml_path": None,
                "preface_xml_path": None,
                "dramatis_xml_path": None,
            }
        ],
        "play_order": ["britannicus"],
        "output": {"output_dir": output_dir},
        "assets": {"logo_paths": [], "asset_directories": []},
        "options": {
            "show_xml_download": True,
            "build_latex_pdf": build_latex_pdf,
            "hide_minor_variants_in_pdf": False,
            "publish_notices": True,
            "publish_prefaces": True,
            "include_metadata": True,
            "resolve_notice_xincludes": True,
        },
    }


_DUMMY_XML = b"<TEI><text><body/></text></TEI>"


# ── Fixture ────────────────────────────────────────────────────────────────────

@pytest.fixture()
def client():
    app = create_app(testing=True)
    with app.test_client() as c:
        yield c


# ── GET /publish/static ───────────────────────────────────────────────────────

def test_publish_static_get_returns_200(client) -> None:
    rv = client.get("/publish/static")
    assert rv.status_code == 200


def test_publish_static_get_contains_upload_form(client) -> None:
    rv = client.get("/publish/static")
    html = rv.data.decode()
    assert "<form" in html
    assert 'name="source_zip"' in html


# ── POST sans fichier ─────────────────────────────────────────────────────────

def test_publish_static_post_without_file_returns_error(client) -> None:
    rv = client.post("/publish/static", data={})
    assert rv.status_code == 200
    html = rv.data.decode().lower()
    assert "erreur" in html or "zip" in html


# ── POST avec ZIP invalide ────────────────────────────────────────────────────

def test_publish_static_post_invalid_zip_returns_error(client) -> None:
    rv = client.post(
        "/publish/static",
        data={"source_zip": (io.BytesIO(b"ceci n'est pas un zip"), "test.zip")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode().lower()
    assert "zip" in html and ("valide" in html or "erreur" in html)


# ── ZIP sans JSON ─────────────────────────────────────────────────────────────

def test_publish_static_zip_without_json_returns_error(client) -> None:
    zip_bytes = _make_zip({"dramatic/britannicus.xml": _DUMMY_XML})
    rv = client.post(
        "/publish/static",
        data={"source_zip": (io.BytesIO(zip_bytes), "source.zip")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode().lower()
    assert "json" in html


# ── ZIP avec plusieurs JSON ───────────────────────────────────────────────────

def test_publish_static_zip_with_multiple_json_returns_error(client) -> None:
    cfg = _pub_config()
    zip_bytes = _make_zip({
        "config_a.json": json.dumps(cfg),
        "config_b.json": json.dumps(cfg),
    })
    rv = client.post(
        "/publish/static",
        data={"source_zip": (io.BytesIO(zip_bytes), "source.zip")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode().lower()
    assert "plusieurs" in html or "erreur" in html


# ── JSON malformé ─────────────────────────────────────────────────────────────

def test_publish_static_malformed_json_returns_error_not_500(client) -> None:
    zip_bytes = _make_zip({"publication_config.json": b"{ pas du json valide !!!"})
    rv = client.post(
        "/publish/static",
        data={"source_zip": (io.BytesIO(zip_bytes), "source.zip")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode().lower()
    assert "invalide" in html or "erreur" in html


# ── JSON non-objet (tableau) ──────────────────────────────────────────────────

def test_publish_static_json_array_returns_error(client) -> None:
    zip_bytes = _make_zip({"publication_config.json": b"[1, 2, 3]"})
    rv = client.post(
        "/publish/static",
        data={"source_zip": (io.BytesIO(zip_bytes), "source.zip")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode().lower()
    assert "objet" in html or "erreur" in html


# ── Entrée dangereuse dans le ZIP ─────────────────────────────────────────────

def test_publish_static_dangerous_zip_entry_is_refused(client) -> None:
    cfg = _pub_config()
    zip_bytes = _make_zip({
        "publication_config.json": json.dumps(cfg),
        "../secret.txt": "contenu_secret_confidentiel",
    })
    rv = client.post(
        "/publish/static",
        data={"source_zip": (io.BytesIO(zip_bytes), "source.zip")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    assert "contenu_secret_confidentiel" not in rv.data.decode()


# ── Traversée de chemin dans le JSON ─────────────────────────────────────────

def test_publish_static_path_traversal_in_json_is_refused(client) -> None:
    cfg = _pub_config(dramatic_path="../../etc/passwd")
    zip_bytes = _make_zip({"publication_config.json": json.dumps(cfg)})
    rv = client.post(
        "/publish/static",
        data={"source_zip": (io.BytesIO(zip_bytes), "source.zip")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode().lower()
    assert "erreur" in html or "chemin" in html or "invalide" in html


def test_publish_static_absolute_path_in_json_is_refused(client) -> None:
    cfg = _pub_config(dramatic_path="/etc/passwd")
    zip_bytes = _make_zip({"publication_config.json": json.dumps(cfg)})
    rv = client.post(
        "/publish/static",
        data={"source_zip": (io.BytesIO(zip_bytes), "source.zip")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    html = rv.data.decode().lower()
    assert "erreur" in html or "chemin" in html or "invalide" in html


# ── output_dir du JSON est ignoré ─────────────────────────────────────────────

def test_publish_static_output_dir_from_json_is_replaced(client, monkeypatch) -> None:
    captured: dict = {}

    class _FakeService:
        def prepare_dialog_config_for_publication(self, config):
            from ets.application.editorial_notice_import.service import PreparedPublicationConfig
            captured["output_dir"] = config.output_dir
            return PreparedPublicationConfig(config=config)

    def _fake_request_from_config(config):
        raise ValueError("arrêt anticipé pour vérifier output_dir")

    monkeypatch.setattr("ets.web.publication_routes.EditorialNoticeImportService", _FakeService)
    monkeypatch.setattr(
        "ets.web.publication_routes.site_publication_request_from_dialog_config",
        _fake_request_from_config,
    )

    cfg = _pub_config(output_dir="C:/Windows/System32/evil_dir")
    zip_bytes = _make_zip({
        "publication_config.json": json.dumps(cfg),
        "dramatic/britannicus.xml": _DUMMY_XML,
    })
    client.post(
        "/publish/static",
        data={"source_zip": (io.BytesIO(zip_bytes), "source.zip")},
        content_type="multipart/form-data",
    )

    output_dir = captured.get("output_dir")
    assert output_dir is not None
    assert "evil_dir" not in str(output_dir)
    assert "System32" not in str(output_dir)


# ── build_latex_pdf forcé à False ─────────────────────────────────────────────

def test_publish_static_build_latex_pdf_forced_to_false(client, monkeypatch) -> None:
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

    cfg = _pub_config(build_latex_pdf=True)
    zip_bytes = _make_zip({
        "publication_config.json": json.dumps(cfg),
        "dramatic/britannicus.xml": _DUMMY_XML,
    })
    client.post(
        "/publish/static",
        data={"source_zip": (io.BytesIO(zip_bytes), "source.zip")},
        content_type="multipart/form-data",
    )

    assert captured.get("build_latex_pdf") is False


# ── Pipeline complet (mocks) ──────────────────────────────────────────────────

def test_publish_static_pipeline_calls_all_services_and_returns_zip(
    client, monkeypatch, tmp_path
) -> None:
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
        (site_dir / "index.html").write_text("<html>site généré</html>", encoding="utf-8")
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

    cfg = _pub_config()
    zip_bytes = _make_zip({
        "publication_config.json": json.dumps(cfg),
        "dramatic/britannicus.xml": _DUMMY_XML,
    })
    rv = client.post(
        "/publish/static",
        data={"source_zip": (io.BytesIO(zip_bytes), "source.zip")},
        content_type="multipart/form-data",
    )

    assert rv.status_code == 200
    assert "zip" in rv.content_type.lower()
    assert "prepare" in calls
    assert "request_from_config" in calls
    assert "build" in calls

    with zipfile.ZipFile(io.BytesIO(rv.data)) as zf:
        assert "index.html" in zf.namelist()


# ── Isolation — pas de Tkinter ────────────────────────────────────────────────

def test_publication_blueprint_does_not_import_tkinter() -> None:
    web_dir = Path(__file__).parents[2] / "src" / "ets" / "web"
    for py_file in web_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "tkinter" not in content, f"tkinter importé dans {py_file.name}"
