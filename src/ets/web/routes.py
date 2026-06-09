from __future__ import annotations

import dataclasses
import json
import tempfile
from contextlib import contextmanager
from pathlib import Path

from flask import Blueprint, render_template, request

from ets.application.services import (
    generate_ekdosis_from_tei,
    generate_html_preview_from_tei,
    generate_tei_from_text,
    validate_text,
)
from ets.domain import EditionConfig

from .config_builder import config_from_dict, config_from_form

bp = Blueprint("web", __name__)

_FORM_KEYS = (
    "config_json",
    "titre",
    "auteur_prenom",
    "auteur_nom",
    "editeur_prenom",
    "editeur_nom",
    "transcripteur_prenom",
    "transcripteur_nom",
    "temoins_json",
    "temoin_reference",
    "transcription",
    "castlist_text",
)


def _form_data(req) -> dict[str, str]:
    return {k: req.form.get(k, "") for k in _FORM_KEYS}


def _empty_form() -> dict[str, str]:
    return dict.fromkeys(_FORM_KEYS, "")


def _build_config(form):
    config_json_raw = form.get("config_json", "").strip()
    if config_json_raw:
        try:
            raw = json.loads(config_json_raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON de configuration invalide : {exc}") from exc
        if not isinstance(raw, dict):
            raise ValueError("Le JSON de configuration doit être un objet (accolades {…}).")
        return config_from_dict(raw)
    return config_from_form(form)


@contextmanager
def _castlist_tempdir(castlist_text: str, config: EditionConfig):
    """Yield (config, base_dir): temp dir with castlist.txt when text is non-empty, else (config, None)."""
    if not castlist_text.strip():
        yield config, None
        return
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "castlist.txt").write_text(castlist_text, encoding="utf-8")
        yield dataclasses.replace(config, castlist_path="castlist.txt"), tmpdir


@bp.get("/")
def index():
    return render_template("index.html", form=_empty_form())


@bp.post("/validate")
def validate():
    form = _form_data(request)
    try:
        config = _build_config(request.form)
    except ValueError as exc:
        return render_template("index.html", form=form, config_error=str(exc))

    text = request.form.get("transcription", "").strip()
    if not text:
        return render_template("index.html", form=form, config_error="La transcription est vide.")

    castlist_text = request.form.get("castlist_text", "")
    with _castlist_tempdir(castlist_text, config) as (cfg, base_dir):
        result = validate_text(text, cfg, castlist_base_dir=base_dir)
    return render_template("index.html", form=form, validation=result)


@bp.post("/generate")
def generate():
    form = _form_data(request)
    try:
        config = _build_config(request.form)
    except ValueError as exc:
        return render_template("index.html", form=form, config_error=str(exc))

    text = request.form.get("transcription", "").strip()
    if not text:
        return render_template("index.html", form=form, config_error="La transcription est vide.")

    castlist_text = request.form.get("castlist_text", "")
    with _castlist_tempdir(castlist_text, config) as (cfg, base_dir):
        tei_result = generate_tei_from_text(text, cfg, castlist_base_dir=base_dir)
    html_result = None
    ekdosis = None
    ekdosis_error = None

    if tei_result.ok and tei_result.tei_xml:
        html_result = generate_html_preview_from_tei(tei_result.tei_xml)
        try:
            ekdosis = generate_ekdosis_from_tei(tei_result.tei_xml)
        except Exception as exc:
            ekdosis_error = str(exc)

    return render_template(
        "index.html",
        form=form,
        tei_result=tei_result,
        html_result=html_result,
        ekdosis=ekdosis,
        ekdosis_error=ekdosis_error,
    )
