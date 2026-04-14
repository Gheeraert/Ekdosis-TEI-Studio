from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
from threading import Thread
from urllib.parse import quote


def _default_preview_dir() -> Path:
    return Path.home() / ".ets_teistudio_v2" / "preview"


class LocalPreviewServer:
    """Small local HTTP server for rendering generated preview HTML in a browser."""

    def __init__(self, root_dir: Path | None = None, host: str = "127.0.0.1", preferred_port: int = 8765) -> None:
        self.root_dir = root_dir or _default_preview_dir()
        self.host = host
        self.preferred_port = preferred_port
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None

    @property
    def port(self) -> int | None:
        if self._httpd is None:
            return None
        return int(self._httpd.server_port)

    def ensure_running(self) -> int:
        if self._httpd is not None:
            return int(self._httpd.server_port)

        self.root_dir.mkdir(parents=True, exist_ok=True)
        handler_factory = partial(SimpleHTTPRequestHandler, directory=str(self.root_dir))
        port = self._select_port()
        self._httpd = ThreadingHTTPServer((self.host, port), handler_factory)
        self._thread = Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return int(self._httpd.server_port)

    def publish_html(self, html: str, filename: str = "preview.html") -> str:
        self.ensure_running()
        target = self.root_dir / filename
        target.write_text(html, encoding="utf-8")
        return self.url_for(filename)

    def url_for(self, filename: str) -> str:
        if self._httpd is None:
            raise RuntimeError("Preview server is not running.")
        escaped = quote(filename)
        return f"http://{self.host}:{self._httpd.server_port}/{escaped}"

    def stop(self) -> None:
        if self._httpd is None:
            return
        self._httpd.shutdown()
        self._httpd.server_close()
        self._httpd = None
        self._thread = None

    def _select_port(self) -> int:
        if self._port_available(self.preferred_port):
            return self.preferred_port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((self.host, 0))
            return int(sock.getsockname()[1])

    def _port_available(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((self.host, port))
            except OSError:
                return False
        return True
