"""Point d'entrée local pour l'interface web Ekdosis-TEI Studio.

Usage :
    python run_web.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ets.web import create_app  # noqa: E402

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
