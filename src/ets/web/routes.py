from __future__ import annotations

import dataclasses
import io
import json
import re
import tempfile
import unicodedata
import zipfile
from contextlib import contextmanager
from pathlib import Path

from flask import Blueprint, current_app, render_template, request, send_file

from ets.application.services import (
    generate_ekdosis_from_tei,
    generate_html_preview_from_tei,
    generate_tei_from_text,
    validate_text,
)
from ets.domain import EditionConfig

from .config_builder import config_from_dict, config_from_form

bp = Blueprint("web", __name__)


def _make_slug(title: str) -> str:
    if not title or not title.strip():
        return "ets"
    normalized = unicodedata.normalize("NFD", title.strip())
    ascii_str = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_str.lower()).strip("_")
    return slug or "ets"


def _is_safe_zip_path(name: str) -> bool:
    if not name:
        return False
    if name.startswith("/") or name.startswith("\\"):
        return False
    if len(name) >= 2 and name[1] == ":":
        return False
    parts = name.replace("\\", "/").split("/")
    return ".." not in parts


def _build_export_json(form) -> dict:
    config_json_raw = form.get("config_json", "").strip()
    if config_json_raw:
        try:
            raw = json.loads(config_json_raw)
            if isinstance(raw, dict):
                return dict(raw)
        except json.JSONDecodeError:
            pass
    temoins_raw: list = []
    temoins_json_str = form.get("temoins_json", "").strip()
    if temoins_json_str:
        try:
            temoins_raw = json.loads(temoins_json_str)
        except json.JSONDecodeError:
            temoins_raw = []
    return {
        "Prénom de l'auteur": form.get("auteur_prenom", ""),
        "Nom de l'auteur": form.get("auteur_nom", ""),
        "Titre de la pièce": form.get("titre", ""),
        "Prénom de l'éditeur scientifique": form.get("editeur_prenom", ""),
        "Nom de l'éditeur scientifique": form.get("editeur_nom", ""),
        "Prénom du transcripteur": form.get("transcripteur_prenom", ""),
        "Nom du transcripteur": form.get("transcripteur_nom", ""),
        "Temoins": temoins_raw,
    }


def _title_from_raw(raw: dict, form) -> str:
    return (
        raw.get("Titre de la pièce", "")
        or form.get("titre", "")
    )


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

    raw_text = request.form.get("transcription", "")
    if not raw_text.strip():
        return render_template("index.html", form=form, config_error="La transcription est vide.")

    castlist_text = request.form.get("castlist_text", "")
    with _castlist_tempdir(castlist_text, config) as (cfg, base_dir):
        result = validate_text(raw_text, cfg, castlist_base_dir=base_dir)
    return render_template("index.html", form=form, validation=result)


@bp.post("/generate")
def generate():
    form = _form_data(request)
    try:
        config = _build_config(request.form)
    except ValueError as exc:
        return render_template("index.html", form=form, config_error=str(exc))

    raw_text = request.form.get("transcription", "")
    if not raw_text.strip():
        return render_template("index.html", form=form, config_error="La transcription est vide.")

    castlist_text = request.form.get("castlist_text", "")
    with _castlist_tempdir(castlist_text, config) as (cfg, base_dir):
        tei_result = generate_tei_from_text(raw_text, cfg, castlist_base_dir=base_dir)
    html_result = None
    ekdosis = None
    ekdosis_error = None

    if tei_result.ok and tei_result.tei_xml:
        html_result = generate_html_preview_from_tei(tei_result.tei_xml)
        try:
            ekdosis = generate_ekdosis_from_tei(tei_result.tei_xml)
        except Exception as exc:
            current_app.logger.exception("Erreur inattendue lors de la génération Ekdosis")
            ekdosis_error = str(exc)

    return render_template(
        "index.html",
        form=form,
        tei_result=tei_result,
        html_result=html_result,
        ekdosis=ekdosis,
        ekdosis_error=ekdosis_error,
    )


@bp.post("/load")
def load():
    form = dict(_form_data(request))
    load_error = None

    package_file = request.files.get("package_file")
    if package_file and package_file.filename:
        data = package_file.read()
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                names = zf.namelist()
                json_names = [
                    n for n in names
                    if n.lower().endswith(".json") and _is_safe_zip_path(n)
                ]
                if not json_names:
                    load_error = "Le ZIP ne contient aucun fichier JSON de configuration."
                elif len(json_names) > 1:
                    load_error = (
                        f"Le ZIP contient plusieurs fichiers JSON "
                        f"({', '.join(json_names)}). Il doit en contenir exactement un."
                    )
                else:
                    json_name = json_names[0]
                    try:
                        raw = json.loads(zf.read(json_name).decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        load_error = f"Le fichier JSON du ZIP est invalide : {exc}"
                        return render_template("index.html", form=form, load_error=load_error)
                    form["config_json"] = json.dumps(raw, ensure_ascii=False, indent=2)

                    stem = json_name.rsplit(".", 1)[0]

                    t_path = raw.get("transcription_path", "").strip()
                    if not t_path:
                        t_path = f"{stem}.txt"
                    if t_path and _is_safe_zip_path(t_path) and t_path in names:
                        form["transcription"] = zf.read(t_path).decode("utf-8")

                    c_path = raw.get("castlist_path", "").strip()
                    if not c_path:
                        c_path = f"{stem}_castlist.txt"
                    if c_path and _is_safe_zip_path(c_path) and c_path in names:
                        form["castlist_text"] = zf.read(c_path).decode("utf-8")
        except zipfile.BadZipFile:
            load_error = "Le fichier uploadé n'est pas un ZIP valide."
    else:
        config_file = request.files.get("config_file")
        if config_file and config_file.filename:
            form["config_json"] = config_file.read().decode("utf-8")

        transcription_file = request.files.get("transcription_file")
        if transcription_file and transcription_file.filename:
            form["transcription"] = transcription_file.read().decode("utf-8")

        castlist_file = request.files.get("castlist_file")
        if castlist_file and castlist_file.filename:
            form["castlist_text"] = castlist_file.read().decode("utf-8")

    return render_template("index.html", form=form, load_error=load_error)


@bp.post("/download/package")
def download_package():
    form = request.form
    raw = _build_export_json(form)
    slug = _make_slug(_title_from_raw(raw, form))
    transcription = form.get("transcription", "")
    castlist = form.get("castlist_text", "")

    if transcription.strip():
        raw["transcription_path"] = f"{slug}.txt"
    else:
        raw.pop("transcription_path", None)
    if castlist.strip():
        raw["castlist_path"] = f"{slug}_castlist.txt"
    else:
        raw.pop("castlist_path", None)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{slug}.json", json.dumps(raw, ensure_ascii=False, indent=2))
        if transcription.strip():
            zf.writestr(f"{slug}.txt", transcription)
        if castlist.strip():
            zf.writestr(f"{slug}_castlist.txt", castlist)
    buf.seek(0)

    return send_file(
        buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{slug}.zip",
    )


@bp.post("/download/config")
def download_config():
    form = request.form
    raw = _build_export_json(form)
    slug = _make_slug(_title_from_raw(raw, form))
    content = json.dumps(raw, ensure_ascii=False, indent=2)
    buf = io.BytesIO(content.encode("utf-8"))
    return send_file(
        buf,
        mimetype="application/json",
        as_attachment=True,
        download_name=f"{slug}.json",
    )


@bp.post("/download/transcription")
def download_transcription():
    form = request.form
    raw = _build_export_json(form)
    slug = _make_slug(_title_from_raw(raw, form))
    buf = io.BytesIO(form.get("transcription", "").encode("utf-8"))
    return send_file(
        buf,
        mimetype="text/plain; charset=utf-8",
        as_attachment=True,
        download_name=f"{slug}.txt",
    )


@bp.post("/download/castlist")
def download_castlist():
    form = request.form
    raw = _build_export_json(form)
    slug = _make_slug(_title_from_raw(raw, form))
    buf = io.BytesIO(form.get("castlist_text", "").encode("utf-8"))
    return send_file(
        buf,
        mimetype="text/plain; charset=utf-8",
        as_attachment=True,
        download_name=f"{slug}_castlist.txt",
    )
