from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


def _default_runtime_dir() -> Path:
    return Path.home() / ".ets_teistudio_v2"


@dataclass(frozen=True)
class AutosavePayload:
    text: str
    current_file_path: str | None = None
    config_path: str | None = None
    saved_at: str | None = None


class AutosaveStore:
    """Simple JSON autosave persistence for desktop sessions."""

    def __init__(self, base_dir: Path | None = None, filename: str = "autosave.json") -> None:
        self.base_dir = base_dir or _default_runtime_dir()
        self.path = self.base_dir / filename

    def exists(self) -> bool:
        return self.path.exists()

    def save(self, payload: AutosavePayload) -> Path:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        serializable: dict[str, Any] = {
            "text": payload.text,
            "current_file_path": payload.current_file_path,
            "config_path": payload.config_path,
            "saved_at": payload.saved_at or datetime.now(timezone.utc).isoformat(),
        }
        self.path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")
        return self.path.resolve()

    def load(self) -> AutosavePayload | None:
        if not self.path.exists():
            return None
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return AutosavePayload(
            text=str(raw.get("text", "")),
            current_file_path=self._optional_text(raw.get("current_file_path")),
            config_path=self._optional_text(raw.get("config_path")),
            saved_at=self._optional_text(raw.get("saved_at")),
        )

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
