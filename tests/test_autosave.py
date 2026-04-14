from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from ets.infrastructure import AutosavePayload, AutosaveStore


def _runtime_dir(name: str) -> Path:
    root = Path(__file__).resolve().parents[1] / "tests" / "_runtime"
    root.mkdir(exist_ok=True)
    path = root / f"{name}_{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_autosave_write_and_read() -> None:
    store = AutosaveStore(base_dir=_runtime_dir("autosave"))
    payload = AutosavePayload(
        text="Texte de travail",
        current_file_path="C:/work/input.txt",
        config_path="C:/work/config.json",
    )
    store.save(payload)

    loaded = store.load()
    assert loaded is not None
    assert loaded.text == "Texte de travail"
    assert loaded.current_file_path == "C:/work/input.txt"
    assert loaded.config_path == "C:/work/config.json"
    assert loaded.saved_at is not None


def test_autosave_load_returns_none_when_missing() -> None:
    store = AutosaveStore(base_dir=_runtime_dir("autosave_missing"))
    assert store.load() is None
    assert store.exists() is False
