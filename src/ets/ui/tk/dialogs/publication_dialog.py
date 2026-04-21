from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ets.application import (
    SitePublicationDialogConfig,
    SitePublicationDialogPlayConfig,
    SitePublicationRequest,
    derive_corpus_slug,
    load_site_publication_dialog_config,
    normalize_publication_identifier,
    save_site_publication_dialog_config,
    site_publication_request_from_dialog_config,
)


@dataclass
class _PublicationVars:
    author_name: tk.StringVar
    corpus_title: tk.StringVar
    scientific_editor: tk.StringVar
    corpus_slug: tk.StringVar
    home_page_tei: tk.StringVar
    general_intro_tei: tk.StringVar
    asset_directory: tk.StringVar
    output_dir: tk.StringVar
    show_xml_download: tk.BooleanVar
    publish_notices: tk.BooleanVar
    publish_prefaces: tk.BooleanVar
    include_metadata: tk.BooleanVar
    resolve_notice_xincludes: tk.BooleanVar


@dataclass
class _PlayEntry:
    play_slug: str
    dramatic_xml_path: Path
    notice_xml_path: Path | None = None
    preface_xml_path: Path | None = None
    dramatis_xml_path: Path | None = None


class PublicationDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.title("Publication du site")
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)
        self.geometry("1020x760")
        self.minsize(900, 620)
        self.result: SitePublicationRequest | None = None

        self.vars = _PublicationVars(
            author_name=tk.StringVar(value=""),
            corpus_title=tk.StringVar(value=""),
            scientific_editor=tk.StringVar(value=""),
            corpus_slug=tk.StringVar(value=""),
            home_page_tei=tk.StringVar(value=""),
            general_intro_tei=tk.StringVar(value=""),
            asset_directory=tk.StringVar(value=""),
            output_dir=tk.StringVar(value=""),
            show_xml_download=tk.BooleanVar(value=False),
            publish_notices=tk.BooleanVar(value=True),
            publish_prefaces=tk.BooleanVar(value=True),
            include_metadata=tk.BooleanVar(value=True),
            resolve_notice_xincludes=tk.BooleanVar(value=True),
        )

        self._play_entries: list[_PlayEntry] = []
        self._logo_paths: list[Path] = []
        self._config_path: Path | None = None

        self.vars.author_name.trace_add("write", self._on_corpus_identity_changed)
        self.vars.corpus_title.trace_add("write", self._on_corpus_identity_changed)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        self._scroll_canvas, form = self._build_scrollable_form()
        self._build_metadata_section(form, row=0)
        self._build_intro_section(form, row=1)
        self._build_corpus_section(form, row=2)

        self.action_bar = ttk.Frame(self, padding=(10, 8, 10, 10))
        self.action_bar.grid(row=1, column=0, sticky="ew")
        self.action_bar.columnconfigure(0, weight=1)
        buttons = ttk.Frame(self.action_bar)
        buttons.grid(row=0, column=1, sticky="e")
        ttk.Button(buttons, text="Charger config...", command=self._on_load_config).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(buttons, text="Generer le site", command=self._on_validate).grid(row=0, column=1)
        ttk.Button(buttons, text="Enregistrer config...", command=self._on_save_config).grid(row=0, column=2, padx=(12, 6))
        ttk.Button(buttons, text="Annuler", command=self._on_cancel).grid(row=0, column=3, padx=(0, 6))

        self._refresh_corpus_slug()

    def _build_scrollable_form(self) -> tuple[tk.Canvas, ttk.Frame]:
        container = ttk.Frame(self, padding=(10, 10, 10, 0))
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        canvas = tk.Canvas(container, highlightthickness=0, borderwidth=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(8, 0))
        canvas.configure(yscrollcommand=scrollbar.set)

        form = ttk.Frame(canvas)
        form.columnconfigure(0, weight=1)
        window_id = canvas.create_window((0, 0), window=form, anchor="nw")

        def _sync_scroll_region(_event: tk.Event[tk.Misc]) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _sync_width(event: tk.Event[tk.Misc]) -> None:
            canvas.itemconfigure(window_id, width=event.width)

        def _on_mousewheel(event: tk.Event[tk.Misc]) -> None:
            delta = getattr(event, "delta", 0)
            if delta:
                canvas.yview_scroll(int(-delta / 120), "units")

        form.bind("<Configure>", _sync_scroll_region)
        canvas.bind("<Configure>", _sync_width)
        canvas.bind("<MouseWheel>", _on_mousewheel)
        return canvas, form

    def _build_metadata_section(self, parent: ttk.Frame, *, row: int) -> None:
        box = ttk.LabelFrame(parent, text="Metadonnees generales")
        box.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        box.columnconfigure(1, weight=1)
        self._add_entry(box, 0, "Auteur", self.vars.author_name)
        self._add_entry(box, 1, "Titre de l'oeuvre/corpus", self.vars.corpus_title)
        self._add_entry(box, 2, "Responsable scientifique", self.vars.scientific_editor)

        ttk.Label(box, text="Slug corpus (auteur + 2 premiers mots du titre)").grid(
            row=3,
            column=0,
            sticky="w",
            padx=(0, 6),
            pady=2,
        )
        slug_entry = ttk.Entry(box, textvariable=self.vars.corpus_slug, state="readonly")
        slug_entry.grid(row=3, column=1, sticky="ew", pady=2)

        ttk.Label(box, text="XML-TEI page d'accueil").grid(row=4, column=0, sticky="w", padx=(0, 6), pady=2)
        ttk.Entry(box, textvariable=self.vars.home_page_tei).grid(row=4, column=1, sticky="ew", pady=2)
        ttk.Button(box, text="Choisir...", command=self._choose_home_page_tei).grid(row=4, column=2, padx=(6, 0), pady=2)

        ttk.Label(box, text="Dossier d'assets").grid(row=5, column=0, sticky="w", padx=(0, 6), pady=2)
        ttk.Entry(box, textvariable=self.vars.asset_directory).grid(row=5, column=1, sticky="ew", pady=2)
        ttk.Button(box, text="Choisir...", command=self._choose_asset_directory).grid(row=5, column=2, padx=(6, 0), pady=2)

        logos = ttk.Frame(box)
        logos.grid(row=6, column=0, columnspan=3, sticky="ew")
        logos.columnconfigure(0, weight=1)
        self.logo_list = tk.Listbox(logos, height=2, selectmode=tk.EXTENDED)
        self.logo_list.grid(row=0, column=0, sticky="ew")
        logo_buttons = ttk.Frame(logos)
        logo_buttons.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        ttk.Button(logo_buttons, text="Ajouter logos...", command=self._add_logo_files).grid(row=0, column=0, pady=(0, 4))
        ttk.Button(logo_buttons, text="Supprimer", command=self._remove_logo_selected).grid(row=1, column=0)

        ttk.Label(box, text="Dossier de sortie").grid(row=7, column=0, sticky="w", padx=(0, 6), pady=2)
        ttk.Entry(box, textvariable=self.vars.output_dir).grid(row=7, column=1, sticky="ew", pady=2)
        ttk.Button(box, text="Choisir...", command=self._choose_output_directory).grid(row=7, column=2, padx=(6, 0), pady=2)

        options = ttk.LabelFrame(box, text="Options")
        options.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        ttk.Checkbutton(options, text="Publier les notices", variable=self.vars.publish_notices).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(options, text="Publier les prefaces", variable=self.vars.publish_prefaces).grid(
            row=0, column=1, sticky="w", padx=(12, 0)
        )
        ttk.Checkbutton(options, text="Activer les telechargements XML", variable=self.vars.show_xml_download).grid(
            row=0, column=2, sticky="w", padx=(12, 0)
        )
        ttk.Checkbutton(options, text="Inclure les metadonnees", variable=self.vars.include_metadata).grid(
            row=1, column=0, sticky="w"
        )
        ttk.Checkbutton(options, text="Resoudre les xi:include locaux", variable=self.vars.resolve_notice_xincludes).grid(
            row=1, column=1, sticky="w", padx=(12, 0)
        )

    def _build_intro_section(self, parent: ttk.Frame, *, row: int) -> None:
        box = ttk.LabelFrame(parent, text="Introduction generale")
        box.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        box.columnconfigure(1, weight=1)
        ttk.Label(box, text="XML-TEI introduction generale").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        ttk.Entry(box, textvariable=self.vars.general_intro_tei).grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Button(box, text="Choisir...", command=self._choose_general_intro_tei).grid(row=0, column=2, padx=(6, 0), pady=2)

    def _build_corpus_section(self, parent: ttk.Frame, *, row: int) -> None:
        box = ttk.LabelFrame(parent, text="Corpus de pieces")
        box.grid(row=row, column=0, sticky="nsew")
        box.columnconfigure(0, weight=1)
        box.rowconfigure(1, weight=1)

        controls = ttk.Frame(box)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        ttk.Button(controls, text="Ajouter piece XML...", command=self._add_dramatic_files).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(controls, text="Remplacer piece XML...", command=self._replace_dramatic_for_selected_play).grid(
            row=0, column=1, padx=(0, 6)
        )
        ttk.Button(controls, text="Associer notice XML...", command=self._attach_notice_to_selected_play).grid(
            row=0, column=2, padx=(0, 6)
        )
        ttk.Button(controls, text="Retirer notice", command=self._clear_notice_for_selected_play).grid(row=0, column=3, padx=(0, 6))
        ttk.Button(controls, text="Associer preface XML...", command=self._attach_preface_to_selected_play).grid(
            row=0, column=4, padx=(0, 6)
        )
        ttk.Button(controls, text="Retirer preface", command=self._clear_preface_for_selected_play).grid(
            row=0, column=5, padx=(0, 6)
        )
        ttk.Button(controls, text="Associer Dramatis XML...", command=self._attach_dramatis_to_selected_play).grid(
            row=0, column=6, padx=(0, 6)
        )
        ttk.Button(controls, text="Retirer Dramatis", command=self._clear_dramatis_for_selected_play).grid(
            row=0, column=7, padx=(0, 6)
        )
        ttk.Button(controls, text="Supprimer piece", command=self._remove_dramatic_selected).grid(row=0, column=8)

        ttk.Label(
            box,
            text=(
                "Regle: 1 XML dramatique = 1 piece complete. "
                "Chaque piece du corpus a son XML dramatique propre. "
                "Les fragments doivent etre fusionnes en amont avec l'outil dedie."
            ),
            wraplength=900,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(0, 4))

        lists = ttk.Frame(box)
        lists.grid(row=2, column=0, sticky="nsew")
        lists.columnconfigure(0, weight=2)
        lists.columnconfigure(1, weight=1)
        lists.rowconfigure(0, weight=1)

        self.dramatic_list = tk.Listbox(lists, height=7, selectmode=tk.SINGLE, exportselection=False)
        self.dramatic_list.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        order_box = ttk.LabelFrame(lists, text="Ordre de navigation des pieces")
        order_box.grid(row=0, column=1, sticky="nsew")
        order_box.columnconfigure(0, weight=1)
        order_box.rowconfigure(0, weight=1)
        self.play_order_list = tk.Listbox(order_box, height=7, selectmode=tk.SINGLE, exportselection=False)
        self.play_order_list.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        order_buttons = ttk.Frame(order_box)
        order_buttons.grid(row=1, column=0, sticky="e", padx=4, pady=(0, 4))
        ttk.Button(order_buttons, text="Monter", command=self._move_play_order_up).grid(row=0, column=0, padx=(0, 4))
        ttk.Button(order_buttons, text="Descendre", command=self._move_play_order_down).grid(row=0, column=1)

    @staticmethod
    def _add_entry(parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 6), pady=2)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=2)

    def _on_corpus_identity_changed(self, *_args: str) -> None:
        self._refresh_corpus_slug()

    def _refresh_corpus_slug(self) -> None:
        self.vars.corpus_slug.set(derive_corpus_slug(self.vars.author_name.get(), self.vars.corpus_title.get()))

    @staticmethod
    def _slug_from_file(path: Path) -> str:
        slug = normalize_publication_identifier(path.stem)
        return slug or "piece"

    def _unique_slug_from_path(self, path: Path) -> str:
        base_slug = self._slug_from_file(path)
        existing = {item.play_slug for item in self._play_entries}
        candidate = base_slug
        suffix = 2
        while candidate in existing:
            candidate = f"{base_slug}-{suffix}"
            suffix += 1
        return candidate

    def _refresh_dramatic_list(self) -> None:
        self.dramatic_list.delete(0, tk.END)
        for entry in self._play_entries:
            notice_text = entry.notice_xml_path.name if entry.notice_xml_path is not None else "-"
            preface_text = entry.preface_xml_path.name if entry.preface_xml_path is not None else "-"
            dramatis_text = entry.dramatis_xml_path.name if entry.dramatis_xml_path is not None else "-"
            row = (
                f"{entry.play_slug} | piece: {entry.dramatic_xml_path.name} | notice: {notice_text}"
                f" | preface: {preface_text} | dramatis: {dramatis_text}"
            )
            self.dramatic_list.insert(tk.END, row)

    def _play_order_items(self) -> list[str]:
        return [self.play_order_list.get(i) for i in range(self.play_order_list.size())]

    def _sync_play_order_from_entries(self) -> None:
        current = self._play_order_items()
        active_slugs = [item.play_slug for item in self._play_entries]
        updated = [slug for slug in current if slug in active_slugs]
        for slug in active_slugs:
            if slug not in updated:
                updated.append(slug)
        self.play_order_list.delete(0, tk.END)
        for slug in updated:
            self.play_order_list.insert(tk.END, slug)

    def _append_play_from_path(self, dramatic_xml_path: Path) -> None:
        self._play_entries.append(
            _PlayEntry(
                play_slug=self._unique_slug_from_path(dramatic_xml_path),
                dramatic_xml_path=dramatic_xml_path.resolve(),
            )
        )

    def _selected_play_index(self) -> int | None:
        selection = self.dramatic_list.curselection()
        if not selection:
            return None
        return int(selection[0])

    def _add_dramatic_files(self) -> None:
        chosen = filedialog.askopenfilenames(
            parent=self,
            title="Ajouter des XML dramatiques (pieces completes)",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if not chosen:
            return

        for item in chosen:
            self._append_play_from_path(Path(item).resolve())
        self._refresh_dramatic_list()
        self._sync_play_order_from_entries()

    def _replace_dramatic_for_selected_play(self) -> None:
        selected_index = self._selected_play_index()
        if selected_index is None:
            messagebox.showerror("Publication", "Selectionnez une piece a modifier.", parent=self)
            return

        chosen = filedialog.askopenfilename(
            parent=self,
            title="Remplacer le XML dramatique de la piece selectionnee",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if not chosen:
            return

        selected = self._play_entries[selected_index]
        self._play_entries[selected_index] = _PlayEntry(
            play_slug=selected.play_slug,
            dramatic_xml_path=Path(chosen).resolve(),
            notice_xml_path=selected.notice_xml_path,
            preface_xml_path=selected.preface_xml_path,
            dramatis_xml_path=selected.dramatis_xml_path,
        )
        self._refresh_dramatic_list()
        self.dramatic_list.selection_set(selected_index)

    def _attach_notice_to_selected_play(self) -> None:
        selected_index = self._selected_play_index()
        if selected_index is None:
            messagebox.showerror("Publication", "Selectionnez une piece avant d'associer une notice.", parent=self)
            return
        chosen = filedialog.askopenfilename(
            parent=self,
            title="Associer une notice XML a la piece selectionnee",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if not chosen:
            return
        selected = self._play_entries[selected_index]
        self._play_entries[selected_index] = _PlayEntry(
            play_slug=selected.play_slug,
            dramatic_xml_path=selected.dramatic_xml_path,
            notice_xml_path=Path(chosen).resolve(),
            preface_xml_path=selected.preface_xml_path,
            dramatis_xml_path=selected.dramatis_xml_path,
        )
        self._refresh_dramatic_list()
        self.dramatic_list.selection_set(selected_index)

    def _clear_notice_for_selected_play(self) -> None:
        selected_index = self._selected_play_index()
        if selected_index is None:
            return
        selected = self._play_entries[selected_index]
        self._play_entries[selected_index] = _PlayEntry(
            play_slug=selected.play_slug,
            dramatic_xml_path=selected.dramatic_xml_path,
            notice_xml_path=None,
            preface_xml_path=selected.preface_xml_path,
            dramatis_xml_path=selected.dramatis_xml_path,
        )
        self._refresh_dramatic_list()
        self.dramatic_list.selection_set(selected_index)

    def _attach_preface_to_selected_play(self) -> None:
        selected_index = self._selected_play_index()
        if selected_index is None:
            messagebox.showerror("Publication", "Selectionnez une piece avant d'associer une preface.", parent=self)
            return
        chosen = filedialog.askopenfilename(
            parent=self,
            title="Associer une preface XML a la piece selectionnee",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if not chosen:
            return
        selected = self._play_entries[selected_index]
        self._play_entries[selected_index] = _PlayEntry(
            play_slug=selected.play_slug,
            dramatic_xml_path=selected.dramatic_xml_path,
            notice_xml_path=selected.notice_xml_path,
            preface_xml_path=Path(chosen).resolve(),
            dramatis_xml_path=selected.dramatis_xml_path,
        )
        self._refresh_dramatic_list()
        self.dramatic_list.selection_set(selected_index)

    def _clear_preface_for_selected_play(self) -> None:
        selected_index = self._selected_play_index()
        if selected_index is None:
            return
        selected = self._play_entries[selected_index]
        self._play_entries[selected_index] = _PlayEntry(
            play_slug=selected.play_slug,
            dramatic_xml_path=selected.dramatic_xml_path,
            notice_xml_path=selected.notice_xml_path,
            preface_xml_path=None,
            dramatis_xml_path=selected.dramatis_xml_path,
        )
        self._refresh_dramatic_list()
        self.dramatic_list.selection_set(selected_index)

    def _attach_dramatis_to_selected_play(self) -> None:
        selected_index = self._selected_play_index()
        if selected_index is None:
            messagebox.showerror("Publication", "Selectionnez une piece avant d'associer un Dramatis XML.", parent=self)
            return
        chosen = filedialog.askopenfilename(
            parent=self,
            title="Associer un Dramatis XML externe a la piece selectionnee",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if not chosen:
            return
        selected = self._play_entries[selected_index]
        self._play_entries[selected_index] = _PlayEntry(
            play_slug=selected.play_slug,
            dramatic_xml_path=selected.dramatic_xml_path,
            notice_xml_path=selected.notice_xml_path,
            preface_xml_path=selected.preface_xml_path,
            dramatis_xml_path=Path(chosen).resolve(),
        )
        self._refresh_dramatic_list()
        self.dramatic_list.selection_set(selected_index)

    def _clear_dramatis_for_selected_play(self) -> None:
        selected_index = self._selected_play_index()
        if selected_index is None:
            return
        selected = self._play_entries[selected_index]
        self._play_entries[selected_index] = _PlayEntry(
            play_slug=selected.play_slug,
            dramatic_xml_path=selected.dramatic_xml_path,
            notice_xml_path=selected.notice_xml_path,
            preface_xml_path=selected.preface_xml_path,
            dramatis_xml_path=None,
        )
        self._refresh_dramatic_list()
        self.dramatic_list.selection_set(selected_index)

    def _remove_dramatic_selected(self) -> None:
        selected_index = self._selected_play_index()
        if selected_index is None:
            return
        del self._play_entries[selected_index]
        self._refresh_dramatic_list()
        self._sync_play_order_from_entries()

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

    def _choose_home_page_tei(self) -> None:
        chosen = filedialog.askopenfilename(
            parent=self,
            title="Choisir le XML-TEI de la page d'accueil",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if chosen:
            self.vars.home_page_tei.set(chosen)

    def _choose_general_intro_tei(self) -> None:
        chosen = filedialog.askopenfilename(
            parent=self,
            title="Choisir le XML-TEI de l'introduction generale",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if chosen:
            self.vars.general_intro_tei.set(chosen)

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

    def _collect_dialog_config(self) -> SitePublicationDialogConfig:
        home_page_tei = self.vars.home_page_tei.get().strip()
        general_intro_tei = self.vars.general_intro_tei.get().strip()
        asset_directory = self.vars.asset_directory.get().strip()
        output_raw = self.vars.output_dir.get().strip()

        return SitePublicationDialogConfig(
            author_name=self.vars.author_name.get().strip(),
            corpus_title=self.vars.corpus_title.get().strip(),
            scientific_editor=self.vars.scientific_editor.get().strip(),
            home_page_tei=Path(home_page_tei).resolve() if home_page_tei else None,
            general_intro_tei=Path(general_intro_tei).resolve() if general_intro_tei else None,
            output_dir=Path(output_raw).resolve() if output_raw else None,
            plays=tuple(
                SitePublicationDialogPlayConfig(
                    play_slug=entry.play_slug,
                    dramatic_xml_path=entry.dramatic_xml_path,
                    notice_xml_path=entry.notice_xml_path,
                    preface_xml_path=entry.preface_xml_path,
                    dramatis_xml_path=entry.dramatis_xml_path,
                )
                for entry in self._play_entries
            ),
            play_order=tuple(self._play_order_items()),
            logo_paths=tuple(self._logo_paths),
            asset_directories=(Path(asset_directory).resolve(),) if asset_directory else (),
            show_xml_download=bool(self.vars.show_xml_download.get()),
            publish_notices=bool(self.vars.publish_notices.get()),
            publish_prefaces=bool(self.vars.publish_prefaces.get()),
            include_metadata=bool(self.vars.include_metadata.get()),
            resolve_notice_xincludes=bool(self.vars.resolve_notice_xincludes.get()),
        )

    def _apply_dialog_config(self, config: SitePublicationDialogConfig) -> None:
        self.vars.author_name.set(config.author_name)
        self.vars.corpus_title.set(config.corpus_title)
        self.vars.scientific_editor.set(config.scientific_editor)
        self.vars.home_page_tei.set(str(config.home_page_tei) if config.home_page_tei is not None else "")
        self.vars.general_intro_tei.set(str(config.general_intro_tei) if config.general_intro_tei is not None else "")
        self.vars.output_dir.set(str(config.output_dir) if config.output_dir is not None else "")

        self._play_entries = [
            _PlayEntry(
                play_slug=play.play_slug,
                dramatic_xml_path=play.dramatic_xml_path,
                notice_xml_path=play.notice_xml_path,
                preface_xml_path=play.preface_xml_path,
                dramatis_xml_path=play.dramatis_xml_path,
            )
            for play in config.plays
        ]
        self._refresh_dramatic_list()

        available_slugs = [item.play_slug for item in self._play_entries]
        ordered_slugs = [slug for slug in config.play_order if slug in available_slugs]
        for slug in available_slugs:
            if slug not in ordered_slugs:
                ordered_slugs.append(slug)
        self.play_order_list.delete(0, tk.END)
        for slug in ordered_slugs:
            self.play_order_list.insert(tk.END, slug)

        self._logo_paths = list(config.logo_paths)
        self.logo_list.delete(0, tk.END)
        for path in self._logo_paths:
            self.logo_list.insert(tk.END, str(path))

        asset_directory = config.asset_directories[0] if config.asset_directories else None
        self.vars.asset_directory.set(str(asset_directory) if asset_directory is not None else "")
        self.vars.show_xml_download.set(config.show_xml_download)
        self.vars.publish_notices.set(config.publish_notices)
        self.vars.publish_prefaces.set(config.publish_prefaces)
        self.vars.include_metadata.set(config.include_metadata)
        self.vars.resolve_notice_xincludes.set(config.resolve_notice_xincludes)
        self._refresh_corpus_slug()

    def _on_save_config(self) -> None:
        try:
            config = self._collect_dialog_config()
        except ValueError as exc:
            messagebox.showerror("Publication", str(exc), parent=self)
            return

        chosen = filedialog.asksaveasfilename(
            parent=self,
            title="Enregistrer une configuration de publication",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=(self._config_path.name if self._config_path is not None else "publication_config.json"),
        )
        if not chosen:
            return

        try:
            target = save_site_publication_dialog_config(config, chosen)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Publication", str(exc), parent=self)
            return

        self._config_path = target
        messagebox.showinfo("Publication", f"Configuration de publication enregistree:\n{target}", parent=self)

    def _on_load_config(self) -> None:
        chosen = filedialog.askopenfilename(
            parent=self,
            title="Charger une configuration de publication",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not chosen:
            return

        try:
            config = load_site_publication_dialog_config(chosen)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Publication", str(exc), parent=self)
            return

        self._apply_dialog_config(config)
        self._config_path = Path(chosen).resolve()
        messagebox.showinfo("Publication", f"Configuration de publication chargee:\n{self._config_path}", parent=self)

    def _build_request(self) -> SitePublicationRequest:
        config = self._collect_dialog_config()
        return site_publication_request_from_dialog_config(config)

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
