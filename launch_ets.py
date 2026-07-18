"""Point d'entrée local de l'interface Tkinter Ekdosis-TEI Studio.

Utilisable directement depuis un clone du dépôt, sans installation préalable.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ets.ui.tk.app import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())