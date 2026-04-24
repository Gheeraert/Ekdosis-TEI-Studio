from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ets.ftp_publish import (
    FTPPublicationConfig,
    load_ftp_publication_config,
    save_ftp_publication_config,
    validate_ftp_publication_config,
)


@dataclass
class _FTPVars:
    host: tk.StringVar
    port: tk.StringVar
    username: tk.StringVar
    password: tk.StringVar
    remote_dir: tk.StringVar
    use_tls: tk.BooleanVar
    passive: tk.BooleanVar
    timeout: tk.StringVar


class FTPPublicationDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, *, initial_config: FTPPublicationConfig | None = None) -> None:
        super().__init__(parent)
        self.title("Publication FTP")
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.resizable(True, True)
        self.geometry("760x520")
        self.minsize(700, 460)
        self.result: FTPPublicationConfig | None = None
        self._config_path: Path | None = None

        initial = initial_config or FTPPublicationConfig(host="", port=21, remote_dir="/", timeout=30)
        self.vars = _FTPVars(
            host=tk.StringVar(value=initial.host),
            port=tk.StringVar(value=str(initial.port)),
            username=tk.StringVar(value=initial.username),
            password=tk.StringVar(value=initial.password),
            remote_dir=tk.StringVar(value=initial.remote_dir),
            use_tls=tk.BooleanVar(value=initial.use_tls),
            passive=tk.BooleanVar(value=initial.passive),
            timeout=tk.StringVar(value=str(initial.timeout)),
        )

        body = ttk.Frame(self, padding=10)
        body.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(8, weight=1)

        self._add_entry(body, 0, "Host", self.vars.host)
        self._add_entry(body, 1, "Port", self.vars.port)
        self._add_entry(body, 2, "Username", self.vars.username)
        self._add_entry(body, 3, "Password", self.vars.password, show="*")
        self._add_entry(body, 4, "Remote dir", self.vars.remote_dir)
        self._add_entry(body, 5, "Timeout (s)", self.vars.timeout)

        options = ttk.Frame(body)
        options.grid(row=6, column=0, columnspan=2, sticky="w", pady=(6, 2))
        ttk.Checkbutton(options, text="Use TLS (FTP_TLS)", variable=self.vars.use_tls).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(options, text="Passive mode", variable=self.vars.passive).grid(row=0, column=1, sticky="w", padx=(12, 0))

        warning = (
            "Warning: the FTP password is stored in clear text in JSON. "
            "Do not share or version this file."
        )
        ttk.Label(body, text=warning, foreground="#8a2d2d", wraplength=680, justify="left").grid(
            row=7,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 0),
        )

        buttons = ttk.Frame(body)
        buttons.grid(row=9, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(buttons, text="Charger config...", command=self._on_load_config).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(buttons, text="Enregistrer config...", command=self._on_save_config).grid(row=0, column=1, padx=(0, 12))
        ttk.Button(buttons, text="Annuler", command=self._on_cancel).grid(row=0, column=2, padx=(0, 6))
        ttk.Button(buttons, text="Publier", command=self._on_publish).grid(row=0, column=3)

    @staticmethod
    def _add_entry(parent: ttk.Frame, row: int, label: str, variable: tk.StringVar, *, show: str | None = None) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
        entry_kwargs: dict[str, object] = {"textvariable": variable}
        if show is not None:
            entry_kwargs["show"] = show
        ttk.Entry(parent, **entry_kwargs).grid(row=row, column=1, sticky="ew", pady=3)

    def _collect_config(self) -> FTPPublicationConfig:
        try:
            port = int(self.vars.port.get().strip())
        except ValueError as exc:
            raise ValueError("FTP port must be an integer.") from exc
        try:
            timeout = int(self.vars.timeout.get().strip())
        except ValueError as exc:
            raise ValueError("FTP timeout must be an integer.") from exc

        config = FTPPublicationConfig(
            host=self.vars.host.get().strip(),
            port=port,
            username=self.vars.username.get().strip(),
            password=self.vars.password.get(),
            remote_dir=self.vars.remote_dir.get().strip(),
            use_tls=bool(self.vars.use_tls.get()),
            passive=bool(self.vars.passive.get()),
            timeout=timeout,
        )
        validate_ftp_publication_config(config)
        return config

    def _apply_config(self, config: FTPPublicationConfig) -> None:
        self.vars.host.set(config.host)
        self.vars.port.set(str(config.port))
        self.vars.username.set(config.username)
        self.vars.password.set(config.password)
        self.vars.remote_dir.set(config.remote_dir)
        self.vars.use_tls.set(config.use_tls)
        self.vars.passive.set(config.passive)
        self.vars.timeout.set(str(config.timeout))

    def _on_load_config(self) -> None:
        chosen = filedialog.askopenfilename(
            parent=self,
            title="Charger une configuration FTP",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not chosen:
            return
        try:
            config = load_ftp_publication_config(chosen)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Publication FTP", str(exc), parent=self)
            return
        self._apply_config(config)
        self._config_path = Path(chosen).resolve()
        messagebox.showinfo("Publication FTP", f"Configuration FTP chargee:\n{self._config_path}", parent=self)

    def _on_save_config(self) -> None:
        try:
            config = self._collect_config()
        except ValueError as exc:
            messagebox.showerror("Publication FTP", str(exc), parent=self)
            return

        chosen = filedialog.asksaveasfilename(
            parent=self,
            title="Enregistrer une configuration FTP",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=(self._config_path.name if self._config_path is not None else "ftp_config.json"),
        )
        if not chosen:
            return
        try:
            path = save_ftp_publication_config(config, chosen)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Publication FTP", str(exc), parent=self)
            return
        self._config_path = path
        messagebox.showinfo("Publication FTP", f"Configuration FTP enregistree:\n{path}", parent=self)

    def _on_publish(self) -> None:
        try:
            self.result = self._collect_config()
        except ValueError as exc:
            messagebox.showerror("Publication FTP", str(exc), parent=self)
            return
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()


def open_ftp_publication_dialog(
    parent: tk.Misc,
    *,
    initial_config: FTPPublicationConfig | None = None,
) -> FTPPublicationConfig | None:
    dialog = FTPPublicationDialog(parent, initial_config=initial_config)
    parent.wait_window(dialog)
    return dialog.result

