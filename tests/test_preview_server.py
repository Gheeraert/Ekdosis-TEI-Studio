from __future__ import annotations

from pathlib import Path
import socket
from uuid import uuid4

from ets.infrastructure import LocalPreviewServer


def _runtime_dir(name: str) -> Path:
    root = Path(__file__).resolve().parents[1] / "tests" / "_runtime"
    root.mkdir(exist_ok=True)
    path = root / f"{name}_{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_preview_server_starts_reuses_and_builds_url() -> None:
    server = LocalPreviewServer(root_dir=_runtime_dir("preview"), preferred_port=0)
    try:
        first_port = server.ensure_running()
        second_port = server.ensure_running()
        assert first_port == second_port

        url = server.publish_html("<html><body>ok</body></html>", filename="preview_test.html")
        assert url.startswith(f"http://127.0.0.1:{first_port}/preview_test.html")
        assert (server.root_dir / "preview_test.html").exists()
    finally:
        server.stop()


def test_preview_server_falls_back_when_preferred_port_is_unavailable() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied_port = int(occupied.getsockname()[1])
        server = LocalPreviewServer(root_dir=_runtime_dir("preview_fallback"), preferred_port=occupied_port)
        try:
            actual_port = server.ensure_running()
            assert actual_port != occupied_port
        finally:
            server.stop()
