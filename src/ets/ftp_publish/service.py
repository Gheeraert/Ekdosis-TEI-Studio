from __future__ import annotations

import ftplib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Protocol

from .models import FTPPublicationConfig, validate_ftp_publication_config


class FTPClientProtocol(Protocol):
    def connect(self, host: str = "", port: int = 0, timeout: float | None = None) -> str: ...
    def login(self, user: str = "", passwd: str = "", acct: str = "") -> str: ...
    def set_pasv(self, val: bool) -> None: ...
    def mkd(self, dirname: str) -> str: ...
    def storbinary(self, cmd: str, fp, blocksize: int = 8192, callback=None, rest=None) -> str: ...
    def quit(self) -> str: ...
    def close(self) -> None: ...


@dataclass(frozen=True)
class FTPPublishResult:
    ok: bool
    files_transferred: int = 0
    directories_created: int = 0
    warnings: tuple[str, ...] = ()
    message: str = ""
    error_detail: str | None = None


class FTPPublishService:
    def __init__(
        self,
        *,
        ftp_factory: Callable[[bool, float], FTPClientProtocol] | None = None,
    ) -> None:
        self._ftp_factory = ftp_factory or self._default_ftp_factory

    def publish_directory(self, *, local_dir: str | Path, config: FTPPublicationConfig) -> FTPPublishResult:
        try:
            validate_ftp_publication_config(config)
        except ValueError as exc:
            return FTPPublishResult(ok=False, message="Invalid FTP configuration.", error_detail=str(exc))

        source_dir = Path(local_dir).resolve()
        if not source_dir.exists():
            return FTPPublishResult(
                ok=False,
                message="FTP publication failed.",
                error_detail=f"Local directory does not exist: {source_dir}",
            )
        if not source_dir.is_dir():
            return FTPPublishResult(
                ok=False,
                message="FTP publication failed.",
                error_detail=f"Local path is not a directory: {source_dir}",
            )

        warnings: list[str] = []
        files_transferred = 0
        directories_created = 0
        ensured_directories: set[str] = set()
        ftp: FTPClientProtocol | None = None
        try:
            ftp = self._ftp_factory(config.use_tls, float(config.timeout))
            ftp.connect(config.host.strip(), int(config.port), timeout=float(config.timeout))
            ftp.login(user=config.username.strip(), passwd=config.password)
            if config.use_tls and hasattr(ftp, "prot_p"):
                getattr(ftp, "prot_p")()
            ftp.set_pasv(bool(config.passive))

            remote_root = _normalize_remote_dir(config.remote_dir)
            directories_created += _ensure_remote_directory_tree(
                ftp,
                remote_root,
                ensured_directories=ensured_directories,
            )

            for root, dirs, files in source_dir.walk(top_down=True):
                dirs.sort()
                files.sort()
                relative_dir = root.relative_to(source_dir)
                remote_dir = _join_remote_path(remote_root, relative_dir)
                directories_created += _ensure_remote_directory_tree(
                    ftp,
                    remote_dir,
                    ensured_directories=ensured_directories,
                )

                for file_name in files:
                    local_path = root / file_name
                    remote_path = _join_remote_path(remote_dir, PurePosixPath(file_name))
                    with local_path.open("rb") as stream:
                        ftp.storbinary(f"STOR {remote_path.as_posix()}", stream)
                    files_transferred += 1

            if files_transferred == 0:
                warnings.append("No files found in local directory; nothing was uploaded.")

            return FTPPublishResult(
                ok=True,
                files_transferred=files_transferred,
                directories_created=directories_created,
                warnings=tuple(warnings),
                message="FTP publication completed successfully.",
            )
        except ftplib.all_errors as exc:
            return FTPPublishResult(
                ok=False,
                files_transferred=files_transferred,
                directories_created=directories_created,
                warnings=tuple(warnings),
                message="FTP publication failed.",
                error_detail=_sanitize_ftp_message(str(exc), password=config.password),
            )
        finally:
            if ftp is not None:
                try:
                    ftp.quit()
                except ftplib.all_errors:
                    ftp.close()

    @staticmethod
    def _default_ftp_factory(use_tls: bool, timeout: float) -> FTPClientProtocol:
        if use_tls:
            return ftplib.FTP_TLS(timeout=timeout)
        return ftplib.FTP(timeout=timeout)


def publish_directory_via_ftp(*, local_dir: str | Path, config: FTPPublicationConfig) -> FTPPublishResult:
    return FTPPublishService().publish_directory(local_dir=local_dir, config=config)


def _normalize_remote_dir(remote_dir: str) -> PurePosixPath:
    stripped = remote_dir.strip()
    if not stripped:
        raise ValueError("FTP remote_dir is required.")
    normalized = PurePosixPath(stripped)
    if normalized.as_posix() == ".":
        return PurePosixPath("/")
    return normalized


def _join_remote_path(base: PurePosixPath, suffix: PurePosixPath) -> PurePosixPath:
    if str(suffix) in {"", "."}:
        return base
    return base / suffix


def _ensure_remote_directory_tree(
    ftp: FTPClientProtocol,
    remote_dir: PurePosixPath,
    *,
    ensured_directories: set[str],
) -> int:
    created = 0
    path_text = remote_dir.as_posix()
    if path_text in ensured_directories:
        return 0

    if path_text.startswith("/"):
        current = PurePosixPath("/")
    else:
        current = PurePosixPath("")

    for part in remote_dir.parts:
        if part in {"", "/"}:
            continue
        current = current / part
        current_text = current.as_posix()
        if current_text in ensured_directories:
            continue
        try:
            ftp.mkd(current_text)
            created += 1
        except ftplib.error_perm as exc:
            message = str(exc).lower()
            if "exist" not in message and "exists" not in message and "file exists" not in message:
                raise
        ensured_directories.add(current_text)

    ensured_directories.add(path_text)
    return created


def _sanitize_ftp_message(message: str, *, password: str) -> str:
    text = message.strip() or "Unknown FTP error."
    if password:
        return text.replace(password, "***")
    return text
