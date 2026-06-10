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
from werkzeug.datastructures import FileStorage

from ets.application import (
    EditorialNoticeImportService,
    SitePublicationDialogConfig,
    SitePublicationDialogPlayConfig,
    build_site_from_publication_request,
    site_publication_dialog_config_from_dict,
    site_publication_request_from_dialog_config,
)

pub_bp = Blueprint("publication", __name__)

# Extensions autorisées par type de source éditoriale
_EDITORIAL_EXTS = {".xml", ".docx"}
_DRAMATIS_EXTS = {".xml"}
_LOGO_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif"}


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


# ── Constructeur de site — helpers ────────────────────────────────────────────

def _save_upload(file: FileStorage, dest_dir: Path) -> Path:
    """Écrit un FileStorage dans dest_dir en conservant l'extension d'origine."""
    filename = Path(file.filename).name if file.filename else "upload"
    target = dest_dir / filename
    counter = 2
    while target.exists():
        stem = Path(file.filename).stem if file.filename else "upload"
        suffix = Path(file.filename).suffix if file.filename else ""
        target = dest_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    file.save(str(target))
    return target


def _check_ext(path: Path, allowed: set[str], label: str) -> str | None:
    """Retourne un message d'erreur si l'extension n'est pas dans allowed."""
    if path.suffix.lower() not in allowed:
        exts = ", ".join(sorted(allowed))
        return (
            f"Extension refusée pour « {label} » : {path.suffix!r}. "
            f"Extensions acceptées : {exts}."
        )
    return None


def _run_builder_pipeline(
    config: SitePublicationDialogConfig,
    tmp: Path,
) -> tuple[io.BytesIO | None, str | None]:
    """
    Exécute la chaîne complète : prepare → request → build → zip.
    Retourne (zip_buf, None) en cas de succès ou (None, message_erreur).
    """
    temp_output_dir = tmp / "site_output"
    config = replace(config, output_dir=temp_output_dir, build_latex_pdf=False)

    service = EditorialNoticeImportService()
    try:
        prepared = service.prepare_dialog_config_for_publication(config)
    except ValueError as exc:
        msg = str(exc)
        if "andoc" in msg:
            return None, (
                "Pandoc est introuvable ou inaccessible. "
                "Installer pandoc pour traiter les fichiers DOCX.\n\nDétail : " + msg
            )
        return None, f"Échec de la préparation des sources éditoriales : {msg}"

    try:
        pub_request = site_publication_request_from_dialog_config(prepared.config)
    except ValueError as exc:
        return None, f"Configuration de publication incomplète : {exc}"

    result = build_site_from_publication_request(pub_request)
    if not result.ok:
        detail = result.error_detail or result.message or "Erreur inconnue."
        return None, f"Échec de la génération du site statique : {detail}"

    if result.output_dir is None or not result.output_dir.exists():
        return None, "La génération a réussi mais le dossier de sortie est introuvable."

    try:
        zip_buf = _zip_directory(result.output_dir)
    except OSError as exc:
        return None, f"Impossible de créer le ZIP de sortie : {exc}"

    return zip_buf, None


# ── Constructeur de site — routes ─────────────────────────────────────────────

@pub_bp.get("/publish/builder")
def builder_get():
    return render_template("builder.html")


@pub_bp.post("/publish/builder")
def builder_post():
    form = request.form
    files = request.files

    # ── Métadonnées ──────────────────────────────────────────────────────────
    author_first = form.get("author_first_name", "").strip()
    author_last = form.get("author_last_name", "").strip()
    editor_first = form.get("editor_first_name", "").strip()
    editor_last = form.get("editor_last_name", "").strip()
    corpus_title = form.get("corpus_title", "").strip()

    author_name = " ".join(p for p in (author_first, author_last) if p)
    scientific_editor = " ".join(p for p in (editor_first, editor_last) if p)

    if not corpus_title:
        return render_template("builder.html", error="Le titre de l'œuvre ou du corpus est requis.")

    # ── Fichier XML dramatique (requis) ───────────────────────────────────────
    play_xml_file = files.get("play_xml")
    if not play_xml_file or not play_xml_file.filename:
        return render_template("builder.html", error="Un fichier XML de pièce dramatique est requis.")

    # ── Page d'accueil (requise) ───────────────────────────────────────────────
    home_page_file = files.get("home_page_file")
    if not home_page_file or not home_page_file.filename:
        return render_template("builder.html", error="La page d'accueil du site est requise.")

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        uploads = tmp / "uploads"
        uploads.mkdir()

        # ── Sauvegarde et validation : page d'accueil ─────────────────────────
        home_path = _save_upload(home_page_file, uploads)
        err = _check_ext(home_path, _EDITORIAL_EXTS, "page d'accueil")
        if err:
            return render_template("builder.html", error=err)

        # ── Sauvegarde et validation : introduction générale (optionnelle) ────
        intro_path: Path | None = None
        intro_file = files.get("general_intro_file")
        if intro_file and intro_file.filename:
            intro_path = _save_upload(intro_file, uploads)
            err = _check_ext(intro_path, _EDITORIAL_EXTS, "introduction générale")
            if err:
                return render_template("builder.html", error=err)

        # ── Sauvegarde et validation : logos (optionnels, multiples) ─────────
        logo_paths: list[Path] = []
        logo_files = files.getlist("logos")
        for logo_file in logo_files:
            if not logo_file or not logo_file.filename:
                continue
            logo_path = _save_upload(logo_file, uploads)
            err = _check_ext(logo_path, _LOGO_EXTS, f"logo {logo_path.name}")
            if err:
                return render_template("builder.html", error=err)
            logo_paths.append(logo_path)

        # ── Sauvegarde et validation : pièce XML ──────────────────────────────
        play_path = _save_upload(play_xml_file, uploads)
        err = _check_ext(play_path, {".xml"}, "pièce dramatique XML")
        if err:
            return render_template("builder.html", error=err)

        # ── Sauvegarde et validation : notice (optionnelle) ───────────────────
        notice_path: Path | None = None
        notice_file = files.get("play_notice")
        if notice_file and notice_file.filename:
            notice_path = _save_upload(notice_file, uploads)
            err = _check_ext(notice_path, _EDITORIAL_EXTS, "notice")
            if err:
                return render_template("builder.html", error=err)

        # ── Sauvegarde et validation : préface (optionnelle) ──────────────────
        preface_path: Path | None = None
        preface_file = files.get("play_preface")
        if preface_file and preface_file.filename:
            preface_path = _save_upload(preface_file, uploads)
            err = _check_ext(preface_path, _EDITORIAL_EXTS, "préface")
            if err:
                return render_template("builder.html", error=err)

        # ── Sauvegarde et validation : dramatis personae XML (optionnel) ──────
        dramatis_path: Path | None = None
        dramatis_file = files.get("play_dramatis")
        if dramatis_file and dramatis_file.filename:
            dramatis_path = _save_upload(dramatis_file, uploads)
            err = _check_ext(dramatis_path, _DRAMATIS_EXTS, "dramatis personae")
            if err:
                return render_template("builder.html", error=err)

        # ── Options ───────────────────────────────────────────────────────────
        publish_notices = "publish_notices" in form
        publish_prefaces = "publish_prefaces" in form
        include_metadata = "include_metadata" in form
        resolve_xincludes = "resolve_notice_xincludes" in form

        # ── Construction de SitePublicationDialogConfig ───────────────────────
        play_config = SitePublicationDialogPlayConfig(
            play_slug="",
            dramatic_xml_path=play_path,
            notice_xml_path=notice_path,
            preface_xml_path=preface_path,
            dramatis_xml_path=dramatis_path,
        )
        config = SitePublicationDialogConfig(
            author_name=author_name,
            corpus_title=corpus_title,
            scientific_editor=scientific_editor,
            home_page_tei=home_path,
            general_intro_tei=intro_path,
            output_dir=None,
            plays=(play_config,),
            play_order=(),
            logo_paths=tuple(logo_paths),
            asset_directories=(),
            show_xml_download=True,
            build_latex_pdf=False,
            hide_minor_variants_in_pdf=False,
            publish_notices=publish_notices,
            publish_prefaces=publish_prefaces,
            include_metadata=include_metadata,
            resolve_notice_xincludes=resolve_xincludes,
        )

        # ── Pipeline de génération ────────────────────────────────────────────
        zip_buf, error_msg = _run_builder_pipeline(config, tmp)
        if error_msg:
            return render_template("builder.html", error=error_msg)

        slug = _make_output_slug(config)
        return send_file(
            zip_buf,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"{slug}_site.zip",
        )
