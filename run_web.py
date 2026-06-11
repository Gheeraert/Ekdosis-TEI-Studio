"""Point d'entrée local et WSGI pour l'interface web Ekdosis-TEI Studio.

Usage local :
    python run_web.py

Usage Render/Gunicorn :
    gunicorn run_web:application --bind 0.0.0.0:$PORT
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ets.web import create_app  # noqa: E402

# Objet WSGI importable par Gunicorn
application = create_app()

# Alias pratique, si besoin
app = application

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
    )