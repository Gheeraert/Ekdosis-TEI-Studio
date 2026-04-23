from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class PandocBridgeError(RuntimeError):
    """Base error for pandoc bridge failures."""


class PandocNotFoundError(PandocBridgeError):
    """Raised when pandoc executable cannot be found."""


class PandocExecutionError(PandocBridgeError):
    """Raised when pandoc execution fails."""


class PandocBridge:
    def __init__(self, executable: str = "pandoc") -> None:
        self._executable = executable

    def load_docx_ast(self, source_path: Path) -> dict[str, Any]:
        command = [
            self._executable,
            str(source_path),
            "-f",
            "docx+styles",
            "-t",
            "json",
        ]
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except FileNotFoundError as exc:
            raise PandocNotFoundError("Pandoc executable not found.") from exc
        except OSError as exc:
            raise PandocExecutionError(f"Unable to launch pandoc: {exc}") from exc

        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            if not detail:
                detail = f"Pandoc exited with code {completed.returncode}."
            raise PandocExecutionError(detail)

        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise PandocExecutionError(f"Invalid Pandoc JSON output: {exc.msg}.") from exc

        if not isinstance(payload, dict):
            raise PandocExecutionError("Invalid Pandoc JSON output: root must be an object.")
        return payload

