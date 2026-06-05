from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from ets.publication_pdf import PublicationPdfCompileResult, compile_publication_pdf


class _RunRecorder:
    def __init__(self, *, returncodes: list[int], create_pdf_on_success: bool = True) -> None:
        self.returncodes = returncodes
        self.create_pdf_on_success = create_pdf_on_success
        self.calls: list[tuple[list[str], dict[str, object]]] = []

    def __call__(self, command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        self.calls.append((command, kwargs))
        returncode = self.returncodes[min(len(self.calls) - 1, len(self.returncodes) - 1)]
        cwd = Path(kwargs["cwd"])  # type: ignore[arg-type]
        if returncode == 0 and self.create_pdf_on_success:
            (cwd / "master.pdf").write_text("pdf", encoding="utf-8")
        return subprocess.CompletedProcess(
            command,
            returncode,
            stdout=f"stdout pass {len(self.calls)}",
            stderr=f"stderr pass {len(self.calls)}",
        )


def _write_master(tmp_path: Path, name: str = "master.tex") -> Path:
    master = tmp_path / name
    master.write_text("\\documentclass{book}", encoding="utf-8")
    return master


def test_compile_publication_pdf_rejects_missing_master(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="introuvable"):
        compile_publication_pdf(tmp_path / "missing.tex")


def test_compile_publication_pdf_rejects_non_tex_master(tmp_path: Path) -> None:
    source = _write_master(tmp_path, name="master.txt")

    with pytest.raises(ValueError, match="extension .tex"):
        compile_publication_pdf(source)


def test_compile_publication_pdf_rejects_invalid_engine(tmp_path: Path) -> None:
    source = _write_master(tmp_path)

    with pytest.raises(ValueError, match="non pris en charge"):
        compile_publication_pdf(source, engine="latex")


def test_compile_publication_pdf_rejects_runs_less_than_one(tmp_path: Path) -> None:
    source = _write_master(tmp_path)

    with pytest.raises(ValueError, match="passes LaTeX"):
        compile_publication_pdf(source, runs=0)


def test_compile_publication_pdf_returns_result_when_engine_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_master(tmp_path)
    monkeypatch.setattr("shutil.which", lambda _engine: None)

    result = compile_publication_pdf(source, engine="xelatex")

    assert isinstance(result, PublicationPdfCompileResult)
    assert result.ok is False
    assert result.pdf_path is None
    assert result.returncode is None
    assert "introuvable" in result.message
    assert result.command == (
        "xelatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        "master.tex",
    )


def test_compile_publication_pdf_success_runs_in_master_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_master(tmp_path)
    runner = _RunRecorder(returncodes=[0])
    monkeypatch.setattr("shutil.which", lambda _engine: "xelatex")
    monkeypatch.setattr("subprocess.run", runner)

    result = compile_publication_pdf(source, runs=1)

    assert result.ok is True
    assert result.pdf_path == (tmp_path / "master.pdf").resolve()
    assert result.returncode == 0
    assert result.command[0] == "xelatex"
    assert len(runner.calls) == 1
    command, kwargs = runner.calls[0]
    assert command == list(result.command)
    assert kwargs["cwd"] == source.resolve().parent
    assert "shell" not in kwargs
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["encoding"] == "utf-8"
    assert kwargs["errors"] == "replace"


def test_compile_publication_pdf_failure_preserves_outputs_and_log(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_master(tmp_path)
    log = tmp_path / "master.log"
    log.write_text("log", encoding="utf-8")
    runner = _RunRecorder(returncodes=[1], create_pdf_on_success=False)
    monkeypatch.setattr("shutil.which", lambda _engine: "xelatex")
    monkeypatch.setattr("subprocess.run", runner)

    result = compile_publication_pdf(source, runs=2)

    assert result.ok is False
    assert result.returncode == 1
    assert result.pdf_path is None
    assert result.log_path == log.resolve()
    assert "stdout pass 1" in result.stdout
    assert "stderr pass 1" in result.stderr
    assert "echouee" in result.message
    assert len(runner.calls) == 1


def test_compile_publication_pdf_runs_twice_when_first_pass_succeeds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_master(tmp_path)
    runner = _RunRecorder(returncodes=[0, 0])
    monkeypatch.setattr("shutil.which", lambda _engine: "xelatex")
    monkeypatch.setattr("subprocess.run", runner)

    result = compile_publication_pdf(source, runs=2)

    assert result.ok is True
    assert len(runner.calls) == 2
    assert "stdout pass 1" in result.stdout
    assert "stdout pass 2" in result.stdout


def test_compile_publication_pdf_does_not_run_second_pass_after_first_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_master(tmp_path)
    runner = _RunRecorder(returncodes=[1, 0], create_pdf_on_success=False)
    monkeypatch.setattr("shutil.which", lambda _engine: "xelatex")
    monkeypatch.setattr("subprocess.run", runner)

    result = compile_publication_pdf(source, runs=2)

    assert result.ok is False
    assert len(runner.calls) == 1
