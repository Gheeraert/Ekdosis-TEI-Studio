from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import shutil
import subprocess


_ALLOWED_ENGINES = {"xelatex", "lualatex", "pdflatex"}


@dataclass(frozen=True)
class PublicationPdfCompileResult:
    ok: bool
    master_path: Path
    pdf_path: Path | None
    engine: str
    command: tuple[str, ...]
    returncode: int | None
    stdout: str
    stderr: str
    log_path: Path | None
    message: str
    error_detail: str | None = None
    runs_completed: int = 0
    converged: bool | None = None
    stability_confirmations: int = 0
    state_files: tuple[str, ...] = ()
    max_runs: int | None = None


def compile_publication_pdf(
    master_path: str | Path,
    *,
    engine: str = "lualatex",
    runs: int = 3,
    max_runs: int | None = None,
    stability_confirmations: int = 2,
    timeout_seconds: int = 120,
) -> PublicationPdfCompileResult:
    resolved_master = Path(master_path).resolve()
    _validate_compile_request(
        resolved_master,
        engine=engine,
        runs=runs,
        max_runs=max_runs,
        stability_confirmations=stability_confirmations,
    )

    command = (
        engine,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        resolved_master.name,
    )
    pdf_path = resolved_master.with_suffix(".pdf")
    log_path = resolved_master.with_suffix(".log")

    if shutil.which(engine) is None:
        return PublicationPdfCompileResult(
            ok=False,
            master_path=resolved_master,
            pdf_path=None,
            engine=engine,
            command=command,
            returncode=None,
            stdout="",
            stderr="",
            log_path=log_path if log_path.exists() else None,
            message=f"Moteur LaTeX introuvable: {engine}.",
            error_detail=f"L'executable '{engine}' est introuvable dans le PATH.",
            max_runs=max_runs,
        )

    _clean_previous_compile_artifacts(resolved_master)

    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    last_returncode: int | None = None
    runs_completed = 0
    last_state_digest: str | None = None
    confirmed_stability = 0
    state_files: tuple[str, ...] = ()
    target_runs = runs if max_runs is None else max_runs

    for run_index in range(1, target_runs + 1):
        try:
            completed = subprocess.run(
                list(command),
                cwd=resolved_master.parent,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
            )
        except FileNotFoundError as exc:
            return PublicationPdfCompileResult(
                ok=False,
                master_path=resolved_master,
                pdf_path=None,
                engine=engine,
                command=command,
                returncode=None,
                stdout="\n".join(stdout_parts),
                stderr="\n".join(stderr_parts),
                log_path=log_path if log_path.exists() else None,
                message=f"Moteur LaTeX introuvable: {engine}.",
                error_detail=str(exc),
                runs_completed=runs_completed,
                stability_confirmations=confirmed_stability,
                state_files=state_files,
                max_runs=max_runs,
            )
        except subprocess.TimeoutExpired as exc:
            stdout_parts.append(_decode_timeout_output(exc.stdout))
            stderr_parts.append(_decode_timeout_output(exc.stderr))
            return PublicationPdfCompileResult(
                ok=False,
                master_path=resolved_master,
                pdf_path=pdf_path if pdf_path.exists() else None,
                engine=engine,
                command=command,
                returncode=None,
                stdout="\n".join(part for part in stdout_parts if part),
                stderr="\n".join(part for part in stderr_parts if part),
                log_path=log_path if log_path.exists() else None,
                message=f"Compilation LaTeX interrompue apres {timeout_seconds} secondes.",
                error_detail=str(exc),
                runs_completed=runs_completed,
                stability_confirmations=confirmed_stability,
                state_files=state_files,
                max_runs=max_runs,
            )

        runs_completed = run_index
        last_returncode = completed.returncode
        stdout_parts.append(completed.stdout or "")
        stderr_parts.append(completed.stderr or "")
        if completed.returncode != 0:
            return PublicationPdfCompileResult(
                ok=False,
                master_path=resolved_master,
                pdf_path=pdf_path if pdf_path.exists() else None,
                engine=engine,
                command=command,
                returncode=completed.returncode,
                stdout="\n".join(part for part in stdout_parts if part),
                stderr="\n".join(part for part in stderr_parts if part),
                log_path=log_path if log_path.exists() else None,
                message=f"Compilation LaTeX echouee a la passe {run_index}.",
                error_detail=f"{engine} a retourne le code {completed.returncode}.",
                runs_completed=runs_completed,
                stability_confirmations=confirmed_stability,
                state_files=state_files,
                max_runs=max_runs,
            )

        if max_runs is not None:
            state_digest, state_files = _auxiliary_state_digest(resolved_master)
            if state_digest == last_state_digest:
                confirmed_stability += 1
            else:
                confirmed_stability = 0
                last_state_digest = state_digest
            if run_index >= runs and confirmed_stability >= stability_confirmations:
                if not pdf_path.exists():
                    return PublicationPdfCompileResult(
                        ok=False,
                        master_path=resolved_master,
                        pdf_path=None,
                        engine=engine,
                        command=command,
                        returncode=last_returncode,
                        stdout="\n".join(part for part in stdout_parts if part),
                        stderr="\n".join(part for part in stderr_parts if part),
                        log_path=log_path if log_path.exists() else None,
                        message="Compilation LaTeX stabilisee, mais aucun PDF n'a ete produit.",
                        error_detail=f"Fichier attendu introuvable: {pdf_path}.",
                        runs_completed=runs_completed,
                        converged=True,
                        stability_confirmations=confirmed_stability,
                        state_files=state_files,
                        max_runs=max_runs,
                    )
                return PublicationPdfCompileResult(
                    ok=True,
                    master_path=resolved_master,
                    pdf_path=pdf_path,
                    engine=engine,
                    command=command,
                    returncode=last_returncode,
                    stdout="\n".join(part for part in stdout_parts if part),
                    stderr="\n".join(part for part in stderr_parts if part),
                    log_path=log_path if log_path.exists() else None,
                    message=f"Compilation LaTeX reussie et stabilisee apres {run_index} passes.",
                    runs_completed=runs_completed,
                    converged=True,
                    stability_confirmations=confirmed_stability,
                    state_files=state_files,
                    max_runs=max_runs,
                )

    if not pdf_path.exists():
        return PublicationPdfCompileResult(
            ok=False,
            master_path=resolved_master,
            pdf_path=None,
            engine=engine,
            command=command,
            returncode=last_returncode,
            stdout="\n".join(part for part in stdout_parts if part),
            stderr="\n".join(part for part in stderr_parts if part),
            log_path=log_path if log_path.exists() else None,
            message="Compilation LaTeX terminee, mais aucun PDF n'a ete produit.",
            error_detail=f"Fichier attendu introuvable: {pdf_path}.",
            runs_completed=runs_completed,
            converged=False if max_runs is not None else None,
            stability_confirmations=confirmed_stability,
            state_files=state_files,
            max_runs=max_runs,
        )

    if max_runs is not None:
        return PublicationPdfCompileResult(
            ok=False,
            master_path=resolved_master,
            pdf_path=pdf_path,
            engine=engine,
            command=command,
            returncode=last_returncode,
            stdout="\n".join(part for part in stdout_parts if part),
            stderr="\n".join(part for part in stderr_parts if part),
            log_path=log_path if log_path.exists() else None,
            message=f"PDF produit, mais compilation non stabilisee apres {max_runs} passes.",
            error_detail="L'etat auxiliaire a continue d'evoluer jusqu'au plafond de passes.",
            runs_completed=runs_completed,
            converged=False,
            stability_confirmations=confirmed_stability,
            state_files=state_files,
            max_runs=max_runs,
        )

    return PublicationPdfCompileResult(
        ok=True,
        master_path=resolved_master,
        pdf_path=pdf_path,
        engine=engine,
        command=command,
        returncode=last_returncode,
        stdout="\n".join(part for part in stdout_parts if part),
        stderr="\n".join(part for part in stderr_parts if part),
        log_path=log_path if log_path.exists() else None,
        message="Compilation LaTeX reussie.",
        runs_completed=runs_completed,
        converged=None,
        max_runs=max_runs,
    )


def _validate_compile_request(
    master_path: Path,
    *,
    engine: str,
    runs: int,
    max_runs: int | None,
    stability_confirmations: int,
) -> None:
    if engine not in _ALLOWED_ENGINES:
        allowed = ", ".join(sorted(_ALLOWED_ENGINES))
        raise ValueError(f"Moteur LaTeX non pris en charge: {engine}. Valeurs autorisees: {allowed}.")
    if runs < 1:
        raise ValueError("Le nombre de passes LaTeX doit etre superieur ou egal a 1.")
    if max_runs is not None and max_runs < runs:
        raise ValueError("Le plafond de passes LaTeX doit etre superieur ou egal au nombre minimal de passes.")
    if max_runs is not None and stability_confirmations < 1:
        raise ValueError("Le nombre de confirmations de stabilite doit etre superieur ou egal a 1.")
    if not master_path.exists() or not master_path.is_file():
        raise ValueError(f"Fichier master.tex introuvable: {master_path}.")
    if master_path.suffix.lower() != ".tex":
        raise ValueError(f"Le fichier master doit avoir l'extension .tex: {master_path}.")


def _clean_previous_compile_artifacts(master_path: Path) -> None:
    stem = master_path.stem
    for artifact in master_path.parent.glob(f"{stem}.*"):
        if artifact.resolve() == master_path:
            continue
        if artifact.is_file():
            artifact.unlink()


def _auxiliary_state_digest(master_path: Path) -> tuple[str, tuple[str, ...]]:
    stem = master_path.stem
    excluded = {
        f"{stem}.tex",
        f"{stem}.pdf",
        f"{stem}.log",
        f"{stem}.synctex.gz",
        f"{stem}.fls",
        f"{stem}.fdb_latexmk",
    }
    files = [
        path
        for path in master_path.parent.glob(f"{stem}.*")
        if path.is_file() and path.name not in excluded
    ]
    files.sort(key=lambda path: path.name)
    digest = hashlib.sha256()
    names: list[str] = []
    for path in files:
        names.append(path.name)
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest(), tuple(names)


def _decode_timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
