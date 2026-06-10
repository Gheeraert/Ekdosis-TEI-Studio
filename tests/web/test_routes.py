"""Tests for ets.web routes (Flask test client)."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest

from ets.web import create_app


# ── Helpers ───────────────────────────────────────────────────────────────────

def _minimal_config_json(n_witnesses: int = 2) -> str:
    temoins = [
        {"abbr": chr(65 + i), "year": str(1670 + i), "desc": f"Témoin {chr(65 + i)}"}
        for i in range(n_witnesses)
    ]
    return json.dumps({
        "Prénom de l'auteur": "Jean",
        "Nom de l'auteur": "Racine",
        "Titre de la pièce": "Test",
        "Prénom de l'éditeur scientifique": "",
        "Nom de l'éditeur scientifique": "Editeur",
        "Prénom du transcripteur": "",
        "Nom du transcripteur": "",
        "Temoins": temoins,
    })


def _valid_text(n_witnesses: int = 2) -> str:
    """Minimal valid ETS transcription for n_witnesses witnesses."""
    lines: list[str] = []
    lines += ["####ACTE I####"] * n_witnesses
    lines += [""]
    lines += ["###SCENE I###"] * n_witnesses
    lines += [""]
    lines += ["#ORESTE.#"] * n_witnesses
    lines += [""]
    lines += ["Je parle."] * n_witnesses
    return "\n".join(lines)


def _invalid_text_single_reading() -> str:
    """One reading per block — invalid for a multi-witness config."""
    return "\n".join([
        "####ACTE I####",
        "",
        "###SCENE I###",
        "",
        "#ORESTE.#",
        "",
        "Je parle.",
    ])


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def client():
    app = create_app(testing=True)
    with app.test_client() as c:
        yield c


# ── GET / ─────────────────────────────────────────────────────────────────────

def test_index_returns_200(client) -> None:
    rv = client.get("/")
    assert rv.status_code == 200


def test_index_contains_form(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    assert "<form" in html
    assert 'name="transcription"' in html
    assert 'name="config_json"' in html


# ── POST /validate ────────────────────────────────────────────────────────────

def test_validate_with_empty_transcription_returns_error(client) -> None:
    rv = client.post("/validate", data={
        "config_json": _minimal_config_json(),
        "transcription": "",
    })
    assert rv.status_code == 200
    assert "vide" in rv.data.decode().lower()


def test_validate_with_whitespace_only_transcription_returns_error(client) -> None:
    rv = client.post("/validate", data={
        "config_json": _minimal_config_json(),
        "transcription": "   \n\t  ",
    })
    assert rv.status_code == 200
    assert "vide" in rv.data.decode().lower()


def test_generate_with_whitespace_only_transcription_returns_error(client) -> None:
    rv = client.post("/generate", data={
        "config_json": _minimal_config_json(),
        "transcription": "   \n\t  ",
    })
    assert rv.status_code == 200
    assert "vide" in rv.data.decode().lower()


def test_validate_with_invalid_config_json_returns_error(client) -> None:
    rv = client.post("/validate", data={
        "config_json": "{ pas du json }",
        "transcription": "quelque chose",
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "invalide" in html.lower() or "erreur" in html.lower()


def test_validate_with_invalid_text_returns_diagnostics(client) -> None:
    rv = client.post("/validate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _invalid_text_single_reading(),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    # Either errors in the diagnostics table or a global failure message
    assert "ERROR" in html or "error" in html.lower()


def test_validate_with_valid_text_shows_success(client) -> None:
    rv = client.post("/validate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "success" in html or "successful" in html.lower() or "Validation" in html


def test_validate_preserves_form_values(client) -> None:
    config = _minimal_config_json()
    rv = client.post("/validate", data={
        "config_json": config,
        "transcription": "mon texte",
    })
    html = rv.data.decode()
    assert "mon texte" in html


# ── POST /generate ────────────────────────────────────────────────────────────

def test_generate_with_empty_transcription_returns_error(client) -> None:
    rv = client.post("/generate", data={
        "config_json": _minimal_config_json(),
        "transcription": "",
    })
    assert rv.status_code == 200
    assert "vide" in rv.data.decode().lower()


def test_generate_with_valid_text_returns_tei(client) -> None:
    rv = client.post("/generate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "TEI XML" in html
    # TEI content is HTML-escaped in the <pre> block
    assert "&lt;?xml" in html or "&lt;TEI" in html


def test_generate_with_valid_text_returns_html_preview(client) -> None:
    rv = client.post("/generate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Aperçu HTML" in html


def test_generate_with_form_fields_instead_of_json(client) -> None:
    rv = client.post("/generate", data={
        "config_json": "",
        "titre": "AndromaqueTest",
        "auteur_prenom": "Jean",
        "auteur_nom": "Racine",
        "editeur_prenom": "",
        "editeur_nom": "Ed",
        "transcripteur_prenom": "",
        "transcripteur_nom": "",
        "temoins_json": json.dumps([
            {"abbr": "A", "year": "1670", "desc": "A"},
            {"abbr": "B", "year": "1671", "desc": "B"},
        ]),
        "temoin_reference": "A",
        "transcription": _valid_text(n_witnesses=2),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "TEI XML" in html


# ── castlist_text ─────────────────────────────────────────────────────────────

def _castlist_text_2witnesses() -> str:
    """Minimal valid castlist for 2 witnesses with speaker THESEE."""
    return "\n".join([
        "%%castlist%%",
        '%%cast id=thesee role="Thésée" aliases="THESEE"%%',
        "Thésée",
        "Thésée",
        "%%fin_cast%%",
        "%%fin_castlist%%",
    ])


def _text_with_thesee(n_witnesses: int = 2) -> str:
    """Minimal valid ETS transcription using THESEE as speaker."""
    lines: list[str] = []
    lines += ["####ACTE I####"] * n_witnesses
    lines += [""]
    lines += ["###SCENE I###"] * n_witnesses
    lines += [""]
    lines += ["#THESEE#"] * n_witnesses
    lines += [""]
    lines += ["Je parle."] * n_witnesses
    return "\n".join(lines)


def test_index_shows_castlist_text_field(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    assert 'name="castlist_text"' in html


def test_validate_without_castlist_text_keeps_current_behavior(client) -> None:
    rv = client.post("/validate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
        "castlist_text": "",
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Validation" in html


def test_validate_with_castlist_text_uses_castlist_device(client) -> None:
    rv = client.post("/validate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _text_with_thesee(n_witnesses=2),
        "castlist_text": _castlist_text_2witnesses(),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Validation" in html
    assert "ERROR" not in html


def test_generate_with_castlist_text_produces_dramatis_personae(client) -> None:
    rv = client.post("/generate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _text_with_thesee(n_witnesses=2),
        "castlist_text": _castlist_text_2witnesses(),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "TEI XML" in html
    assert "dramatis-personae" in html


def test_castlist_path_in_json_not_read_as_local_path(client) -> None:
    config = json.loads(_minimal_config_json(n_witnesses=2))
    config["castlist_path"] = "/etc/passwd"
    rv = client.post("/validate", data={
        "config_json": json.dumps(config),
        "transcription": _valid_text(n_witnesses=2),
        "castlist_text": "",
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Validation" in html or "vide" not in html.lower()


def test_no_permanent_file_created(client, tmp_path) -> None:
    import os
    before = set(os.listdir(tmp_path))
    client.post("/generate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _text_with_thesee(n_witnesses=2),
        "castlist_text": _castlist_text_2witnesses(),
    })
    after = set(os.listdir(tmp_path))
    assert before == after


# ── Isolation ─────────────────────────────────────────────────────────────────

def test_web_package_does_not_import_tkinter() -> None:
    web_dir = Path(__file__).parents[2] / "src" / "ets" / "web"
    for py_file in web_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "tkinter" not in content, f"tkinter trouvé dans {py_file.name}"


# ── Helpers ZIP ───────────────────────────────────────────────────────────────

def _make_zip(files: dict[str, str]) -> bytes:
    """Build an in-memory ZIP from a dict {name: text_content}."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


def _minimal_config_dict(title: str = "Britannicus") -> dict:
    return {
        "Prénom de l'auteur": "Jean",
        "Nom de l'auteur": "Racine",
        "Titre de la pièce": title,
        "Prénom de l'éditeur scientifique": "",
        "Nom de l'éditeur scientifique": "Editeur",
        "Prénom du transcripteur": "",
        "Nom du transcripteur": "",
        "Temoins": [
            {"abbr": "A", "year": "1670", "desc": "Édition princeps"},
            {"abbr": "B", "year": "1676", "desc": "Collective"},
        ],
    }


# ── POST /load — ZIP ──────────────────────────────────────────────────────────

def test_load_zip_fills_all_three_zones(client) -> None:
    cfg = _minimal_config_dict()
    cfg["transcription_path"] = "britannicus.txt"
    cfg["castlist_path"] = "britannicus_castlist.txt"
    zip_bytes = _make_zip({
        "britannicus.json": json.dumps(cfg),
        "britannicus.txt": "Contenu transcription",
        "britannicus_castlist.txt": "%%castlist%%\n%%fin_castlist%%",
    })
    rv = client.post("/load", data={
        "package_file": (io.BytesIO(zip_bytes), "britannicus.zip"),
    }, content_type="multipart/form-data")
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Contenu transcription" in html
    assert "%%castlist%%" in html
    assert "Britannicus" in html


def test_load_zip_json_only_fills_config(client) -> None:
    cfg = _minimal_config_dict()
    zip_bytes = _make_zip({"britannicus.json": json.dumps(cfg)})
    rv = client.post("/load", data={
        "package_file": (io.BytesIO(zip_bytes), "britannicus.zip"),
    }, content_type="multipart/form-data")
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Britannicus" in html


def test_load_zip_uses_transcription_path_from_json(client) -> None:
    cfg = _minimal_config_dict()
    cfg["transcription_path"] = "custom_trans.txt"
    zip_bytes = _make_zip({
        "britannicus.json": json.dumps(cfg),
        "custom_trans.txt": "Texte de la pièce",
    })
    rv = client.post("/load", data={
        "package_file": (io.BytesIO(zip_bytes), "britannicus.zip"),
    }, content_type="multipart/form-data")
    assert rv.status_code == 200
    assert "Texte de la pièce" in rv.data.decode()


def test_load_zip_uses_castlist_path_from_json(client) -> None:
    cfg = _minimal_config_dict()
    cfg["castlist_path"] = "ma_castlist.txt"
    zip_bytes = _make_zip({
        "britannicus.json": json.dumps(cfg),
        "ma_castlist.txt": "%%castlist%%\n%%fin_castlist%%",
    })
    rv = client.post("/load", data={
        "package_file": (io.BytesIO(zip_bytes), "britannicus.zip"),
    }, content_type="multipart/form-data")
    assert rv.status_code == 200
    assert "%%castlist%%" in rv.data.decode()


def test_load_zip_fallback_names_when_paths_absent(client) -> None:
    cfg = _minimal_config_dict()
    zip_bytes = _make_zip({
        "britannicus.json": json.dumps(cfg),
        "britannicus.txt": "Fallback transcription",
        "britannicus_castlist.txt": "%%castlist%%\n%%fin_castlist%%",
    })
    rv = client.post("/load", data={
        "package_file": (io.BytesIO(zip_bytes), "britannicus.zip"),
    }, content_type="multipart/form-data")
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Fallback transcription" in html
    assert "%%castlist%%" in html


def test_load_zip_no_json_returns_error(client) -> None:
    zip_bytes = _make_zip({"britannicus.txt": "juste du texte"})
    rv = client.post("/load", data={
        "package_file": (io.BytesIO(zip_bytes), "britannicus.zip"),
    }, content_type="multipart/form-data")
    assert rv.status_code == 200
    html = rv.data.decode().lower()
    assert "json" in html and ("aucun" in html or "erreur" in html)


def test_load_zip_multiple_json_returns_error(client) -> None:
    cfg = _minimal_config_dict()
    zip_bytes = _make_zip({
        "a.json": json.dumps(cfg),
        "b.json": json.dumps(cfg),
    })
    rv = client.post("/load", data={
        "package_file": (io.BytesIO(zip_bytes), "britannicus.zip"),
    }, content_type="multipart/form-data")
    assert rv.status_code == 200
    html = rv.data.decode().lower()
    assert "plusieurs" in html or "erreur" in html


def test_load_zip_rejects_absolute_path(client) -> None:
    cfg = _minimal_config_dict()
    cfg["transcription_path"] = "/etc/passwd"
    zip_bytes = _make_zip({
        "britannicus.json": json.dumps(cfg),
        "/etc/passwd": "root:x:0:0",
    })
    rv = client.post("/load", data={
        "package_file": (io.BytesIO(zip_bytes), "britannicus.zip"),
    }, content_type="multipart/form-data")
    assert rv.status_code == 200
    assert "root:x:0:0" not in rv.data.decode()


def test_load_zip_rejects_path_traversal(client) -> None:
    cfg = _minimal_config_dict()
    cfg["transcription_path"] = "../secret.txt"
    zip_bytes = _make_zip({
        "britannicus.json": json.dumps(cfg),
        "../secret.txt": "données secrètes",
    })
    rv = client.post("/load", data={
        "package_file": (io.BytesIO(zip_bytes), "britannicus.zip"),
    }, content_type="multipart/form-data")
    assert rv.status_code == 200
    assert "données secrètes" not in rv.data.decode()


# ── POST /load — imports individuels ─────────────────────────────────────────

def test_load_individual_config_file(client) -> None:
    cfg = _minimal_config_dict()
    rv = client.post("/load", data={
        "config_file": (io.BytesIO(json.dumps(cfg).encode()), "test.json"),
    }, content_type="multipart/form-data")
    assert rv.status_code == 200
    assert "Britannicus" in rv.data.decode()


def test_load_individual_transcription_file(client) -> None:
    rv = client.post("/load", data={
        "transcription_file": (io.BytesIO(b"Mon texte de transcription"), "trans.txt"),
    }, content_type="multipart/form-data")
    assert rv.status_code == 200
    assert "Mon texte de transcription" in rv.data.decode()


def test_load_individual_castlist_file(client) -> None:
    rv = client.post("/load", data={
        "castlist_file": (io.BytesIO(b"%%castlist%%\n%%fin_castlist%%"), "castlist.txt"),
    }, content_type="multipart/form-data")
    assert rv.status_code == 200
    assert "%%castlist%%" in rv.data.decode()


# ── POST /download/package ────────────────────────────────────────────────────

def test_download_package_returns_zip(client) -> None:
    rv = client.post("/download/package", data={
        "config_json": _minimal_config_json(),
        "transcription": _valid_text(n_witnesses=2),
        "castlist_text": "",
    })
    assert rv.status_code == 200
    assert rv.content_type == "application/zip" or "zip" in rv.content_type


def test_download_package_zip_contains_standalone_json(client) -> None:
    rv = client.post("/download/package", data={
        "config_json": _minimal_config_json(),
        "transcription": _valid_text(n_witnesses=2),
        "castlist_text": "",
    })
    assert rv.status_code == 200
    with zipfile.ZipFile(io.BytesIO(rv.data)) as zf:
        json_names = [n for n in zf.namelist() if n.endswith(".json")]
        assert len(json_names) == 1
        raw = json.loads(zf.read(json_names[0]))
        assert "Titre de la pièce" in raw
        assert "Temoins" in raw
        assert raw.get("Titre de la pièce") == "Test"


def test_download_package_zip_contains_transcription(client) -> None:
    rv = client.post("/download/package", data={
        "config_json": _minimal_config_json(),
        "transcription": "Mon texte unique",
        "castlist_text": "",
    })
    assert rv.status_code == 200
    with zipfile.ZipFile(io.BytesIO(rv.data)) as zf:
        txt_names = [n for n in zf.namelist() if n.endswith(".txt") and "_castlist" not in n]
        assert len(txt_names) == 1
        assert zf.read(txt_names[0]).decode() == "Mon texte unique"


def test_download_package_zip_contains_castlist(client) -> None:
    rv = client.post("/download/package", data={
        "config_json": _minimal_config_json(),
        "transcription": "",
        "castlist_text": "%%castlist%%\n%%fin_castlist%%",
    })
    assert rv.status_code == 200
    with zipfile.ZipFile(io.BytesIO(rv.data)) as zf:
        castlist_names = [n for n in zf.namelist() if "_castlist" in n]
        assert len(castlist_names) == 1
        assert "%%castlist%%" in zf.read(castlist_names[0]).decode()


def test_download_package_json_has_relative_paths(client) -> None:
    rv = client.post("/download/package", data={
        "config_json": _minimal_config_json(),
        "transcription": "du texte",
        "castlist_text": "%%castlist%%\n%%fin_castlist%%",
    })
    assert rv.status_code == 200
    with zipfile.ZipFile(io.BytesIO(rv.data)) as zf:
        json_names = [n for n in zf.namelist() if n.endswith(".json")]
        raw = json.loads(zf.read(json_names[0]))
        assert "transcription_path" in raw
        assert "castlist_path" in raw
        assert not raw["transcription_path"].startswith("/")
        assert not raw["castlist_path"].startswith("/")


# ── POST /download/config ─────────────────────────────────────────────────────

def test_download_config_returns_standalone_json(client) -> None:
    rv = client.post("/download/config", data={
        "config_json": _minimal_config_json(),
    })
    assert rv.status_code == 200
    raw = json.loads(rv.data)
    assert "Titre de la pièce" in raw
    assert "Temoins" in raw


def test_download_config_has_french_keys(client) -> None:
    rv = client.post("/download/config", data={
        "config_json": _minimal_config_json(),
    })
    assert rv.status_code == 200
    raw = json.loads(rv.data)
    assert "Prénom de l'auteur" in raw or "Nom de l'auteur" in raw


# ── POST /download/transcription ─────────────────────────────────────────────

def test_download_transcription_returns_text(client) -> None:
    rv = client.post("/download/transcription", data={
        "config_json": _minimal_config_json(),
        "transcription": "Contenu de la transcription",
    })
    assert rv.status_code == 200
    assert "Contenu de la transcription" in rv.data.decode()


# ── POST /download/castlist ───────────────────────────────────────────────────

def test_download_castlist_returns_text(client) -> None:
    rv = client.post("/download/castlist", data={
        "config_json": _minimal_config_json(),
        "castlist_text": "%%castlist%%\n%%fin_castlist%%",
    })
    assert rv.status_code == 200
    assert "%%castlist%%" in rv.data.decode()


# ── Stateless : pas de stockage permanent ─────────────────────────────────────

def test_load_zip_invalid_json_returns_error_not_500(client) -> None:
    zip_bytes = _make_zip({"britannicus.json": "{ pas du json valide !!!"})
    rv = client.post("/load", data={
        "package_file": (io.BytesIO(zip_bytes), "britannicus.zip"),
    }, content_type="multipart/form-data")
    assert rv.status_code == 200
    html = rv.data.decode().lower()
    assert "invalide" in html or "erreur" in html


def test_download_package_removes_stale_paths_when_content_empty(client) -> None:
    cfg = _minimal_config_dict()
    cfg["transcription_path"] = "ancien_chemin.txt"
    cfg["castlist_path"] = "ancienne_castlist.txt"
    rv = client.post("/download/package", data={
        "config_json": json.dumps(cfg),
        "transcription": "",
        "castlist_text": "",
    })
    assert rv.status_code == 200
    with zipfile.ZipFile(io.BytesIO(rv.data)) as zf:
        json_names = [n for n in zf.namelist() if n.endswith(".json")]
        raw = json.loads(zf.read(json_names[0]))
        assert "transcription_path" not in raw
        assert "castlist_path" not in raw


def test_load_zip_no_permanent_file(client, tmp_path) -> None:
    import os
    cfg = _minimal_config_dict()
    zip_bytes = _make_zip({"test.json": json.dumps(cfg)})
    before = set(os.listdir(tmp_path))
    client.post("/load", data={
        "package_file": (io.BytesIO(zip_bytes), "test.zip"),
    }, content_type="multipart/form-data")
    assert set(os.listdir(tmp_path)) == before


# ── Transcription annotée ────────────────────────────────────────────────────

def test_validate_invalid_shows_annotated_source_section(client) -> None:
    rv = client.post("/validate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _invalid_text_single_reading(),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "annotated-source" in html


def test_validate_annotated_lines_have_stable_ids(client) -> None:
    rv = client.post("/validate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _invalid_text_single_reading(),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert 'id="src-line-1"' in html
    assert 'id="src-line-2"' in html


def test_validate_diagnostic_table_links_to_annotated_line(client) -> None:
    rv = client.post("/validate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _invalid_text_single_reading(),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    import re
    assert re.search(r'href="#src-line-\d+"', html), "Aucun lien vers une ligne annotée"


def test_validate_faulty_line_has_error_class(client) -> None:
    rv = client.post("/validate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _invalid_text_single_reading(),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "source-line-error" in html or "source-line-warning" in html


def test_generate_valid_shows_annotated_source(client) -> None:
    rv = client.post("/generate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "annotated-source" in html
    assert 'id="src-line-1"' in html


def test_validate_returns_200(client) -> None:
    rv = client.post("/validate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
    })
    assert rv.status_code == 200


def test_generate_returns_200(client) -> None:
    rv = client.post("/generate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
    })
    assert rv.status_code == 200


def test_form_fields_unchanged(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    assert 'name="transcription"' in html
    assert 'name="config_json"' in html
    assert 'name="castlist_text"' in html


# ── Interface à onglets ───────────────────────────────────────────────────────

def test_index_has_five_tabs(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    assert "Import" in html
    assert "Configuration manuelle" in html
    assert "Saisie" in html
    assert "Résultats" in html
    assert "Export" in html


def test_index_config_tab_is_config_manuelle(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    import re
    tab_buttons = re.findall(r'<button[^>]+class="tab-button"[^>]*>([^<]+)</button>', html)
    assert "Configuration manuelle" in tab_buttons
    assert "Configuration" not in [t for t in tab_buttons if t != "Configuration manuelle"]


def test_index_old_tab_name_absent(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    import re
    tab_buttons = re.findall(r'<button[^>]+class="tab-button"[^>]*>([^<]+)</button>', html)
    assert "Import / Export" not in tab_buttons


def test_index_tab_buttons_are_not_submit(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    # Les boutons d'onglet portent class="tab-button" et type="button"
    assert 'class="tab-button"' in html
    # Aucun bouton d'onglet ne doit être type="submit"
    import re
    tab_buttons = re.findall(r'<button[^>]+class="tab-button"[^>]*>', html)
    assert tab_buttons, "Aucun bouton d'onglet trouvé"
    for btn in tab_buttons:
        assert 'type="submit"' not in btn, f"Bouton d'onglet submit trouvé : {btn}"


def test_index_has_required_fields(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    for field in [
        'name="package_file"',
        'name="config_file"',
        'name="transcription_file"',
        'name="castlist_file"',
        'name="config_json"',
        'name="transcription"',
        'name="castlist_text"',
    ]:
        assert field in html, f"Champ manquant : {field}"


def test_index_has_required_formactions(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    for route in ["/load", "/generate", "/download/package",
                  "/download/config", "/download/transcription", "/download/castlist"]:
        assert route in html, f"Route manquante : {route}"


def test_index_single_form(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    assert html.count("<form") == 1, "Il doit y avoir exactement un seul <form>"


# ── Onglet actif selon le contexte ────────────────────────────────────────────

def test_index_active_tab_is_import(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    assert 'data-active-tab="tab-import"' in html


def test_load_success_active_tab_saisie(client) -> None:
    cfg = _minimal_config_dict()
    zip_bytes = _make_zip({"test.json": json.dumps(cfg)})
    rv = client.post("/load", data={
        "package_file": (io.BytesIO(zip_bytes), "test.zip"),
    }, content_type="multipart/form-data")
    assert rv.status_code == 200
    html = rv.data.decode()
    assert 'data-active-tab="tab-saisie"' in html


def test_load_error_active_tab_import(client) -> None:
    zip_bytes = _make_zip({"no_json.txt": "juste du texte"})
    rv = client.post("/load", data={
        "package_file": (io.BytesIO(zip_bytes), "test.zip"),
    }, content_type="multipart/form-data")
    assert rv.status_code == 200
    html = rv.data.decode()
    assert 'data-active-tab="tab-import"' in html


def test_validate_active_tab_resultats(client) -> None:
    rv = client.post("/validate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
    })
    assert rv.status_code == 200
    assert 'data-active-tab="tab-resultats"' in rv.data.decode()


def test_generate_active_tab_resultats(client) -> None:
    rv = client.post("/generate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
    })
    assert rv.status_code == 200
    assert 'data-active-tab="tab-resultats"' in rv.data.decode()


# ── Boutons d'export dans l'onglet Export supplémentaire ─────────────────────

def test_export_tab_has_all_download_buttons(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    for route in ["/download/package", "/download/config",
                  "/download/transcription", "/download/castlist"]:
        assert route in html, f"formaction manquant : {route}"


def test_import_fields_still_present(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    for field in ["name=\"package_file\"", "name=\"config_file\"",
                  "name=\"transcription_file\"", "name=\"castlist_file\""]:
        assert field in html, f"Champ d'import manquant : {field}"


# ── Onglet Export renommé ─────────────────────────────────────────────────────

def test_index_tab_export_not_supplementaire(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    import re
    tab_buttons = re.findall(r'<button[^>]+class="tab-button"[^>]*>([^<]+)</button>', html)
    assert "Export" in tab_buttons
    assert "Export supplémentaire" not in tab_buttons


# ── Bouton contextuel dans l'onglet Résultats ─────────────────────────────────

def test_validate_ok_shows_generate_button(client) -> None:
    rv = client.post("/validate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Générer TEI + HTML + LaTeX" in html
    assert 'formaction="/generate"' in html


def test_validate_error_shows_back_to_saisie_button(client) -> None:
    rv = client.post("/validate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _invalid_text_single_reading(),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Retour à la saisie" in html


def test_validate_error_back_button_is_not_submit(client) -> None:
    rv = client.post("/validate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _invalid_text_single_reading(),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    import re
    buttons = re.findall(r'<button([^>]*)>Retour à la saisie</button>', html)
    assert buttons, "Bouton 'Retour à la saisie' non trouvé"
    for attrs in buttons:
        assert 'type="submit"' not in attrs


def test_generate_ok_no_contextual_action(client) -> None:
    rv = client.post("/generate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "TEI XML" in html
    # Après génération, le bouton "Générer" ne réapparaît pas dans result-actions
    import re
    result_actions_blocks = re.findall(r'<div class="result-actions">(.*?)</div>', html, re.DOTALL)
    for block in result_actions_blocks:
        assert 'formaction="/generate"' not in block


def test_generate_ok_shows_export_button(client) -> None:
    rv = client.post("/generate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "Exporter les résultats" in html


def test_generate_ok_export_button_is_not_submit(client) -> None:
    rv = client.post("/generate", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    import re
    buttons = re.findall(r'<button([^>]*)>Exporter les résultats</button>', html)
    assert buttons, "Bouton 'Exporter les résultats' non trouvé"
    for attrs in buttons:
        assert 'type="submit"' not in attrs


def test_export_routes_still_present(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    for route in ["/download/package", "/download/config",
                  "/download/transcription", "/download/castlist"]:
        assert route in html, f"Route d'export manquante : {route}"


# ── Sous-titre et onglet À propos d'ETS ──────────────────────────────────────

def test_index_new_subtitle_present(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    assert "Plate-forme de saisie, d'encodage et de visualisation pour l'édition critique du théâtre classique" in html


def test_index_old_subtitle_absent(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    assert "Interface web minimale" not in html


def test_index_has_apropos_tab(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    assert "À propos d'ETS" in html


def test_index_existing_tabs_still_present(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    for label in ["Import", "Configuration manuelle", "Saisie", "Résultats", "Export"]:
        assert label in html, f"Onglet manquant : {label}"


# ── Page À propos — contenu éditorial ────────────────────────────────────────

def test_apropos_title(client) -> None:
    rv = client.get("/about")
    assert "À propos d'Ekdosis-TEI Studio" in rv.data.decode()


def test_apropos_tony_gheeraert(client) -> None:
    rv = client.get("/about")
    assert "Tony Gheeraert" in rv.data.decode()


def test_apropos_marcello_vitali_rosati(client) -> None:
    rv = client.get("/about")
    assert "Marcello Vitali-Rosati" in rv.data.decode()


def test_apropos_clara_matos(client) -> None:
    rv = client.get("/about")
    assert "Clara Matos" in rv.data.decode()


def test_apropos_robert_alessi(client) -> None:
    rv = client.get("/about")
    assert "Robert Alessi" in rv.data.decode()


# ── Pied de page ─────────────────────────────────────────────────────────────

def test_footer_github_link(client) -> None:
    rv = client.get("/")
    assert "https://github.com/Gheeraert/Ekdosis-TEI-Studio" in rv.data.decode()


def test_footer_propulse_par(client) -> None:
    rv = client.get("/")
    html = rv.data.decode("utf-8")
    assert "Propulsé par" in html
    assert "Ekdosis-TEI Studio" in html


# ── Mode d'emploi Export ──────────────────────────────────────────────────────

def test_export_mode_emploi_index_html(client) -> None:
    rv = client.get("/")
    assert "index.html" in rv.data.decode()


# ── Routes d'export inchangées ────────────────────────────────────────────────

def test_export_routes_unchanged(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    for route in ["/download/package", "/download/config",
                  "/download/transcription", "/download/castlist"]:
        assert route in html, f"Route d'export manquante : {route}"


def test_all_tabs_present(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    for label in ["Import", "Configuration manuelle", "Saisie",
                  "Résultats", "Export", "À propos d'ETS"]:
        assert label in html, f"Onglet manquant : {label}"


# ── Onglet Protocole de transcription ────────────────────────────────────────

def test_protocole_tab_present(client) -> None:
    rv = client.get("/")
    assert "Protocole de transcription" in rv.data.decode()


def test_protocole_sections_present(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    for section in ["Structure dramatique", "Variantes, lacunes",
                    "Vers partagés", "Didascalies", "Chœurs",
                    "Strophes et métrique", "Dramatis personae"]:
        assert section in html, f"Section manquante : {section}"


def test_protocole_castlist_markers_present(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    assert "%%castlist%%" in html
    assert "%%fin_castlist%%" in html


def test_protocole_didascalie_types_present(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    for typ in ["SPC", "ASP", "TMP", "EVT", "SET", "PROX", "ATT", "VOI"]:
        assert typ in html, f"Type de didascalie manquant : {typ}"


def test_protocole_form_fields_unchanged(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    assert 'name="transcription"' in html
    assert 'name="config_json"' in html
    assert 'name="castlist_text"' in html


# ── Onglet Export — deux sections ────────────────────────────────────────────

def test_export_tab_has_two_sections(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    assert "Exporter le travail courant" in html
    assert "Exporter les fichiers générés" in html


def test_export_tab_old_routes_still_present(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    for route in ["/download/package", "/download/config",
                  "/download/transcription", "/download/castlist"]:
        assert route in html, f"Ancienne route manquante : {route}"


def test_export_tab_new_routes_present(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    for route in ["/download/generated/tei", "/download/generated/html",
                  "/download/generated/ekdosis", "/download/generated/package"]:
        assert route in html, f"Nouvelle route manquante : {route}"


# ── POST /download/generated/* ────────────────────────────────────────────────

def test_download_generated_tei_returns_xml(client) -> None:
    rv = client.post("/download/generated/tei", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
    })
    assert rv.status_code == 200
    content = rv.data.decode("utf-8")
    assert "<?xml" in content or "<TEI" in content


def test_download_generated_html_returns_html(client) -> None:
    rv = client.post("/download/generated/html", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
    })
    assert rv.status_code == 200
    content = rv.data.decode("utf-8")
    assert "<html" in content.lower() or "<!doctype" in content.lower() or "<body" in content.lower()


def test_download_generated_ekdosis_returns_200(client) -> None:
    rv = client.post("/download/generated/ekdosis", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
    })
    assert rv.status_code == 200


def test_download_generated_package_returns_zip_with_xml(client) -> None:
    rv = client.post("/download/generated/package", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
    })
    assert rv.status_code == 200
    assert "zip" in rv.content_type
    with zipfile.ZipFile(io.BytesIO(rv.data)) as zf:
        names = zf.namelist()
        assert any(n.endswith(".xml") for n in names), f"Pas de .xml dans le ZIP : {names}"
        assert any(n.endswith(".html") for n in names), f"Pas de .html dans le ZIP : {names}"


def test_download_generated_tei_with_empty_transcription_returns_error_page(client) -> None:
    rv = client.post("/download/generated/tei", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": "",
    })
    assert rv.status_code == 200
    html = rv.data.decode()
    assert "vide" in html.lower() or "erreur" in html.lower()


def test_download_generated_existing_exports_unchanged(client) -> None:
    rv = client.post("/download/package", data={
        "config_json": _minimal_config_json(n_witnesses=2),
        "transcription": _valid_text(n_witnesses=2),
        "castlist_text": "",
    })
    assert rv.status_code == 200
    assert "zip" in rv.content_type


# ── GET /about ────────────────────────────────────────────────────────────────

def test_about_returns_200(client) -> None:
    rv = client.get("/about")
    assert rv.status_code == 200


def test_main_nav_contains_about_link(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    assert 'href="/about"' in html
    assert "À propos d'ETS" in html


def test_about_page_contains_editorial_content(client) -> None:
    rv = client.get("/about")
    html = rv.data.decode()
    assert "Ekdosis-TEI Studio" in html
    assert "Tony Gheeraert" in html


def test_index_does_not_contain_apropos_tab(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    assert 'data-tab="tab-apropos"' not in html


def test_index_internal_tabs_present(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    assert "Import" in html
    assert "Configuration manuelle" in html
    assert "Saisie" in html
    assert "Résultats" in html
    assert "Export" in html
    assert "Protocole de transcription" in html
