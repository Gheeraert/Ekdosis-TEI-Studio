from __future__ import annotations

from pathlib import Path

from flask import Flask

from .publication_routes import pub_bp
from .routes import bp


def create_app(*, testing: bool = False) -> Flask:
    pkg_dir = Path(__file__).parent
    app = Flask(
        __name__,
        template_folder=str(pkg_dir / "templates"),
        static_folder=str(pkg_dir / "static"),
    )
    if testing:
        app.config["TESTING"] = True
    app.register_blueprint(bp)
    app.register_blueprint(pub_bp)
    return app
