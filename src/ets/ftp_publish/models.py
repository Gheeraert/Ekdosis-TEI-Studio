from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FTPPublicationConfig:
    host: str
    port: int = 21
    username: str = ""
    password: str = field(default="", repr=False)
    remote_dir: str = "/"
    use_tls: bool = False
    passive: bool = True
    timeout: int = 30


def validate_ftp_publication_config(config: FTPPublicationConfig) -> None:
    if not config.host.strip():
        raise ValueError("FTP host is required.")
    if not config.username.strip():
        raise ValueError("FTP username is required.")
    if not config.remote_dir.strip():
        raise ValueError("FTP remote_dir is required.")
    if config.port < 1 or config.port > 65535:
        raise ValueError("FTP port must be between 1 and 65535.")
    if config.timeout <= 0:
        raise ValueError("FTP timeout must be a positive integer.")

