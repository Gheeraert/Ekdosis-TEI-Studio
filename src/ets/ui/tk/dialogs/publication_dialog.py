from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ets.application import (
    DramaticDocumentInput,
    DramaticPlayInput,
    NoticeInput,
    SiteAssetsInput,
    SiteIdentityInput,
    SitePublicationRequest,
)


@dataclass
class _PublicationVars:
    site_title: tk.StringVar
    site_subtitle: tk.StringVar
    project_name: tk.StringVar
    editor: tk.StringVar
    credits: tk.StringVar
    output_dir: tk.StringVar
    play_slug: tk.StringVar
    master_notice: tk.StringVar
    asset_directory: tk.StringVar
    show_xml_download: tk.BooleanVar
    publish_notices: tk.BooleanVar
    include_metadata: tk.BooleanVar
    resolve_notice_xincludes: tk.BooleanVar


class PublicationDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.title("Publication du site")
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)
        self.result: SitePublicationRequest | None = None

        self.vars = _PublicationVars(
            site_title=tk.StringVar(value=""),
            site_subtitle=tk.StringVar(value=""),
            project_name=tk.StringVar(value=""),
            editor=tk.StringVar(value=""),
            credits=tk.StringVar(value=""),
            output_dir=tk.StringVar(value=""),
            play_slug=tk.StringVar(value=""),
            master_notice=tk.StringVar(value=""),
            asset_directory=tk.StringVar(value=""),
            show_xml_download=tk.BooleanVar(value=False),
            publish_notices=tk.BooleanVar(value=True),
            include_metadata=tk.BooleanVar(value=True),
            resolve_notice_xincludes=tk.BooleanVar(value=True),
        )

        self._dramatic_entries: list[tuple[str, Path]] = []
        self._notice_paths: list[Path] = []
        self._logo_paths: list[Path] = []

        frame = ttk.Frame(self, padding=10)
        frame.grid(sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self._build_identity_section(frame, row=0)
        self._build_dramatic_section(frame, row=1)
        self._build_notice_section(frame, row=2)
        self._build_assets_section(frame, row=3)
        self._build_output_section(frame, row=4)
        self._build_mapping_section(frame, row=5)
        self._build_options_section(frame, row=6)

        buttons = ttk.Frame(frame)
        buttons.grid(row=7, column=0, sticky="e", pady=(10, 0))
        ttk.Button(buttons, text="Annuler", command=self._on_cancel).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(buttons, text="Générer le site", command=self._on_validate).grid(row=0, column=1)

    def _build_identity_section(self, parent: ttk.Frame, *, row: int) -> None:
        box = ttk.LabelFrame(parent, text="Identité du site")
        box.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        box.columnconfigure(1, weight=1)
        self._add_entry(box, 0, "Titre du site", self.vars.site_title)
        self._add_entry(box, 1, "Sous-titre", self.vars.site_subtitle)
        self._add_entry(box, 2, "Projet", self.vars.project_name)
        self._add_entry(box, 3, "Éditeur", self.vars.editor)
        self._add_entry(box, 4, "Crédits", self.vars.credits)
        ttk.Label(box, text="Introduction d'accueil").grid(row=5, column=0, sticky="nw", padx=(0, 6), pady=2)
        self.homepage_intro = tk.Text(box, height=3, wrap="word")
        self.homepage_intro.grid(row=5, column=1, sticky="ew", pady=2)

    def _build_dramatic_section(self, parent: ttk.Frame, *, row: int) -> None:
        box = ttk.LabelFrame(parent, text="XML dramatiques (groupés par pièce)")
        box.grid(row=row, column=0, sticky="nsew", pady=(0, 8))
        box.columnconfigure(0, weight=1)
        box.rowconfigure(1, weight=1)

        controls = ttk.Frame(box)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        controls.columnconfigure(1, weight=1)
        ttk.Label(controls, text="Slug de pièce").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Entry(controls, textvariable=self.vars.play_slug).grid(row=0, column=1, sticky="ew", padx=(0, 6))
        ttk.Button(controls, text="Ajouter XML…", command=self._add_dramatic_files).grid(row=0, column=2, padx=(0, 6))
        ttk.Button(controls, text="Supprimer sélection", command=self._remove_dramatic_selected).grid(row=0, column=3)

        lists = ttk.Frame(box)
        lists.grid(row=1, column=0, sticky="nsew")
        lists.columnconfigure(0, weight=2)
        lists.columnconfigure(1, weight=1)
        lists.rowconfigure(0, weight=1)

        self.dramatic_list = tk.Listbox(lists, height=6, selectmode=tk.EXTENDED)
        self.dramatic_list.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        order_box = ttk.LabelFrame(lists, text="Ordre des pièces")
        order_box.grid(row=0, column=1, sticky="nsew")
        order_box.columnconfigure(0, weight=1)
        order_box.rowconfigure(0, weight=1)
        self.play_order_list = tk.Listbox(order_box, height=6, selectmode=tk.SINGLE, exportselection=False)
        self.play_order_list.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        order_buttons = ttk.Frame(order_box)
        order_buttons.grid(row=1, column=0, sticky="e", padx=4, pady=(0, 4))
        ttk.Button(order_buttons, text="Monter", command=self._move_play_order_up).grid(row=0, column=0, padx=(0, 4))
        ttk.Button(order_buttons, text="Descendre", command=self._move_play_order_down).grid(row=0, column=1)

    def _build_notice_section(self, parent: ttk.Frame, *, row: int) -> None:
        box = ttk.LabelFrame(parent, text="Notices XML")
        box.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        box.columnconfigure(1, weight=1)
        ttk.Label(box, text="Notice maître").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        ttk.Entry(box, textvariable=self.vars.master_notice).grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Button(box, text="Choisir…", command=self._choose_master_notice).grid(row=0, column=2, padx=(6, 0), pady=2)

        extras = ttk.Frame(box)
        extras.grid(row=1, column=0, columnspan=3, sticky="ew")
        extras.columnconfigure(0, weight=1)
        self.notice_list = tk.Listbox(extras, height=4, selectmode=tk.EXTENDED)
        self.notice_list.grid(row=0, column=0, sticky="ew")
        notice_buttons = ttk.Frame(extras)
        notice_buttons.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        ttk.Button(notice_buttons, text="Ajouter…", command=self._add_notice_files).grid(row=0, column=0, pady=(0, 4))
        ttk.Button(notice_buttons, text="Supprimer", command=self._remove_notice_selected).grid(row=1, column=0)

    def _build_assets_section(self, parent: ttk.Frame, *, row: int) -> None:
        box = ttk.LabelFrame(parent, text="Assets (optionnel)")
        box.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        box.columnconfigure(1, weight=1)

        ttk.Label(box, text="Dossier assets").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        ttk.Entry(box, textvariable=self.vars.asset_directory).grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Button(box, text="Choisir…", command=self._choose_asset_directory).grid(row=0, column=2, padx=(6, 0), pady=2)

        logos = ttk.Frame(box)
        logos.grid(row=1, column=0, columnspan=3, sticky="ew")
        logos.columnconfigure(0, weight=1)
        self.logo_list = tk.Listbox(logos, height=3, selectmode=tk.EXTENDED)
        self.logo_list.grid(row=0, column=0, sticky="ew")
        logo_buttons = ttk.Frame(logos)
        logo_buttons.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        ttk.Button(logo_buttons, text="Ajouter logos…", command=self._add_logo_files).grid(row=0, column=0, pady=(0, 4))
        ttk.Button(logo_buttons, text="Supprimer", command=self._remove_logo_selected).grid(row=1, column=0)

    def _build_output_section(self, parent: ttk.Frame, *, row: int) -> None:
        box = ttk.LabelFrame(parent, text="Sortie")
        box.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        box.columnconfigure(1, weight=1)
        ttk.Label(box, text="Dossier de sortie").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        ttk.Entry(box, textvariable=self.vars.output_dir).grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Button(box, text="Choisir…", command=self._choose_output_directory).grid(row=0, column=2, padx=(6, 0), pady=2)

    def _build_mapping_section(self, parent: ttk.Frame, *, row: int) -> None:
        box = ttk.LabelFrame(parent, text="Associations pièce -> notice (optionnel)")
        box.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(box, text="Une association par ligne: play_slug|notice_slug").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.mapping_text = tk.Text(box, height=3, wrap="word")
        self.mapping_text.grid(row=1, column=0, sticky="ew")

    def _build_options_section(self, parent: ttk.Frame, *, row: int) -> None:
        box = ttk.LabelFrame(parent, text="Options")
        box.grid(row=row, column=0, sticky="ew")
        ttk.Checkbutton(box, text="Publier les notices", variable=self.vars.publish_notices).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(box, text="Activer les téléchargements XML", variable=self.vars.show_xml_download).grid(
            row=0, column=1, sticky="w", padx=(12, 0)
        )
        ttk.Checkbutton(box, text="Inclure les métadonnées", variable=self.vars.include_metadata).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(box, text="Résoudre les xi:include locaux", variable=self.vars.resolve_notice_xincludes).grid(
            row=1, column=1, sticky="w", padx=(12, 0)
        )

    @staticmethod
    def _add_entry(parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 6), pady=2)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=2)

    def _add_dramatic_files(self) -> None:
        play_slug = self.vars.play_slug.get().strip()
        if not play_slug:
            messagebox.showerror("Publication", "Le slug de pièce est requis avant l'ajout de fichiers.", parent=self)
            return
        chosen = filedialog.askopenfilenames(
            parent=self,
            title="Ajouter des XML dramatiques",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if not chosen:
            return
        self._add_dramatic_entries(play_slug, tuple(Path(item).resolve() for item in chosen))

    def _add_dramatic_entries(self, play_slug: str, paths: tuple[Path, ...]) -> None:
        normalized_slug = play_slug.strip()
        if not normalized_slug:
            return
        for path in paths:
            self._dramatic_entries.append((normalized_slug, path))
            self.dramatic_list.insert(tk.END, f"{normalized_slug} | {path}")
        existing_order = self._play_order_items()
        if normalized_slug not in existing_order:
            self.play_order_list.insert(tk.END, normalized_slug)

    def _remove_dramatic_selected(self) -> None:
        selected = list(self.dramatic_list.curselection())
        for index in reversed(selected):
            del self._dramatic_entries[index]
            self.dramatic_list.delete(index)
        self._sync_play_order_from_entries()

    def _sync_play_order_from_entries(self) -> None:
        current = self._play_order_items()
        active_slugs = [slug for slug, _path in self._dramatic_entries]
        unique_active: list[str] = []
        for slug in active_slugs:
            if slug not in unique_active:
                unique_active.append(slug)
        updated = [slug for slug in current if slug in unique_active]
        for slug in unique_active:
            if slug not in updated:
                updated.append(slug)
        self.play_order_list.delete(0, tk.END)
        for slug in updated:
            self.play_order_list.insert(tk.END, slug)

    def _move_play_order_up(self) -> None:
        selection = self.play_order_list.curselection()
        if not selection:
            return
        idx = selection[0]
        if idx <= 0:
            return
        value = self.play_order_list.get(idx)
        self.play_order_list.delete(idx)
        self.play_order_list.insert(idx - 1, value)
        self.play_order_list.selection_set(idx - 1)

    def _move_play_order_down(self) -> None:
        selection = self.play_order_list.curselection()
        if not selection:
            return
        idx = selection[0]
        end = self.play_order_list.size() - 1
        if idx >= end:
            return
        value = self.play_order_list.get(idx)
        self.play_order_list.delete(idx)
        self.play_order_list.insert(idx + 1, value)
        self.play_order_list.selection_set(idx + 1)

    def _choose_master_notice(self) -> None:
        chosen = filedialog.askopenfilename(
            parent=self,
            title="Choisir la notice maître",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if chosen:
            self.vars.master_notice.set(chosen)

    def _add_notice_files(self) -> None:
        chosen = filedialog.askopenfilenames(
            parent=self,
            title="Ajouter des notices XML",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if not chosen:
            return
        for item in chosen:
            path = Path(item).resolve()
            if path in self._notice_paths:
                continue
            self._notice_paths.append(path)
            self.notice_list.insert(tk.END, str(path))

    def _remove_notice_selected(self) -> None:
        for index in reversed(list(self.notice_list.curselection())):
            del self._notice_paths[index]
            self.notice_list.delete(index)

    def _choose_asset_directory(self) -> None:
        chosen = filedialog.askdirectory(parent=self, title="Choisir un dossier assets")
        if chosen:
            self.vars.asset_directory.set(chosen)

    def _add_logo_files(self) -> None:
        chosen = filedialog.askopenfilenames(
            parent=self,
            title="Ajouter des logos",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.svg *.gif *.webp"), ("All files", "*.*")],
        )
        if not chosen:
            return
        for item in chosen:
            path = Path(item).resolve()
            if path in self._logo_paths:
                continue
            self._logo_paths.append(path)
            self.logo_list.insert(tk.END, str(path))

    def _remove_logo_selected(self) -> None:
        for index in reversed(list(self.logo_list.curselection())):
            del self._logo_paths[index]
            self.logo_list.delete(index)

    def _choose_output_directory(self) -> None:
        chosen = filedialog.askdirectory(parent=self, title="Choisir le dossier de sortie")
        if chosen:
            self.vars.output_dir.set(chosen)

    def _play_order_items(self) -> list[str]:
        return [self.play_order_list.get(i) for i in range(self.play_order_list.size())]

    def _parse_explicit_mapping(self) -> tuple[tuple[str, str], ...]:
        lines = [line.strip() for line in self.mapping_text.get("1.0", "end-1c").splitlines() if line.strip()]
        pairs: list[tuple[str, str]] = []
        for line in lines:
            if "|" in line:
                left, right = line.split("|", maxsplit=1)
            elif "->" in line:
                left, right = line.split("->", maxsplit=1)
            else:
                raise ValueError("Format d'association invalide. Utilisez 'play_slug|notice_slug'.")
            play_slug = left.strip()
            notice_slug = right.strip()
            if not play_slug or not notice_slug:
                raise ValueError("Association pièce/notice invalide: slug vide.")
            pairs.append((play_slug, notice_slug))
        return tuple(pairs)

    def _collect_notice_inputs(self) -> tuple[NoticeInput, ...]:
        collected: list[Path] = []
        master = self.vars.master_notice.get().strip()
        if master:
            collected.append(Path(master).resolve())
        for path in self._notice_paths:
            if path not in collected:
                collected.append(path)
        return tuple(NoticeInput(source_path=path) for path in collected)

    def _build_request(self) -> SitePublicationRequest:
        site_title = self.vars.site_title.get().strip()
        if not site_title:
            raise ValueError("Le titre du site est requis.")
        output_dir_raw = self.vars.output_dir.get().strip()
        if not output_dir_raw:
            raise ValueError("Le dossier de sortie est requis.")
        if not self._dramatic_entries:
            raise ValueError("Ajoutez au moins un XML dramatique.")

        grouped: dict[str, list[DramaticDocumentInput]] = {}
        for play_slug, path in self._dramatic_entries:
            grouped.setdefault(play_slug, []).append(DramaticDocumentInput(source_path=path))

        play_order = self._play_order_items()
        if not play_order:
            play_order = list(grouped.keys())
        ordered_slugs = [slug for slug in play_order if slug in grouped]
        for slug in grouped:
            if slug not in ordered_slugs:
                ordered_slugs.append(slug)

        plays = tuple(
            DramaticPlayInput(
                play_slug=slug,
                documents=tuple(grouped[slug]),
            )
            for slug in ordered_slugs
        )

        asset_directory = self.vars.asset_directory.get().strip()
        assets = SiteAssetsInput(
            logo_files=tuple(self._logo_paths),
            asset_directories=(Path(asset_directory).resolve(),) if asset_directory else (),
        )

        identity = SiteIdentityInput(
            site_title=site_title,
            site_subtitle=self.vars.site_subtitle.get().strip(),
            project_name=self.vars.project_name.get().strip(),
            editor=self.vars.editor.get().strip(),
            credits=self.vars.credits.get().strip(),
            homepage_intro=self.homepage_intro.get("1.0", "end-1c").strip(),
        )

        return SitePublicationRequest(
            identity=identity,
            output_dir=Path(output_dir_raw).resolve(),
            plays=plays,
            play_order=tuple(ordered_slugs),
            notices=self._collect_notice_inputs(),
            assets=assets,
            show_xml_download=bool(self.vars.show_xml_download.get()),
            publish_notices=bool(self.vars.publish_notices.get()),
            include_metadata=bool(self.vars.include_metadata.get()),
            resolve_notice_xincludes=bool(self.vars.resolve_notice_xincludes.get()),
            play_notice_map=self._parse_explicit_mapping(),
        )

    def _on_validate(self) -> None:
        try:
            self.result = self._build_request()
        except ValueError as exc:
            messagebox.showerror("Publication", str(exc), parent=self)
            return
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()


def open_publication_dialog(parent: tk.Misc) -> SitePublicationRequest | None:
    dialog = PublicationDialog(parent)
    parent.wait_window(dialog)
    return dialog.result

