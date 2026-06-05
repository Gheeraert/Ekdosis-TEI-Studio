from __future__ import annotations

from dataclasses import dataclass
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


def compile_publication_pdf(
    master_path: str | Path,
    *,
    engine: str = "xelatex",
    runs: int = 2,
    timeout_seconds: int = 120,
) -> PublicationPdfCompileResult:
    resolved_master = Path(master_path).resolve()
    _validate_compile_request(resolved_master, engine=engine, runs=runs)

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
        )

    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    last_returncode: int | None = None

    for run_index in range(1, runs + 1):
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
            )

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
    )


def _validate_compile_request(master_path: Path, *, engine: str, runs: int) -> None:
    if engine not in _ALLOWED_ENGINES:
        allowed = ", ".join(sorted(_ALLOWED_ENGINES))
        raise ValueError(f"Moteur LaTeX non pris en charge: {engine}. Valeurs autorisees: {allowed}.")
    if runs < 1:
        raise ValueError("Le nombre de passes LaTeX doit etre superieur ou egal a 1.")
    if not master_path.exists() or not master_path.is_file():
        raise ValueError(f"Fichier master.tex introuvable: {master_path}.")
    if master_path.suffix.lower() != ".tex":
        raise ValueError(f"Le fichier master doit avoir l'extension .tex: {master_path}.")


def _decode_timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
