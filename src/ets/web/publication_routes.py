from __future__ import annotations

import io
import json
import re
import tempfile
import unicodedata
import zipfile
from dataclasses import replace
from pathlib import Path

from flask import Blueprint, render_template, request, send_file

from ets.application import (
    EditorialNoticeImportService,
    SitePublicationDialogConfig,
    build_site_from_publication_request,
    site_publication_dialog_config_from_dict,
    site_publication_request_from_dialog_config,
)

pub_bp = Blueprint("publication", __name__)


def _is_safe_zip_entry(name: str) -> bool:
    if not name:
        return False
    if name.startswith("/") or name.startswith("\\"):
        return False
    if len(name) >= 2 and name[1] == ":":
        return False
    parts = name.replace("\\", "/").split("/")
    return ".." not in parts


def _make_output_slug(config: SitePublicationDialogConfig) -> str:
    combined = " ".join(p for p in (config.author_name, config.corpus_title) if p).strip()
    if not combined:
        return "site_statique"
    normalized = unicodedata.normalize("NFD", combined)
    ascii_str = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_str.lower()).strip("_")
    return slug or "site_statique"


def _validate_config_paths(config: SitePublicationDialogConfig, base_dir: Path) -> list[str]:
    errors: list[str] = []
    base = base_dir.resolve()

    def _check(path: Path | None, label: str) -> None:
        if path is None:
            return
        try:
            path.resolve().relative_to(base)
        except ValueError:
            errors.append(f"Chemin hors du dossier source ({label}) : {path.name}")

    _check(config.home_page_tei, "home_page_tei")
    _check(config.general_intro_tei, "general_intro_tei")
    for i, play in enumerate(config.plays):
        _check(play.dramatic_xml_path, f"plays[{i}].dramatic_xml_path")
        _check(play.notice_xml_path, f"plays[{i}].notice_xml_path")
        _check(play.preface_xml_path, f"plays[{i}].preface_xml_path")
        _check(play.dramatis_xml_path, f"plays[{i}].dramatis_xml_path")
    for logo in config.logo_paths:
        _check(logo, "logo_paths")
    for asset_dir in config.asset_directories:
        _check(asset_dir, "asset_directories")
    return errors


def _zip_directory(source_dir: Path) -> io.BytesIO:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(source_dir.rglob("*")):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(source_dir))
    buf.seek(0)
    return buf


@pub_bp.get("/publish/static")
def publish_static_get():
    return render_template("publish_static.html")


@pub_bp.post("/publish/static")
def publish_static_post():
    uploaded = request.files.get("source_zip")
    if not uploaded or not uploaded.filename:
        return render_template("publish_static.html", error="Aucun fichier ZIP fourni.")

    zip_data = uploaded.read()

    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            all_names = zf.namelist()
    except zipfile.BadZipFile:
        return render_template(
            "publish_static.html",
            error="Le fichier fourni n'est pas un ZIP valide.",
        )

    dangerous = [n for n in all_names if not _is_safe_zip_entry(n)]
    if dangerous:
        sample = ", ".join(dangerous[:3])
        return render_template(
            "publish_static.html",
            error=f"Le ZIP contient des entrées dangereuses : {sample}.",
        )

    json_names = [n for n in all_names if n.lower().endswith(".json")]
    if not json_names:
        return render_template(
            "publish_static.html",
            error="Le ZIP ne contient aucun fichier JSON de configuration de publication.",
        )
    if len(json_names) > 1:
        listed = ", ".join(json_names)
        return render_template(
            "publish_static.html",
            error=f"Le ZIP contient plusieurs fichiers JSON ({listed}). Il doit en contenir exactement un.",
        )

    json_entry = json_names[0]

    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        try:
            raw_json = zf.read(json_entry).decode("utf-8")
        except UnicodeDecodeError as exc:
            return render_template(
                "publish_static.html",
                error=f"Le fichier JSON n'est pas encodé en UTF-8 : {exc}",
            )

    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        return render_template(
            "publish_static.html",
            error=f"JSON de configuration invalide : {exc.msg}.",
        )

    if not isinstance(payload, dict):
        return render_template(
            "publish_static.html",
            error="Le JSON de configuration doit être un objet (accolades {…}).",
        )

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        temp_source_dir = tmp / "source"
        temp_source_dir.mkdir()
        temp_output_dir = tmp / "site_output"

        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            for entry in zf.infolist():
                if not _is_safe_zip_entry(entry.filename):
                    continue
                if entry.filename.endswith("/"):
                    continue
                target = temp_source_dir / entry.filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(entry.filename))

        try:
            config = site_publication_dialog_config_from_dict(payload, base_dir=temp_source_dir)
        except ValueError as exc:
            return render_template(
                "publish_static.html",
                error=f"Configuration de publication invalide : {exc}",
            )

        path_errors = _validate_config_paths(config, temp_source_dir)
        if path_errors:
            return render_template(
                "publish_static.html",
                error="Chemin(s) invalide(s) dans la configuration :\n" + "\n".join(path_errors),
            )

        # Replace output_dir with our controlled temp dir; always disable PDF.
        config = replace(config, output_dir=temp_output_dir, build_latex_pdf=False)

        service = EditorialNoticeImportService()
        try:
            prepared = service.prepare_dialog_config_for_publication(config)
        except ValueError as exc:
            error_msg = str(exc)
            if "andoc" in error_msg:
                return render_template(
                    "publish_static.html",
                    error=(
                        "Pandoc est introuvable ou inaccessible. "
                        "Installer pandoc pour traiter les fichiers DOCX.\n\nDétail : " + error_msg
                    ),
                )
            return render_template(
                "publish_static.html",
                error=f"Échec de la préparation des sources éditoriales : {error_msg}",
            )

        try:
            pub_request = site_publication_request_from_dialog_config(prepared.config)
        except ValueError as exc:
            return render_template(
                "publish_static.html",
                error=f"Configuration de publication incomplète : {exc}",
            )

        result = build_site_from_publication_request(pub_request)

        if not result.ok:
            detail = result.error_detail or result.message or "Erreur inconnue."
            return render_template(
                "publish_static.html",
                error=f"Échec de la génération du site statique : {detail}",
            )

        if result.output_dir is None or not result.output_dir.exists():
            return render_template(
                "publish_static.html",
                error="La génération a réussi mais le dossier de sortie est introuvable.",
            )

        try:
            zip_buf = _zip_directory(result.output_dir)
        except OSError as exc:
            return render_template(
                "publish_static.html",
                error=f"Impossible de créer le ZIP de sortie : {exc}",
            )

        slug = _make_output_slug(config)
        return send_file(
            zip_buf,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"{slug}_site.zip",
        )
