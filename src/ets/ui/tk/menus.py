from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class MenuCallbacks:
    new_file: Callable[[], None]
    open_file: Callable[[], None]
    save_file: Callable[[], None]
    save_file_as: Callable[[], None]
    restore_autosave: Callable[[], None]
    new_config: Callable[[], None]
    edit_config: Callable[[], None]
    save_config_as: Callable[[], None]
    load_config: Callable[[], None]
    load_annotations: Callable[[], None]
    save_annotations: Callable[[], None]
    quit_app: Callable[[], None]
    undo: Callable[[], None]
    redo: Callable[[], None]
    cut: Callable[[], None]
    copy: Callable[[], None]
    paste: Callable[[], None]
    select_all: Callable[[], None]
    find: Callable[[], None]
    replace: Callable[[], None]
    validate: Callable[[], None]
    validate_generated_tei: Callable[[], None]
    generate_tei: Callable[[], None]
    preview_html: Callable[[], None]
    export_tei: Callable[[], None]
    export_html: Callable[[], None]
    build_publication_site: Callable[[], None]
    add_annotation: Callable[[], None]
    edit_annotation: Callable[[], None]
    delete_annotation: Callable[[], None]
    toggle_diagnostics: Callable[[], None]
    show_about: Callable[[], None]
    show_help: Callable[[], None]


def install_menus(root: tk.Tk, cb: MenuCallbacks) -> None:
    menu = tk.Menu(root)
    root.configure(menu=menu)

    file_menu = tk.Menu(menu, tearoff=False)
    file_menu.add_command(label="Nouveau", command=cb.new_file)
    file_menu.add_command(label="Ouvrir", command=cb.open_file)
    file_menu.add_command(label="Enregistrer", command=cb.save_file)
    file_menu.add_command(label="Enregistrer sous…", command=cb.save_file_as)
    file_menu.add_command(label="Restaurer l'enregistrement automatique", command=cb.restore_autosave)
    file_menu.add_separator()
    file_menu.add_command(label="Nouvelle configuration…", command=cb.new_config)
    file_menu.add_command(label="Modifier la configuration…", command=cb.edit_config)
    file_menu.add_command(label="Enregistrer la configuration sous…", command=cb.save_config_as)
    file_menu.add_command(label="Charger une configuration…", command=cb.load_config)
    file_menu.add_separator()
    file_menu.add_command(label="Charger des annotations…", command=cb.load_annotations)
    file_menu.add_command(label="Enregistrer les annotations…", command=cb.save_annotations)
    file_menu.add_separator()
    file_menu.add_command(label="Quitter", command=cb.quit_app)
    menu.add_cascade(label="Fichier", menu=file_menu)

    edit_menu = tk.Menu(menu, tearoff=False)
    edit_menu.add_command(label="Annuler", command=cb.undo)
    edit_menu.add_command(label="Rétablir", command=cb.redo)
    edit_menu.add_separator()
    edit_menu.add_command(label="Couper", command=cb.cut)
    edit_menu.add_command(label="Copier", command=cb.copy)
    edit_menu.add_command(label="Coller", command=cb.paste)
    edit_menu.add_command(label="Tout sélectionner", command=cb.select_all)
    edit_menu.add_separator()
    edit_menu.add_command(label="Rechercher", command=cb.find)
    edit_menu.add_command(label="Remplacer", command=cb.replace)
    menu.add_cascade(label="Édition", menu=edit_menu)

    tools_menu = tk.Menu(menu, tearoff=False)
    tools_menu.add_command(label="Valider la saisie", command=cb.validate)
    tools_menu.add_command(label="Valider la TEI générée", command=cb.validate_generated_tei)
    tools_menu.add_command(label="Générer le code XML-TEI", command=cb.generate_tei)
    tools_menu.add_command(label="Aperçu HTML", command=cb.preview_html)
    tools_menu.add_separator()
    tools_menu.add_command(label="Ajouter une annotation", command=cb.add_annotation)
    tools_menu.add_command(label="Modifier une annotation", command=cb.edit_annotation)
    tools_menu.add_command(label="Supprimer une annotation", command=cb.delete_annotation)
    tools_menu.add_separator()
    tools_menu.add_command(label="Export TEI", command=cb.export_tei)
    tools_menu.add_command(label="Export HTML", command=cb.export_html)
    tools_menu.add_command(label="Générer le site de publication…", command=cb.build_publication_site)
    menu.add_cascade(label="Outils", menu=tools_menu)

    view_menu = tk.Menu(menu, tearoff=False)
    view_menu.add_command(label="Afficher/masquer diagnostics", command=cb.toggle_diagnostics)
    menu.add_cascade(label="Affichage", menu=view_menu)

    help_menu = tk.Menu(menu, tearoff=False)
    help_menu.add_command(label="Aide syntaxe", command=cb.show_help)
    help_menu.add_command(label="À propos", command=cb.show_about)
    menu.add_cascade(label="Aide", menu=help_menu)
