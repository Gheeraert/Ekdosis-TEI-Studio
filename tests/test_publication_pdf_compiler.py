from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from ets.publication_pdf import PublicationPdfCompileResult, compile_publication_pdf


class _RunRecorder:
    def __init__(
        self,
        *,
        returncodes: list[int],
        create_pdf_on_success: bool = True,
        states: list[dict[str, str | None]] | None = None,
        stdout: str | None = None,
    ) -> None:
        self.returncodes = returncodes
        self.create_pdf_on_success = create_pdf_on_success
        self.states = states or []
        self.stdout = stdout
        self.calls: list[tuple[list[str], dict[str, object]]] = []

    def __call__(self, command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        self.calls.append((command, kwargs))
        pass_index = len(self.calls)
        returncode = self.returncodes[min(pass_index - 1, len(self.returncodes) - 1)]
        cwd = Path(kwargs["cwd"])  # type: ignore[arg-type]
        if returncode == 0 and self.create_pdf_on_success:
            (cwd / "master.pdf").write_text("pdf", encoding="utf-8")
        if pass_index <= len(self.states):
            for name, content in self.states[pass_index - 1].items():
                target = cwd / name
                if content is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_text(content, encoding="utf-8")
        return subprocess.CompletedProcess(
            command,
            returncode,
            stdout=self.stdout if self.stdout is not None else f"stdout pass {pass_index}",
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
    monkeypatch.setattr("shutil.which", lambda _engine: "lualatex")
    monkeypatch.setattr("subprocess.run", runner)

    result = compile_publication_pdf(source, runs=1)

    assert result.ok is True
    assert result.pdf_path == (tmp_path / "master.pdf").resolve()
    assert result.returncode == 0
    assert result.command[0] == "lualatex"
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
    runner = _RunRecorder(returncodes=[1], create_pdf_on_success=False, states=[{"master.log": "log"}])
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


def test_compile_publication_pdf_runs_three_times_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_master(tmp_path)
    runner = _RunRecorder(returncodes=[0, 0, 0])
    monkeypatch.setattr("shutil.which", lambda _engine: "lualatex")
    monkeypatch.setattr("subprocess.run", runner)

    result = compile_publication_pdf(source)

    assert result.ok is True
    assert result.command[0] == "lualatex"
    assert len(runner.calls) == 3
    assert "stdout pass 1" in result.stdout
    assert "stdout pass 2" in result.stdout
    assert "stdout pass 3" in result.stdout


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


def test_compile_publication_pdf_preserves_timeout_behavior(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_master(tmp_path)

    def _timeout(_command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        (tmp_path / "master.pdf").write_text("partial pdf", encoding="utf-8")
        raise subprocess.TimeoutExpired("lualatex", 120, output="partial stdout", stderr="partial stderr")

    monkeypatch.setattr("shutil.which", lambda _engine: "lualatex")
    monkeypatch.setattr("subprocess.run", _timeout)

    result = compile_publication_pdf(source, max_runs=12)

    assert result.ok is False
    assert result.pdf_path == (tmp_path / "master.pdf").resolve()
    assert result.returncode is None
    assert result.runs_completed == 0
    assert "partial stdout" in result.stdout
    assert "partial stderr" in result.stderr
    assert "interrompue" in result.message


def test_compile_publication_pdf_adaptive_stops_after_immediate_stability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_master(tmp_path)
    runner = _RunRecorder(
        returncodes=[0, 0, 0, 0],
        states=[
            {"master.aux": "same", "master.1": "same"},
            {"master.aux": "same", "master.1": "same"},
            {"master.aux": "same", "master.1": "same"},
            {"master.aux": "unused"},
        ],
    )
    monkeypatch.setattr("shutil.which", lambda _engine: "lualatex")
    monkeypatch.setattr("subprocess.run", runner)

    result = compile_publication_pdf(source, runs=3, max_runs=12, stability_confirmations=2)

    assert result.ok is True
    assert result.converged is True
    assert result.runs_completed == 3
    assert result.stability_confirmations == 2
    assert len(runner.calls) == 3
    assert result.state_files == ("master.1", "master.aux")


def test_compile_publication_pdf_adaptive_stops_after_late_stability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_master(tmp_path)
    states = [{"master.aux": f"state {index}"} for index in range(1, 8)]
    states.extend([
        {"master.aux": "stable", "master.1": "stable"},
        {"master.aux": "stable", "master.1": "stable"},
        {"master.aux": "stable", "master.1": "stable"},
        {"master.aux": "unused"},
    ])
    runner = _RunRecorder(returncodes=[0] * 12, states=states)
    monkeypatch.setattr("shutil.which", lambda _engine: "lualatex")
    monkeypatch.setattr("subprocess.run", runner)

    result = compile_publication_pdf(source, runs=3, max_runs=12, stability_confirmations=2)

    assert result.ok is True
    assert result.converged is True
    assert result.runs_completed == 10
    assert len(runner.calls) == 10


def test_compile_publication_pdf_resets_stability_when_numeric_auxiliary_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_master(tmp_path)
    runner = _RunRecorder(
        returncodes=[0] * 12,
        states=[
            {"master.aux": "a", "master.17": "one"},
            {"master.aux": "a", "master.17": "one"},
            {"master.aux": "a", "master.17": "two"},
            {"master.aux": "a", "master.17": "two"},
            {"master.aux": "a", "master.17": "two"},
        ],
    )
    monkeypatch.setattr("shutil.which", lambda _engine: "lualatex")
    monkeypatch.setattr("subprocess.run", runner)

    result = compile_publication_pdf(source, runs=1, max_runs=12, stability_confirmations=2)

    assert result.ok is True
    assert result.runs_completed == 5
    assert len(runner.calls) == 5


def test_compile_publication_pdf_detects_auxiliary_appearance_and_disappearance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_master(tmp_path)
    runner = _RunRecorder(
        returncodes=[0] * 12,
        states=[
            {"master.aux": "a"},
            {"master.aux": "a", "master.44": "new"},
            {"master.aux": "a", "master.44": None},
            {"master.aux": "a"},
            {"master.aux": "a"},
        ],
    )
    monkeypatch.setattr("shutil.which", lambda _engine: "lualatex")
    monkeypatch.setattr("subprocess.run", runner)

    result = compile_publication_pdf(source, runs=1, max_runs=12, stability_confirmations=2)

    assert result.ok is True
    assert result.runs_completed == 5


def test_compile_publication_pdf_ignores_pdf_and_log_for_stability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_master(tmp_path)
    runner = _RunRecorder(
        returncodes=[0, 0, 0],
        states=[
            {"master.aux": "same", "master.log": "log 1", "master.pdf": "pdf 1"},
            {"master.aux": "same", "master.log": "log 2", "master.pdf": "pdf 2"},
            {"master.aux": "same", "master.log": "log 3", "master.pdf": "pdf 3"},
        ],
    )
    monkeypatch.setattr("shutil.which", lambda _engine: "lualatex")
    monkeypatch.setattr("subprocess.run", runner)

    result = compile_publication_pdf(source, runs=1, max_runs=12, stability_confirmations=2)

    assert result.ok is True
    assert result.converged is True
    assert result.runs_completed == 3
    assert result.state_files == ("master.aux",)


def test_compile_publication_pdf_ignores_residual_reledmac_reminder_when_state_is_stable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_master(tmp_path)
    reminder = "\n".join(
        [
            "reledmac reminder:",
            " The number of the footnotes in this section has changed since the last run.",
            " You will need to run LaTeX two more times before the footnote placement",
            " and line numbering in this section are correct.",
        ]
    )
    runner = _RunRecorder(
        returncodes=[0, 0, 0],
        states=[
            {"master.aux": "same", "master.1": "same"},
            {"master.aux": "same", "master.1": "same"},
            {"master.aux": "same", "master.1": "same"},
        ],
        stdout=reminder,
    )
    monkeypatch.setattr("shutil.which", lambda _engine: "lualatex")
    monkeypatch.setattr("subprocess.run", runner)

    result = compile_publication_pdf(source, runs=1, max_runs=12, stability_confirmations=2)

    assert result.ok is True
    assert result.converged is True
    assert "reledmac reminder" in result.stdout


def test_compile_publication_pdf_reports_unstable_state_at_max_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_master(tmp_path)
    runner = _RunRecorder(
        returncodes=[0] * 12,
        states=[{"master.aux": f"state {index}"} for index in range(12)],
    )
    monkeypatch.setattr("shutil.which", lambda _engine: "lualatex")
    monkeypatch.setattr("subprocess.run", runner)

    result = compile_publication_pdf(source, runs=3, max_runs=12, stability_confirmations=2)

    assert result.ok is False
    assert result.converged is False
    assert result.runs_completed == 12
    assert result.pdf_path == (tmp_path / "master.pdf").resolve()
    assert "non stabilisee" in result.message


def test_compile_publication_pdf_rejects_max_runs_less_than_runs(tmp_path: Path) -> None:
    source = _write_master(tmp_path)

    with pytest.raises(ValueError, match="plafond"):
        compile_publication_pdf(source, runs=3, max_runs=2)


def test_compile_publication_pdf_rejects_zero_stability_confirmations(tmp_path: Path) -> None:
    source = _write_master(tmp_path)

    with pytest.raises(ValueError, match="confirmations"):
        compile_publication_pdf(source, max_runs=12, stability_confirmations=0)
