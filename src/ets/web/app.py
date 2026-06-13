from __future__ import annotations

import os
from pathlib import Path

from flask import Flask

from .publication_routes import pub_bp
from .routes import bp

# Limite par défaut de la taille d'une requête (corps + fichiers uploadés).
# Surchargable via la variable d'environnement ETS_MAX_CONTENT_LENGTH (en octets).
DEFAULT_MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 Mo


def create_app(*, testing: bool = False) -> Flask:
    pkg_dir = Path(__file__).parent
    app = Flask(
        __name__,
        template_folder=str(pkg_dir / "templates"),
        static_folder=str(pkg_dir / "static"),
    )
    if testing:
        app.config["TESTING"] = True
    app.config["MAX_CONTENT_LENGTH"] = _max_content_length()
    app.register_blueprint(bp)
    app.register_blueprint(pub_bp)
    return app


def _max_content_length() -> int:
    raw = os.environ.get("ETS_MAX_CONTENT_LENGTH", "").strip()
    if raw:
        try:
            value = int(raw)
        except ValueError:
            value = 0
        if value > 0:
            return value
    return DEFAULT_MAX_CONTENT_LENGTH
