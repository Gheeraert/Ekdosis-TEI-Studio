from __future__ import annotations

import ftplib
import json
from pathlib import Path
from uuid import uuid4

import pytest

from ets.ftp_publish import (
    FTPPublicationConfig,
    FTPPublishService,
    ftp_publication_config_from_dict,
    ftp_publication_config_to_dict,
    load_ftp_publication_config,
    save_ftp_publication_config,
    validate_ftp_publication_config,
)


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = ROOT / "tests" / "_runtime"


def _runtime_dir(prefix: str) -> Path:
    target = RUNTIME_ROOT / f"{prefix}_{uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _sample_config() -> FTPPublicationConfig:
    return FTPPublicationConfig(
        host="ftp.example.org",
        port=21,
        username="login",
        password="plain-password",
        remote_dir="/www/site",
        use_tls=False,
        passive=True,
        timeout=30,
    )


def test_ftp_publication_config_json_roundtrip() -> None:
    runtime = _runtime_dir("ftp_config_roundtrip")
    config_path = runtime / "ftp_config.json"
    config = _sample_config()

    payload = ftp_publication_config_to_dict(config)
    assert payload == {
        "schema": "ets.ftp_publication_config",
        "version": 1,
        "host": "ftp.example.org",
        "port": 21,
        "username": "login",
        "password": "plain-password",
        "remote_dir": "/www/site",
        "use_tls": False,
        "passive": True,
        "timeout": 30,
    }

    rebuilt = ftp_publication_config_from_dict(payload)
    assert rebuilt == config

    written = save_ftp_publication_config(config, config_path)
    loaded = load_ftp_publication_config(written)
    assert written == config_path.resolve()
    assert loaded == config

    file_payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert file_payload["password"] == "plain-password"


@pytest.mark.parametrize(
    ("config", "expected_error"),
    [
        (FTPPublicationConfig(host="", username="user", remote_dir="/site"), "host"),
        (FTPPublicationConfig(host="ftp.example.org", username="", remote_dir="/site"), "username"),
        (FTPPublicationConfig(host="ftp.example.org", username="user", remote_dir=""), "remote_dir"),
        (FTPPublicationConfig(host="ftp.example.org", username="user", remote_dir="/site", port=0), "port"),
        (FTPPublicationConfig(host="ftp.example.org", username="user", remote_dir="/site", port=70000), "port"),
    ],
)
def test_ftp_publication_config_validation_errors(config: FTPPublicationConfig, expected_error: str) -> None:
    with pytest.raises(ValueError, match=expected_error):
        validate_ftp_publication_config(config)


class _FakeFTPClient:
    def __init__(self) -> None:
        self.connected_with: tuple[str, int, float | None] | None = None
        self.logged_with: tuple[str, str] | None = None
        self.passive: bool | None = None
        self.created_dirs: list[str] = []
        self.uploaded: list[tuple[str, bytes]] = []
        self.closed = False

    def connect(self, host: str = "", port: int = 0, timeout: float | None = None) -> str:
        self.connected_with = (host, port, timeout)
        return "ok"

    def login(self, user: str = "", passwd: str = "", acct: str = "") -> str:
        self.logged_with = (user, passwd)
        return "ok"

    def set_pasv(self, val: bool) -> None:
        self.passive = val

    def mkd(self, dirname: str) -> str:
        self.created_dirs.append(dirname)
        return dirname

    def storbinary(self, cmd: str, fp, blocksize: int = 8192, callback=None, rest=None) -> str:
        self.uploaded.append((cmd, fp.read()))
        return "ok"

    def quit(self) -> str:
        self.closed = True
        return "bye"

    def close(self) -> None:
        self.closed = True


def test_ftp_publish_service_uploads_recursively_and_creates_directories() -> None:
    runtime = _runtime_dir("ftp_service_recursive")
    local_dir = runtime / "site"
    (local_dir / "index.html").parent.mkdir(parents=True, exist_ok=True)
    (local_dir / "index.html").write_text("home", encoding="utf-8")
    (local_dir / "plays").mkdir(parents=True, exist_ok=True)
    (local_dir / "plays" / "andromaque.html").write_text("play", encoding="utf-8")

    fake = _FakeFTPClient()
    service = FTPPublishService(ftp_factory=lambda _use_tls, _timeout: fake)
    result = service.publish_directory(local_dir=local_dir, config=_sample_config())

    assert result.ok is True
    assert result.files_transferred == 2
    assert result.directories_created >= 2
    assert fake.connected_with is not None
    assert fake.connected_with[0] == "ftp.example.org"
    assert fake.logged_with == ("login", "plain-password")
    assert fake.passive is True
    uploaded_commands = [item[0] for item in fake.uploaded]
    assert "STOR /www/site/index.html" in uploaded_commands
    assert "STOR /www/site/plays/andromaque.html" in uploaded_commands
    assert fake.closed is True


class _FailingFTPClient(_FakeFTPClient):
    def __init__(self, *, failing_password: str) -> None:
        super().__init__()
        self._failing_password = failing_password

    def storbinary(self, cmd: str, fp, blocksize: int = 8192, callback=None, rest=None) -> str:
        raise ftplib.error_temp(f"Temporary error for {self._failing_password}")


def test_ftp_publish_service_never_exposes_password_in_repr_or_error_messages() -> None:
    runtime = _runtime_dir("ftp_service_no_password_leak")
    local_dir = runtime / "site"
    local_dir.mkdir(parents=True, exist_ok=True)
    (local_dir / "index.html").write_text("home", encoding="utf-8")
    password = "top-secret-password"
    config = FTPPublicationConfig(
        host="ftp.example.org",
        username="login",
        password=password,
        remote_dir="/www/site",
    )

    fake = _FailingFTPClient(failing_password=password)
    service = FTPPublishService(ftp_factory=lambda _use_tls, _timeout: fake)
    result = service.publish_directory(local_dir=local_dir, config=config)

    assert result.ok is False
    assert result.error_detail is not None
    assert password not in repr(config)
    assert password not in repr(result)
    assert password not in result.error_detail

