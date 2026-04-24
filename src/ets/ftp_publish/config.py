from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import FTPPublicationConfig, validate_ftp_publication_config


FTP_PUBLICATION_CONFIG_SCHEMA = "ets.ftp_publication_config"
FTP_PUBLICATION_CONFIG_VERSION = 1


def _expect_text(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Invalid FTP publication config: '{field_name}' must be a string.")
    return value.strip()


def _expect_int(value: Any, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Invalid FTP publication config: '{field_name}' must be an integer.")
    return value


def _expect_bool(value: Any, *, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"Invalid FTP publication config: '{field_name}' must be a boolean.")
    return value


def ftp_publication_config_to_dict(config: FTPPublicationConfig) -> dict[str, Any]:
    validate_ftp_publication_config(config)
    return {
        "schema": FTP_PUBLICATION_CONFIG_SCHEMA,
        "version": FTP_PUBLICATION_CONFIG_VERSION,
        "host": config.host.strip(),
        "port": int(config.port),
        "username": config.username.strip(),
        "password": config.password,
        "remote_dir": config.remote_dir.strip(),
        "use_tls": bool(config.use_tls),
        "passive": bool(config.passive),
        "timeout": int(config.timeout),
    }


def ftp_publication_config_from_dict(payload: dict[str, Any]) -> FTPPublicationConfig:
    schema = payload.get("schema")
    if schema != FTP_PUBLICATION_CONFIG_SCHEMA:
        raise ValueError(
            "Invalid FTP publication config: unsupported schema. "
            f"Expected '{FTP_PUBLICATION_CONFIG_SCHEMA}'."
        )
    version = payload.get("version")
    if version != FTP_PUBLICATION_CONFIG_VERSION:
        raise ValueError(
            "Invalid FTP publication config: unsupported version. "
            f"Expected {FTP_PUBLICATION_CONFIG_VERSION}."
        )

    config = FTPPublicationConfig(
        host=_expect_text(payload.get("host"), field_name="host"),
        port=_expect_int(payload.get("port"), field_name="port"),
        username=_expect_text(payload.get("username"), field_name="username"),
        password=_expect_text(payload.get("password"), field_name="password"),
        remote_dir=_expect_text(payload.get("remote_dir"), field_name="remote_dir"),
        use_tls=_expect_bool(payload.get("use_tls"), field_name="use_tls"),
        passive=_expect_bool(payload.get("passive"), field_name="passive"),
        timeout=_expect_int(payload.get("timeout"), field_name="timeout"),
    )
    validate_ftp_publication_config(config)
    return config


def save_ftp_publication_config(config: FTPPublicationConfig, output_path: str | Path) -> Path:
    target = Path(output_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = ftp_publication_config_to_dict(config)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def load_ftp_publication_config(config_path: str | Path) -> FTPPublicationConfig:
    path = Path(config_path).resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid FTP publication configuration JSON: {exc.msg}.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Invalid FTP publication config: root JSON value must be an object.")
    return ftp_publication_config_from_dict(payload)

