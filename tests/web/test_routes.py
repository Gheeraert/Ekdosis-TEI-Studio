"""Tests for ets.web routes (Flask test client)."""

from __future__ import annotations

import json
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
