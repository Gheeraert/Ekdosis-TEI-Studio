from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ets.application.editorial_notice_import.pandoc_bridge import (
    PandocBridge,
    PandocExecutionError,
    PandocNotFoundError,
)


def test_default_timeout_is_a_positive_number() -> None:
    bridge = PandocBridge(executable="pandoc-stub")
    assert bridge._timeout == PandocBridge.DEFAULT_TIMEOUT_SECONDS
    assert bridge._timeout > 0


def test_custom_timeout_is_honoured() -> None:
    bridge = PandocBridge(executable="pandoc-stub", timeout=5.0)
    assert bridge._timeout == 5.0


def test_load_docx_ast_passes_timeout_to_subprocess_run(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")

    monkeypatch.setattr(
        "ets.application.editorial_notice_import.pandoc_bridge.subprocess.run",
        fake_run,
    )

    bridge = PandocBridge(executable="pandoc-stub", timeout=12.5)
    docx_path = tmp_path / "doc.docx"
    docx_path.write_bytes(b"")

    result = bridge.load_docx_ast(docx_path)

    assert result == {}
    assert captured["kwargs"]["timeout"] == 12.5


def test_load_docx_ast_raises_clean_error_on_timeout(monkeypatch, tmp_path: Path) -> None:
    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(cmd=command, timeout=kwargs.get("timeout"))

    monkeypatch.setattr(
        "ets.application.editorial_notice_import.pandoc_bridge.subprocess.run",
        fake_run,
    )

    bridge = PandocBridge(executable="pandoc-stub", timeout=7.0)
    docx_path = tmp_path / "doc.docx"
    docx_path.write_bytes(b"")

    with pytest.raises(PandocExecutionError) as excinfo:
        bridge.load_docx_ast(docx_path)

    message = str(excinfo.value)
    assert "timeout" in message.lower()
    assert "7" in message
    # The error message must never leak the absolute server path.
    assert str(docx_path) not in message
    assert str(tmp_path) not in message


def test_load_docx_ast_raises_not_found_error_when_executable_missing(monkeypatch, tmp_path: Path) -> None:
    def fake_run(command, **kwargs):
        raise FileNotFoundError("no such file")

    monkeypatch.setattr(
        "ets.application.editorial_notice_import.pandoc_bridge.subprocess.run",
        fake_run,
    )

    bridge = PandocBridge(executable="pandoc-stub")
    docx_path = tmp_path / "doc.docx"
    docx_path.write_bytes(b"")

    with pytest.raises(PandocNotFoundError):
        bridge.load_docx_ast(docx_path)
