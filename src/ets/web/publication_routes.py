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
from ets.application.site_publication_config import site_publication_dialog_config_to_dict

pub_bp = Blueprint("publication", __name__)

# Extensions autorisées par type de source éditoriale
_EDITORIAL_EXTS = {".xml", ".docx"}
_DRAMATIS_EXTS = {".xml"}
_LOGO_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif"}
_MAX_SOURCE_ZIP_BYTES = 50 * 1024 * 1024
_MAX_SOURCE_ZIP_UNCOMPRESSED_BYTES = 200 * 1024 * 1024
_MAX_SOURCE_ZIP_ENTRY_BYTES = 50 * 1024 * 1024


def _is_safe_zip_entry(name: str) -> bool:
    if not name:
        return False
    if name.startswith("/") or name.startswith("\\"):
        return False
    if len(name) >= 2 and name[1] == ":":
        return False
    parts = name.replace("\\", "/").split("/")
    return ".." not in parts


def _zip_size_errors(zip_data: bytes, zf: zipfile.ZipFile) -> list[str]:
    errors: list[str] = []
    if len(zip_data) > _MAX_SOURCE_ZIP_BYTES:
        errors.append("Le fichier ZIP est trop volumineux.")

    total_uncompressed = 0
    for info in zf.infolist():
        if info.is_dir():
            continue
        total_uncompressed += info.file_size
        if info.file_size > _MAX_SOURCE_ZIP_ENTRY_BYTES:
            errors.append(f"L'entrée ZIP {info.filename!r} dépasse la taille maximale autorisée.")

    if total_uncompressed > _MAX_SOURCE_ZIP_UNCOMPRESSED_BYTES:
        errors.append("La taille totale décompressée du ZIP est trop volumineuse.")
    return errors


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


def _basename_any_path(value: str | None) -> str:
    if not value:
        return ""
    return str(value).replace("\\", "/").rstrip("/").split("/")[-1]


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
            size_errors = _zip_size_errors(zip_data, zf)
            if size_errors:
                return render_template("publish_static.html", error=" ".join(size_errors))
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


@pub_bp.post("/publish/builder/config")
def builder_config_download():
    """Construit et retourne un JSON métier de publication depuis le formulaire constructeur."""
    form = request.form
    files = request.files

    author_first = form.get("author_first_name", "").strip()
    author_last = form.get("author_last_name", "").strip()
    editor_first = form.get("editor_first_name", "").strip()
    editor_last = form.get("editor_last_name", "").strip()
    corpus_title = form.get("corpus_title", "").strip()

    publish_notices = "publish_notices" in form
    publish_prefaces = "publish_prefaces" in form
    include_metadata = "include_metadata" in form
    resolve_xincludes = "resolve_notice_xincludes" in form

    author_name = " ".join(p for p in (author_first, author_last) if p)
    scientific_editor = " ".join(p for p in (editor_first, editor_last) if p)
    relative_base = Path.cwd().resolve()
    sources_dir = relative_base / "sources"

    def _source_path(key: str) -> Path | None:
        f = files.get(key)
        filename = _basename_any_path(f.filename if f else None)
        if not filename:
            return None
        return sources_dir / filename

    home_page_path = _source_path("home_page_file")
    intro_path = _source_path("general_intro_file")
    logo_paths = tuple(
        sources_dir / filename
        for logo_file in files.getlist("logos")
        for filename in [_basename_any_path(logo_file.filename if logo_file else None)]
        if filename
    )

    # Collect indexed play blocks
    indices: set[int] = set()
    for key in list(files.keys()):
        m = re.match(r"^play_(\d+)_(xml|notice|preface|dramatis)$", key)
        if m:
            indices.add(int(m.group(1)))

    play_configs: list[SitePublicationDialogPlayConfig] = []
    for i in sorted(indices):
        def _fn(key: str) -> str:
            f = files.get(key)
            return _basename_any_path(f.filename if f else None)

        xml_name = _fn(f"play_{i}_xml")
        notice_name = _fn(f"play_{i}_notice")
        preface_name = _fn(f"play_{i}_preface")
        dramatis_name = _fn(f"play_{i}_dramatis")
        has_any = any([xml_name, notice_name, preface_name, dramatis_name])
        if not has_any:
            continue
        if not xml_name:
            return render_template(
                "builder.html",
                error=(
                    "Une piece contient une notice, une preface ou un dramatis "
                    "mais aucun XML dramatique de piece."
                ),
            )

        raw_stem = Path(xml_name).stem
        normalized_stem = unicodedata.normalize("NFD", raw_stem)
        ascii_stem = normalized_stem.encode("ascii", "ignore").decode("ascii").lower()
        play_slug = re.sub(r"[^a-z0-9]+", "-", ascii_stem).strip("-") or "piece"
        play_configs.append(
            SitePublicationDialogPlayConfig(
                play_slug=play_slug,
                dramatic_xml_path=sources_dir / xml_name,
                notice_xml_path=(sources_dir / notice_name) if notice_name else None,
                preface_xml_path=(sources_dir / preface_name) if preface_name else None,
                dramatis_xml_path=(sources_dir / dramatis_name) if dramatis_name else None,
            )
        )

    config = SitePublicationDialogConfig(
        author_name=author_name,
        corpus_title=corpus_title,
        scientific_editor=scientific_editor,
        home_page_tei=home_page_path,
        general_intro_tei=intro_path,
        output_dir=None,
        plays=tuple(play_configs),
        play_order=tuple(play.play_slug for play in play_configs),
        logo_paths=logo_paths,
        asset_directories=(),
        show_xml_download=True,
        build_latex_pdf=False,
        hide_minor_variants_in_pdf=False,
        publish_notices=publish_notices,
        publish_prefaces=publish_prefaces,
        include_metadata=include_metadata,
        resolve_notice_xincludes=resolve_xincludes,
    )

    config_data = site_publication_dialog_config_to_dict(config, relative_to=relative_base)
    json_bytes = json.dumps(config_data, ensure_ascii=False, indent=2).encode("utf-8")
    buf = io.BytesIO(json_bytes)
    buf.seek(0)

    normalized = unicodedata.normalize("NFD", corpus_title)
    ascii_str = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_str.lower()).strip("_") or "configuration"

    return send_file(
        buf,
        mimetype="application/json",
        as_attachment=True,
        download_name=f"{slug}_publication_config.json",
    )


@pub_bp.post("/publish/builder/source-package")
def builder_source_package():
    """Assemble les sources uploadées et la config dans un ZIP compatible /publish/static."""
    form = request.form
    files = request.files

    author_first = form.get("author_first_name", "").strip()
    author_last = form.get("author_last_name", "").strip()
    editor_first = form.get("editor_first_name", "").strip()
    editor_last = form.get("editor_last_name", "").strip()
    corpus_title = form.get("corpus_title", "").strip()

    author_name = " ".join(p for p in (author_first, author_last) if p)
    scientific_editor = " ".join(p for p in (editor_first, editor_last) if p)

    publish_notices = "publish_notices" in form
    publish_prefaces = "publish_prefaces" in form
    include_metadata = "include_metadata" in form
    resolve_xincludes = "resolve_notice_xincludes" in form

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        sources_dir = tmp / "sources"
        sources_dir.mkdir()

        def _save_path(key: str) -> Path | None:
            f = files.get(key)
            if not f or not f.filename:
                return None
            return _save_upload(f, sources_dir)

        home_page_path = _save_path("home_page_file")
        intro_path = _save_path("general_intro_file")

        logo_paths: list[Path] = []
        for logo_file in files.getlist("logos"):
            if logo_file and logo_file.filename:
                saved = _save_upload(logo_file, sources_dir)
                logo_paths.append(saved)

        # Collect indexed play blocks
        indices: set[int] = set()
        for key in list(files.keys()):
            m = re.match(r"^play_(\d+)_(xml|notice|preface|dramatis)$", key)
            if m:
                indices.add(int(m.group(1)))

        play_configs: list[SitePublicationDialogPlayConfig] = []
        for i in sorted(indices):
            xml_file = files.get(f"play_{i}_xml")
            notice_file = files.get(f"play_{i}_notice")
            preface_file = files.get(f"play_{i}_preface")
            dramatis_file = files.get(f"play_{i}_dramatis")

            has_xml = bool(xml_file and xml_file.filename)
            has_any = has_xml or any(
                bool(f and f.filename) for f in [notice_file, preface_file, dramatis_file]
            )
            if not has_any:
                continue
            if not has_xml:
                return render_template(
                    "builder.html",
                    error=(
                        "Une pièce contient une notice, une préface ou un dramatis "
                        "mais aucun XML dramatique de pièce."
                    ),
                )

            saved = _save_upload(xml_file, sources_dir)  # type: ignore[arg-type]
            raw_stem = Path(xml_file.filename).stem  # type: ignore[union-attr]
            normalized_stem = unicodedata.normalize("NFD", raw_stem)
            ascii_stem = normalized_stem.encode("ascii", "ignore").decode("ascii").lower()
            play_slug = re.sub(r"[^a-z0-9]+", "-", ascii_stem).strip("-") or "piece"

            def _save_path_opt(key: str) -> Path | None:
                f = files.get(key)
                if not f or not f.filename:
                    return None
                return _save_upload(f, sources_dir)

            play_configs.append(
                SitePublicationDialogPlayConfig(
                    play_slug=play_slug,
                    dramatic_xml_path=saved,
                    notice_xml_path=_save_path_opt(f"play_{i}_notice"),
                    preface_xml_path=_save_path_opt(f"play_{i}_preface"),
                    dramatis_xml_path=_save_path_opt(f"play_{i}_dramatis"),
                )
            )

        config = SitePublicationDialogConfig(
            author_name=author_name,
            corpus_title=corpus_title,
            scientific_editor=scientific_editor,
            home_page_tei=home_page_path,
            general_intro_tei=intro_path,
            output_dir=None,
            plays=tuple(play_configs),
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

        config_dict = site_publication_dialog_config_to_dict(config, relative_to=tmp)
        config_json = json.dumps(config_dict, ensure_ascii=False, indent=2)

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("publication_config.json", config_json.encode("utf-8"))
            for f in sources_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(tmp).as_posix())
        zip_buf.seek(0)

        normalized = unicodedata.normalize("NFD", corpus_title)
        ascii_str = normalized.encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^a-z0-9]+", "_", ascii_str.lower()).strip("_") or "source"

        return send_file(
            zip_buf,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"{slug}_source.zip",
        )


@pub_bp.post("/publish/builder/import-source-package")
def builder_import_source_package():
    """Importe un paquet source ZIP dans le constructeur (configuration + inventaire)."""
    uploaded = request.files.get("source_package_file")
    if not uploaded or not uploaded.filename:
        return render_template("builder.html", error="Aucun fichier ZIP fourni.")

    zip_data = uploaded.read()

    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            size_errors = _zip_size_errors(zip_data, zf)
            if size_errors:
                return render_template("builder.html", error=" ".join(size_errors))
            all_names = zf.namelist()
    except zipfile.BadZipFile:
        return render_template(
            "builder.html",
            error="Le fichier fourni n'est pas un ZIP valide.",
        )

    dangerous = [n for n in all_names if not _is_safe_zip_entry(n)]
    if dangerous:
        sample = ", ".join(dangerous[:3])
        return render_template(
            "builder.html",
            error=f"Le ZIP contient des entrées dangereuses : {sample}.",
        )

    json_names = [n for n in all_names if n.lower().endswith(".json")]
    if not json_names:
        return render_template(
            "builder.html",
            error="Le ZIP ne contient aucun fichier JSON de configuration.",
        )
    if len(json_names) > 1:
        listed = ", ".join(json_names)
        return render_template(
            "builder.html",
            error=f"Le ZIP contient plusieurs fichiers JSON ({listed}). Il doit en contenir exactement un.",
        )

    json_entry = json_names[0]

    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        try:
            raw_json = zf.read(json_entry).decode("utf-8")
        except UnicodeDecodeError as exc:
            return render_template(
                "builder.html",
                error=f"Le fichier JSON n'est pas encodé en UTF-8 : {exc}",
            )

    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        return render_template(
            "builder.html",
            error=f"JSON de configuration invalide : {exc.msg}.",
        )

    if not isinstance(payload, dict):
        return render_template(
            "builder.html",
            error="Le JSON de configuration doit être un objet (accolades {…}).",
        )

    metadata = payload.get("metadata") or {}
    xml_sources = payload.get("xml_sources") or {}
    options_raw = payload.get("options") or {}
    plays_raw = payload.get("plays") if isinstance(payload.get("plays"), list) else []

    # Contrôle des chemins déclarés dans le JSON (même règles que les entrées ZIP).
    json_paths: list[str] = []
    if isinstance(xml_sources, dict):
        for _key in ("home_page_tei_path", "general_intro_tei_path"):
            _v = xml_sources.get(_key)
            if _v is not None:
                json_paths.append(str(_v))
    for _p in plays_raw:
        if isinstance(_p, dict):
            for _key in ("dramatic_xml_path", "notice_xml_path", "preface_xml_path", "dramatis_xml_path"):
                _v = _p.get(_key)
                if _v is not None:
                    json_paths.append(str(_v))

    unsafe_json_paths = [p for p in json_paths if not _is_safe_zip_entry(p)]
    if unsafe_json_paths:
        sample = ", ".join(unsafe_json_paths[:3])
        return render_template(
            "builder.html",
            error=f"Le JSON contient des chemins dangereux : {sample}.",
        )

    source_import = {
        "author_name": metadata.get("author_name", "") if isinstance(metadata, dict) else "",
        "corpus_title": metadata.get("corpus_title", "") if isinstance(metadata, dict) else "",
        "scientific_editor": metadata.get("scientific_editor", "") if isinstance(metadata, dict) else "",
        "home_page_path": xml_sources.get("home_page_tei_path") if isinstance(xml_sources, dict) else None,
        "general_intro_path": xml_sources.get("general_intro_tei_path") if isinstance(xml_sources, dict) else None,
        "options": {
            "publish_notices": bool(options_raw.get("publish_notices", True)) if isinstance(options_raw, dict) else True,
            "publish_prefaces": bool(options_raw.get("publish_prefaces", True)) if isinstance(options_raw, dict) else True,
            "include_metadata": bool(options_raw.get("include_metadata", True)) if isinstance(options_raw, dict) else True,
            "resolve_notice_xincludes": bool(options_raw.get("resolve_notice_xincludes", True)) if isinstance(options_raw, dict) else True,
        },
        "plays": [
            {
                "play_slug": p.get("play_slug", "") if isinstance(p, dict) else "",
                "dramatic_xml_path": p.get("dramatic_xml_path") if isinstance(p, dict) else None,
                "notice_xml_path": p.get("notice_xml_path") if isinstance(p, dict) else None,
                "preface_xml_path": p.get("preface_xml_path") if isinstance(p, dict) else None,
                "dramatis_xml_path": p.get("dramatis_xml_path") if isinstance(p, dict) else None,
            }
            for p in plays_raw
            if isinstance(p, dict)
        ],
    }

    return render_template("builder.html", source_import=source_import)


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

        # ── Collecte et validation des pièces (indexées) ──────────────────────
        indices: set[int] = set()
        for key in list(files.keys()):
            m = re.match(r"^play_(\d+)_(xml|notice|preface|dramatis)$", key)
            if m:
                indices.add(int(m.group(1)))

        play_configs: list[SitePublicationDialogPlayConfig] = []
        for i in sorted(indices):
            xml_file = files.get(f"play_{i}_xml")
            notice_file = files.get(f"play_{i}_notice")
            preface_file = files.get(f"play_{i}_preface")
            dramatis_file = files.get(f"play_{i}_dramatis")

            has_xml = bool(xml_file and xml_file.filename)
            has_notice = bool(notice_file and notice_file.filename)
            has_preface = bool(preface_file and preface_file.filename)
            has_dramatis = bool(dramatis_file and dramatis_file.filename)
            has_any = has_xml or has_notice or has_preface or has_dramatis

            if not has_any:
                continue

            if not has_xml:
                return render_template(
                    "builder.html",
                    error=(
                        f"La pièce {i + 1} contient des fichiers annexes (notice, préface ou "
                        f"dramatis personae) mais aucun XML de pièce dramatique."
                    ),
                )

            play_path = _save_upload(xml_file, uploads)  # type: ignore[arg-type]
            err = _check_ext(play_path, {".xml"}, f"pièce {i + 1} XML")
            if err:
                return render_template("builder.html", error=err)

            notice_path: Path | None = None
            if has_notice:
                notice_path = _save_upload(notice_file, uploads)  # type: ignore[arg-type]
                err = _check_ext(notice_path, _EDITORIAL_EXTS, f"notice pièce {i + 1}")
                if err:
                    return render_template("builder.html", error=err)

            preface_path: Path | None = None
            if has_preface:
                preface_path = _save_upload(preface_file, uploads)  # type: ignore[arg-type]
                err = _check_ext(preface_path, _EDITORIAL_EXTS, f"préface pièce {i + 1}")
                if err:
                    return render_template("builder.html", error=err)

            dramatis_path: Path | None = None
            if has_dramatis:
                dramatis_path = _save_upload(dramatis_file, uploads)  # type: ignore[arg-type]
                err = _check_ext(dramatis_path, _DRAMATIS_EXTS, f"dramatis personae pièce {i + 1}")
                if err:
                    return render_template("builder.html", error=err)

            play_configs.append(SitePublicationDialogPlayConfig(
                play_slug="",
                dramatic_xml_path=play_path,
                notice_xml_path=notice_path,
                preface_xml_path=preface_path,
                dramatis_xml_path=dramatis_path,
            ))

        if not play_configs:
            return render_template(
                "builder.html",
                error="Au moins une pièce XML est requise.",
            )

        # ── Options ───────────────────────────────────────────────────────────
        publish_notices = "publish_notices" in form
        publish_prefaces = "publish_prefaces" in form
        include_metadata = "include_metadata" in form
        resolve_xincludes = "resolve_notice_xincludes" in form

        # ── Construction de SitePublicationDialogConfig ───────────────────────
        config = SitePublicationDialogConfig(
            author_name=author_name,
            corpus_title=corpus_title,
            scientific_editor=scientific_editor,
            home_page_tei=home_path,
            general_intro_tei=intro_path,
            output_dir=None,
            plays=tuple(play_configs),
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
