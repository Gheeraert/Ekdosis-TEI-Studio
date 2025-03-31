# ==============================================================================
# TEILaTeXStudio
#
# Un outil d'encodage inspiré du markdown
# pour encoder des variantes dans le théâtre classique
# avec sorties TEI et LaTeX avec le paquet Ekdosis de Robert Alessi
#
#
# Auteur : Tony Gheeraert
# Affiliation :Chaire d'Excellence en Éditions Numériques, Université de Rouen
#              Centre de recherche Editer-Interpréter (CEREdI, UR 3229)
#              Presses universitaires de Rouen et du Havre
# Date de création : mars 2025
# Licence : MIT
# ==============================================================================

import tkinter as tk
import tkinter.filedialog as fd
from tkinter import messagebox, scrolledtext, ttk
from tkinter import font
from tkinter import simpledialog
import difflib
from collections import defaultdict
import re
import unicodedata
import os
import sys
import math
import lxml.etree as ET
import tempfile
import webbrowser
from tkinter import messagebox
from tkinter import filedialog

def exporter_template_latex():
    template_contenu = r"""
%
% Template LaTeX (ekdosis) pour l'édition du théâtre classique
% Par Federico Siragusa, Roch Delannay et Tony Gheeraert
%
% Basé sur le paquet ekdosis de Robert Alessi
%
% Développé dans le cadre de la chaire d'excellence
% "Editions numériques" (Université de Rouen)
%
% 2025
%
%

\documentclass{book}

% Paquets utiles
\usepackage[main=french, spanish, latin]{babel}
\usepackage[T1]{fontenc}
\usepackage{fontspec}
\usepackage{csquotes}
\usepackage[teiexport, divs=ekdosis, poetry=verse]{ekdosis}
\usepackage{setspace}
\usepackage{lettrine}
\usepackage{hyperref}
\usepackage{zref-user,zref-abspage}

% Informations de mise en page
%
% Police: pour une mise en page "classique"
% charger les polices Junicode et Garamond, 
% et décommenter les lignes ci-dessous
%
%\setmainfont{Junicode}[
%Scale = 1.2,
%Ligatures = {Rare},
%Language = French,
%Style = {Historic},
%Contextuals = {Alternate},
%StylisticSet = 8
%]

\singlespacing

% Police spécifique et style pour l'apparat critique
%
% \newfontfamily\apparatfont{Garamond}
% --------------------------------------------------
%
%
% Page de garde et front(<text><front></front><body></body></text>) 
% Avec mapping automatique

\newenvironment{front}
{\begin{content}} % début de l'environnement
	{\end{content}}   % fin de l'environnement
\EnvtoTEI{front}{front}

\newcommand{\titre}[1]{{\centering\Huge\uppercase{#1}\par}}
\TeXtoTEI{titre}{docTitle}

\newcommand{\autor}[1]{{\centering #1\par}}
\TeXtoTEI{autor}{docAuthor}

\newcommand{\byline}[1]{{\centering #1\par}}
\TeXtoTEI{byline}{byline}

\newcommand{\imprint}[1]{{\centering\Large\uppercase{#1}\par}}
\TeXtoTEI{imprint}{docImprint}

\newcommand{\docdate}[1]{{\centering\Large\uppercase{#1}\par}}
\TeXtoTEI{docdate}{docDate}

%
% Dramatis personae
%

% Liste des personnages (cast). Se contente de créer le balisage TEI
\newenvironment{cast}
{\begin{content}}
	{\end{content}}
\EnvtoTEI{cast}{castList}

% Personnages (castitem, role, roledesc)
%
% A utiliser ainsi:
%
% \roleitem{phedre}{Phèdre}{femme de Thésée}
% \roleitem{hippolyte}{Hippolyte}{fils de Thésée}

\newcommand{\castitem}[1]{#1\par\vspace{0.5ex}}
\TeXtoTEI{castitem}{castItem}

\NewDocumentCommand{\role}{m m}{#2}
\TeXtoTEIPat{\role{#1}{#2}}{<role xml:id="#1">#2</role>}

\newcommand{\roledesc}[1]{#1}
\TeXtoTEI{roledesc}{roleDesc}

\newcommand{\roleitem}[3]{%
	\castitem{%
		\role{#1}{#2}, \roledesc{#3}%
	}%
}

%
% Lieu de l'action
% usage: \set{L'action est à Rome}
%
\newcommand{\set}[1]{#1}
\TeXtoTEI{set}{set}

%
% Didascalies explicites (comprend la liste des personnages en début de scène)
% Usage: \stage{\pn{#antiochus}{Antiochus} entre par la gauche.}
% (pn = abréviation pour persName)
%
% Noms des persos en tête de scène
\newcommand{\stage}[1]{%
	\par\vspace{1em}
	\begin{center}
		\Large\textsc{#1}
	\end{center}
	\vspace{1em}
}
\TeXtoTEI{stage}{stage}
%
%
% Didascalies
\newcommand{\didas}[1]{%
	\par\vspace{0.5em}%
	\begin{center}%
		\textit{#1}%
	\end{center}%
	\vspace{0.5em}%
}
\TeXtoTEI{\didas}{stage}


\newenvironment{head}
{\par\medskip\noindent\textsc}
{\par\medskip}
\EnvtoTEI{head}{head}

% Les noms de personnages
\NewDocumentCommand{\persname}{m m}{%
	#2\unskip % on affiche juste le nom, ekdosis s'occupe du reste
}
\TeXtoTEIPat{\persname{#1}{#2}}{<persName corresp="#1">#2</persName>}

% Raccourci "pn" pour "persName"
\newcommand{\pn}[2]{\persname{#1}{#2}}
\TeXtoTEIPat{\pn{#1}{#2}}{<persName corresp="#1">#2</persName>}

% Les noms de lieux: "placeName"
\NewDocumentCommand{\place}{m m}{#2}
\TeXtoTEIPat{\place{#1}{#2}}{<placeName ref="#1">#2</placeName>}


% Encodage des actes et des scènes
% (méthode native ekdosis)
%
% Usage;
% \ekddiv{head=Acte premier, type=act, n=1, depth=2}
% \ekddiv{head=Acte premier, type=scene, n=2, depth=3}
%
% depth = 2 pour les actes, depth = 3 pour les scènes
%
\FormatDiv{1}{\begin{center}\Huge}{\end{center}}
\FormatDiv{2}{\begin{center}\LARGE}{\end{center}\vspace*{-1em}}
\FormatDiv{3}{\begin{center}\LARGE\textsc}{\end{center}\vspace*{-1em}}

%  Encodage des dialogues
%
%
\newenvironment{speech}{\par}{\par}
\newcommand{\speaker}[1]{\vspace{1em}\large\centering\textsc{#1}\par}
\TeXtoTEI{speaker}{speaker}
\EnvtoTEI{speech}{sp} 
\SetTEIxmlExport{autopar=false}
%%
%
% Numérotation des vers PDF
%
% Affichage automatique en LaTeX-ekdosis
% (La config ci-dessous prévient l'affichage du 
% numéro de paragraphe à gauche)
%
\SetLineation{
%	modulo,
	vmodulo=5
}
\SetLineation{lineation=none}
%
% Export TEI de la numérotation des vers
\newcommand{\vnum}[2]{\linelabel{v#1}#2\par}
\TeXtoTEIPat{\vnum{#1}{#2}}{<l n="#1">#2</l>}
%
%
%
%-------------------------------------------
%
%% éléments supplémentaires
%
% Structuration de la poésie:
% simplement terminer les vers par \\
%
%----------
% Les lettres
%
\newenvironment{letter}
{\par{\begin{content}}}
	{\end{content}}
\EnvtoTEI{letter}{div}[type="letter"]
%------------
% Les chansons
%
\newenvironment{song}[1]
{\par{\begin{content}}}
	{\end{content}}
\EnvtoTEI{song}{div}[type="song"]
%-------------------------------------------
%-------------------------------------------
%
% Déclaration de l'apparat et des versions. Ici pour l'exemple
%
\DeclareApparatus{default}
\DeclareWitness{A}{1670}{Description de A}
\DeclareWitness{B}{1671}{Description de B}
\DeclareWitness{C}{1672}{Description de C}
\DeclareWitness{D}{1673}{Description de D}


%
% Début du corps du document
%

\begin{document}
	\begin{ekdosis}
		
		%
		% Cast/castitem: pour la prochaine version.
		% Ne pas décommenter (bug connu)
		%
		%\begin{cast}
		%	\castitem{\role{xmlid=antiochus}Antiochus, \roledesc{roi de Comagène}}
		%	\castitem{\role{xmlid=arsace}Arsace, \roledesc{Confident d'Antiochus}}
		%\end{cast}
		%\set{La Scene est à Rome}
		%\normalfont
		
		% Pièce
		%%%%%%%%%
		%%%%%%%%%
		% INSERER LE TEXTE GENERE PAR
		% LATEX-TEI Studio ICI
		
		%%%%%%%%%
		%%%%%%%%%
	\end{ekdosis}
\end{document}
"""
    chemin = filedialog.asksaveasfilename(
        defaultextension=".tex",
        filetypes=[("Fichier LaTeX", "*.tex")],
        title="Enregistrer le template LaTeX"
    )
    if chemin:
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(template_contenu)

def exporter_xslt():
    chemin = filedialog.asksaveasfilename(
    defaultextension=".xsl",
    filetypes=[("Feuille de style XSLT", "*.xsl")],
    title="Enregistrer la feuille XSLT"
    )
    if chemin:
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(xslt_str)

def chemin_relatif(nom_fichier):
    """Retourne le chemin correct vers un fichier de ressource, compatible PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, nom_fichier)
    return os.path.abspath(nom_fichier)

def afficher_nagscreen():
    nag = tk.Toplevel(fenetre)
    nag.title("Bienvenue dans TEILaTeXStudio")

    # Thème parchemin
    COULEUR_FOND = "#fdf6e3"
    COULEUR_ENCADRE = "#f5ebc4"
    COULEUR_TEXTE = "#4a3c1a"
    POLICE_SERIF = "Georgia"

    nag.configure(bg=COULEUR_FOND)

    largeur_nag = 540
    hauteur_nag = 500
    fenetre.update_idletasks()
    x_main = fenetre.winfo_rootx()
    y_main = fenetre.winfo_rooty()
    w_main = fenetre.winfo_width()
    h_main = fenetre.winfo_height()
    x = x_main + (w_main - largeur_nag) // 2
    y = y_main + (h_main - hauteur_nag) // 2
    nag.geometry(f"{largeur_nag}x{hauteur_nag}+{x}+{y}")
    nag.grab_set()

    # 💡 Utiliser une vraie instance de police
    police_titre = font.Font(family=POLICE_SERIF, size=32, weight="bold")

    titre = tk.Label(
        nag,
        text="LaTeX–TEI Studio",
        font=("Georgia", 32, "bold"),
        bg=COULEUR_ENCADRE,
        fg=COULEUR_TEXTE,
        pady=20
    )
    titre.pack(padx=20, pady=40)

    # Logo
    try:
        logo_path = chemin_relatif("favicon.png")
        logo = tk.PhotoImage(file=logo_path)
        nag.logo_img = logo  # éviter le garbage collection
        logo_label = tk.Label(nag, image=logo, bg=COULEUR_FOND)
        logo_label.pack(pady=(10, 10))
    except Exception:
        logo_label = tk.Label(nag, text="🧾", font=("Helvetica", 38), bg=COULEUR_FOND)
        logo_label.pack(pady=(10, 10))

    # Mention
    chaire = tk.Label(
        nag,
        text="Assistant pour l'encodage des variantes de textes théâtraux\n\npar T. Gheeraert\n Presses de l'Université de Rouen et du Havre\n Chaire d'excellence en éditions numériques\n CEREdI (UR 3229)",
        font=("Georgia", 12),
        bg=COULEUR_FOND,
        fg=COULEUR_TEXTE,
        justify="center"
    )
    chaire.pack(pady=(0, 10))

    # Bouton
    def commencer():
        nag.destroy()
        initialiser_projet()

    bouton = tk.Button(
        nag, text="Commencer",
        font=("Georgia", 12, "bold"),
        bg=COULEUR_ENCADRE,
        fg=COULEUR_TEXTE,
        activebackground=COULEUR_TEXTE,
        activeforeground="white",
        width=20,
        relief="raised",
        bd=2,
        command=commencer
    )
    bouton.pack(pady=10)

def demander_infos_initiales():
    global titre_piece, numero_acte, numero_scene, nombre_scenes

    titre_piece = simpledialog.askstring("Titre de la pièce", "Entrez le titre de la pièce :")
    numero_acte = simpledialog.askstring("Numéro de l'acte", "Entrez le numéro de l'acte (ex: 1) :")
    numero_scene = simpledialog.askstring("Numéro de la scène", "Entrez le numéro de la scène (ex: 1) :")
    nombre_scenes = simpledialog.askstring("Nombre total de scènes dans l'acte", "Entrez le nombre total de scènes :")

    if not all([titre_piece, numero_acte, numero_scene, nombre_scenes]):
        messagebox.showerror("Erreur", "Toutes les informations sont obligatoires.")
        fenetre.destroy()

def nom_fichier(base, extension):
    try:
        titre_nettoye = nettoyer_identifiant(titre_piece)
        return f"{titre_nettoye}_A{numero_acte}_S{numero_scene}_of{nombre_scenes}_{base}.{extension}"
    except NameError:
        # Variables non encore définies : nom provisoire
        return f"temp_{base}.{extension}"

def normaliser_bloc(bloc):
    return "\n".join([l for l in bloc.strip().splitlines() if l.strip()])

def valider_structure_amelioree():
    texte = zone_saisie.get("1.0", tk.END).strip()
    lignes = texte.splitlines()

    erreurs = []
    a_acte = False
    a_scene = False
    locuteur_en_cours = None

    i = 0
    while i < len(lignes):
        ligne = lignes[i].strip()
        ligne_num = i + 1

        # === Lignes de didascalies ===
        if ligne.startswith("**") and ligne.endswith("**"):
            if i == 0 or lignes[i - 1].strip():
                erreurs.append(f"Ligne {ligne_num} : une ligne vide est requise avant une didascalie.")
            if i == len(lignes) - 1 or lignes[i + 1].strip():
                erreurs.append(f"Ligne {ligne_num} : une ligne vide est requise après une didascalie.")

        # === Dièses mal appariés ===
        if ligne.count("#") % 2 != 0:
            erreurs.append(f"Ligne {ligne_num} : nombre impair de dièses.")

        # === Acte ===
        if re.fullmatch(r"####\d+####", ligne):
            a_acte = True
            a_scene = False
            i += 1
            continue

        # === Scène ===
        if re.fullmatch(r"###\d+###", ligne):
            if not a_acte:
                erreurs.append(f"Ligne {ligne_num} : scène définie avant tout acte.")
            a_scene = True
            i += 1
            continue

        # === Bloc de personnages ===
        if re.fullmatch(r"(##[^\#]+##\s*)+", ligne):
            if not a_scene:
                erreurs.append(f"Ligne {ligne_num} : personnages présents hors d'une scène.")

            # Vérifier qu’un locuteur suive avant nouvelle scène/acte
            j = i + 1
            locuteur_trouvé = False
            while j < len(lignes):
                ligne_suiv = lignes[j].strip()
                if re.fullmatch(r"####\d+####", ligne_suiv) or re.fullmatch(r"###\d+###", ligne_suiv):
                    break
                if re.fullmatch(r"#[^#]+#", ligne_suiv):
                    locuteur_trouvé = True
                    break
                j += 1
            if not locuteur_trouvé:
                erreurs.append(f"Ligne {ligne_num} : aucun locuteur (#Nom#) trouvé après les personnages.")
            i += 1
            continue

        # === Locuteur ===
        if re.fullmatch(r"#[^#]+#", ligne):
            if not a_scene:
                erreurs.append(f"Ligne {ligne_num} : locuteur défini hors d'une scène.")
            if locuteur_en_cours:
                erreurs.append(f"Ligne {ligne_num} : locuteur '{locuteur_en_cours}' sans contenu.")
            locuteur_en_cours = ligne[1:-1].strip()
            i += 1
            continue

        # === Vers normaux ou partagés ===
        if ligne or ligne.startswith("***") or ligne.endswith("***"):
            if locuteur_en_cours:
                locuteur_en_cours = None
            i += 1
            continue

        # === Ligne vide ===
        i += 1

    # Rappels finaux
    if not any(re.fullmatch(r"####\d+####", l.strip()) for l in lignes):
        erreurs.append("Aucun acte (####n####) n’est défini.")
    if not any(re.fullmatch(r"###\d+###", l.strip()) for l in lignes):
        erreurs.append("Aucune scène (###n###) n’est définie.")
    if not any(re.fullmatch(r"#[^#]+#", l.strip()) for l in lignes):
        erreurs.append("Aucun locuteur (#Nom#) n’est défini.")

    if erreurs:
        messagebox.showerror("Erreurs détectées", "\n".join(erreurs))
    else:
        messagebox.showinfo("Validation réussie", "Structure valide.")

valider_structure = valider_structure_amelioree  # on remplace la fonction existante

# Ajouter ce bouton à l’interface existante
def ajouter_bouton_validation(frame):
    btn_valider = tk.Button(frame, text="Valider la structure", command=valider_structure)
    btn_valider.pack(side=tk.LEFT, padx=10)

ajouter_bouton_validation = ajouter_bouton_validation  # pour usage externe si besoin

# Fonction de normalisation plus robuste pour les identifiants TEI
def nettoyer_identifiant(nom):
    # Convertir en minuscules
    nom = nom.lower()
    # Supprimer les accents
    nom = ''.join(
        c for c in unicodedata.normalize('NFD', nom)
        if unicodedata.category(c) != 'Mn'
    )
    # Supprimer tout sauf les caractères alphanumériques
    nom = re.sub(r"[^\w]", "", nom)
    return nom

def echapper_caracteres_latex(texte):
    """Échappe les caractères spéciaux LaTeX comme l’esperluette."""
    return texte.replace("&", r"\&")

def encoder_caracteres_tei(texte):
    """Encode les caractères spéciaux XML/TEI comme l’esperluette."""
    return texte.replace("&", "&amp;")

def rechercher():
    terme = simpledialog.askstring("Rechercher", "Mot ou expression à chercher :")
    if terme:
        zone_saisie.tag_remove("found", "1.0", tk.END)
        start_pos = "1.0"
        while True:
            start_pos = zone_saisie.search(terme, start_pos, stopindex=tk.END)
            if not start_pos:
                break
            end_pos = f"{start_pos}+{len(terme)}c"
            zone_saisie.tag_add("found", start_pos, end_pos)
            start_pos = end_pos
        zone_saisie.tag_config("found", background="yellow")

def remplacer_avance():
    terme = simpledialog.askstring("Remplacer", "Mot à rechercher :")
    if not terme:
        return

    remplacement = simpledialog.askstring("Remplacer", f"Remplacer « {terme} » par :")
    if remplacement is None:
        return

    sensible_casse = messagebox.askyesno("Casse", "Faire la recherche en respectant la casse (majuscules/minuscules) ?")

    contenu = zone_saisie.get("1.0", tk.END)
    count = 0
    index = "1.0"

    while True:
        index = zone_saisie.search(terme, index, nocase=not sensible_casse, stopindex=tk.END)
        if not index:
            break

        fin_index = f"{index}+{len(terme)}c"
        zone_saisie.tag_add("remplacer", index, fin_index)
        zone_saisie.tag_config("remplacer", background="yellow")

        zone_saisie.see(index)
        zone_saisie.focus()

        confirmer = messagebox.askyesno("Remplacer ?", f"Remplacer cette occurrence de « {terme} » par « {remplacement} » ?")
        zone_saisie.tag_delete("remplacer")

        if confirmer:
            zone_saisie.delete(index, fin_index)
            zone_saisie.insert(index, remplacement)
            count += 1
            index = f"{index}+{len(remplacement)}c"
        else:
            index = fin_index

    messagebox.showinfo("Remplacements terminés", f"{count} remplacement(s) effectué(s).")


def appliquer_style_light(fenetre):
    fond = "#f4f4f4"

    fenetre.configure(bg=fond)

    police_label = font.Font(family="Helvetica", size=11, weight="bold")
    police_zone = font.Font(family="Courier", size=11)
    police_bouton = font.Font(family="Helvetica", size=12, weight="bold")

    zone_saisie.configure(font=police_zone)
    zone_resultat_tei.configure(font=police_zone)
    zone_resultat_latex.configure(font=police_zone)

    for widget in fenetre.winfo_children():
        if isinstance(widget, tk.Label):
            widget.configure(font=police_label, bg=fond)
        elif isinstance(widget, tk.Frame):
            widget.configure(bg=fond)

    for widget in frame_bas.winfo_children():
        if isinstance(widget, tk.Button):
            widget.configure(font=police_bouton)

def appliquer_style_parchemin(fenetre):
    # Couleurs
    COULEUR_FOND = "#fdf6e3"
    COULEUR_ENCADRE = "#f5ebc4"
    COULEUR_TEXTE = "#4a3c1a"
    POLICE_SERIF = "Georgia"

    # Appliquer à la fenêtre principale
    fenetre.configure(bg=COULEUR_FOND)

    # Polices
    police_label = font.Font(family=POLICE_SERIF, size=11, weight="bold")
    police_zone = font.Font(family="Courier New", size=11)
    police_bouton = font.Font(family=POLICE_SERIF, size=12, weight="bold")

    # Style ttk pour les Combobox
    style = ttk.Style()
    style.theme_use('default')
    style.configure(
        "Parchemin.TCombobox",
        fieldbackground=COULEUR_FOND,
        background=COULEUR_ENCADRE,
        foreground=COULEUR_TEXTE,
        font=(POLICE_SERIF, 11)
    )

    def styliser_recursivement(widget):
        if isinstance(widget, tk.Toplevel) and widget.title() == "Bienvenue dans TEILaTeXStudio":
            return

        for child in widget.winfo_children():
            # Label et LabelFrame
            if isinstance(child, (tk.Label, tk.LabelFrame)):
                child.configure(font=police_label, bg=COULEUR_ENCADRE, fg=COULEUR_TEXTE)
            # Frame
            elif isinstance(child, tk.Frame):
                child.configure(bg=COULEUR_FOND)
            # Entry
            elif isinstance(child, tk.Entry):
                try:
                    child.configure(bg="white", fg=COULEUR_TEXTE, font=police_zone, insertbackground=COULEUR_TEXTE)
                except tk.TclError:
                    pass  # certains widgets ttk.Entry n'acceptent pas ces options
            # Button
            elif isinstance(child, tk.Button):
                child.configure(
                    font=police_bouton,
                    bg=COULEUR_ENCADRE,
                    fg=COULEUR_TEXTE,
                    activebackground=COULEUR_TEXTE,
                    activeforeground="white",
                    relief="raised",
                    bd=2
                )
            # Combobox
            elif isinstance(child, ttk.Combobox):
                child.configure(style="Parchemin.TCombobox")

            # Récursion
            styliser_recursivement(child)

    styliser_recursivement(fenetre)

    # Zones de texte
    try:
        zone_saisie.configure(bg="white", font=police_zone)
        zone_resultat_tei.configure(bg="white", font=police_zone)
        zone_resultat_latex.configure(bg="white", font=police_zone)
    except:
        pass


def confirmer_quitter():
    if messagebox.askokcancel("Quitter", "Voulez-vous vraiment quitter ?\nLes modifications non sauvegardées seront perdues."):
        fenetre.destroy()

def exporter_tei():
    contenu = zone_resultat_tei.get("1.0", tk.END).strip()
    if not contenu:
        messagebox.showwarning("Avertissement", "Aucun contenu TEI à enregistrer.")
        return
    fichier = fd.asksaveasfilename(
        defaultextension=".xml",
        filetypes=[("Fichiers TEI XML", "*.xml")],
        initialfile=nom_fichier("tei", "xml"),
        title="Enregistrer le fichier TEI"
    )
    if fichier:
        with open(fichier, "w", encoding="utf-8") as f:
            f.write(contenu)
        messagebox.showinfo("Succès", f"Fichier TEI enregistré :\n{fichier}")

def exporter_latex():
    contenu = zone_resultat_latex.get("1.0", tk.END).strip()
    if not contenu:
        messagebox.showwarning("Avertissement", "Aucun contenu LaTeX à enregistrer.")
        return
    fichier = fd.asksaveasfilename(
        defaultextension=".tex",
        filetypes=[("Fichiers LaTeX", "*.tex")],
        initialfile=nom_fichier("latex", "tex"),
        title="Enregistrer le fichier LaTeX"
    )
    if fichier:
        with open(fichier, "w", encoding="utf-8") as f:
            f.write(contenu)
        messagebox.showinfo("Succès", f"Fichier LaTeX enregistré :\n{fichier}")

def enregistrer_saisie():
    valider_structure()
    contenu = zone_saisie.get("1.0", tk.END).strip()
    if not contenu:
        messagebox.showwarning("Avertissement", "Aucune saisie à enregistrer.")
        return
    fichier = fd.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Fichiers texte", "*.txt")],
        initialfile=nom_fichier("saisie", "txt"),
        title="Enregistrer la saisie"
    )
    if fichier:
        with open(fichier, "w", encoding="utf-8") as f:
            f.write(contenu)
        messagebox.showinfo("Succès", f"Saisie enregistrée :\n{fichier}")

def formatter_persname_tei(noms):
    return ", ".join(
        f'<persName ref="#{nettoyer_identifiant(n)}">{n}</persName>'
        for n in noms
    )
def formatter_persname_latex(noms):
    return ", ".join(
        f'\\pn{{#{nettoyer_identifiant(n)}}}{{{n}}}'
        for n in noms
    )

def extraire_numero_et_titre(s):
    numero = int(s)
    titres = ["", "premier", "deuxième", "troisième", "quatrième", "cinquième",
              "sixième", "septième", "huitième", "neuvième", "dixième"]
    titre = titres[numero] if numero < len(titres) else f"{numero}e"
    return numero, titre

def activer_undo_redo(widget):
    widget.config(undo=True, maxundo=-1)
    widget.bind("<Control-z>", lambda e: widget.edit_undo())
    widget.bind("<Control-y>", lambda e: widget.edit_redo())

def mettre_a_jour_menu(*args):
    texte = zone_saisie.get("1.0", tk.END).strip()
    lignes = [l.strip() for l in texte.splitlines() if l.strip() and not l.startswith("[")]
    menu_ref["values"] = [chr(65 + i) for i in range(len(lignes))]
    if lignes:
        liste_ref.current(0)


def previsualiser_html():
    tei = zone_resultat_tei.get("1.0", tk.END).strip()
    if not tei:
        messagebox.showwarning("Avertissement", "Aucun contenu TEI à prévisualiser.")
        return

    try:
        tei_xml = ET.fromstring(tei.encode("utf-8"))

        # Feuille XSLT intégrée
        xslt_str = '''<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:tei="http://www.tei-c.org/ns/1.0"
    exclude-result-prefixes="tei">
  <xsl:output method="html" encoding="UTF-8" indent="yes"/>
    <xsl:template match="/tei:TEI">
    <html lang="fr">
      <head>
        <meta charset="UTF-8"/>
        <title>Ãdition TEI</title>
        <xsl:text disable-output-escaping="yes">
          <![CDATA[<link href="https://fonts.googleapis.com/css2?family=IM+Fell+DW+Pica&display=swap" rel="stylesheet">]]>
        </xsl:text>
        <style>
          body {
            font-family: 'IM Fell DW Pica', Georgia, serif;
            background: #fdf6e3;
            color: #4a3c1a;
            padding: 2em;
            max-width: 800px;
            margin-left: 9em;
          }
          .acte, .scene, .personnages {
            font-weight: bold;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            margin-left: 11em;
          }
          .scene-titre {
            font-style: italic;
            margin-bottom: 0.5em;
            margin-left: 11em;
          }
          .locuteur {
            font-variant: small-caps;
            margin-top: 1em;
            margin-bottom: 0.2em;
            margin-left: 11em;
          }
          .tirade {
            margin-left: 1em;
            margin-bottom: 1em;
          }
          .vers {
            margin: 0.2em 0;
          }
          .didascalie {
            font-style: italic;
            color: #555;
            margin-left: 9em;
            margin-bottom: 0.5em;
          }
          .variation {
            border-bottom: 1px dotted #8b5e3c;
            cursor: help;
            }
            p.vers {
            display: flex;
            gap: 1em;
            margin: 0.2em 0;
          }
          .vers-container {
            position: relative;
            margin-left: 5em;
            margin-bottom: 0.4em;
            line-height: 1;
          }
          .num-vers {
            position: absolute;
            left: -4.5em;
            width: 4em;
            text-align: right;
            font-size: 0.85em;
            color: #5a5245;
            font-style: italic;
          }
          .texte-vers {
            display: inline;
          }
          .vers-decale {
            margin-left: 14em; /* ou plus selon le dÃ©calage dÃ©sirÃ© */
          }
        </style>
      </head>
      <body>
        <xsl:apply-templates/>
      </body>
    </html>
  </xsl:template>

  <!-- Acte -->
  <xsl:template match="tei:div[@type='act']">
    <div class="acte">ACTE <xsl:value-of select="@n"/></div>
    <xsl:apply-templates/>
  </xsl:template>

  <!-- Titre de scÃ¨ne -->
  <xsl:template match="tei:head">
    <div class="scene-titre"><xsl:apply-templates/></div>
  </xsl:template>

  <!-- Didascalies -->
  <xsl:template match="tei:stage">
    <div class="didascalie"><xsl:apply-templates/></div>
  </xsl:template>

  <!-- Bloc de parole -->
  <xsl:template match="tei:sp">
    <div class="locuteur"><xsl:value-of select="tei:speaker"/></div>
    <div class="tirade">
      <xsl:apply-templates select="tei:l"/>
    </div>
  </xsl:template>

  <!-- Vers -->
<xsl:template match="tei:l">
  <div>
    <xsl:attribute name="class">
      <xsl:text>vers-container</xsl:text>
      <xsl:if test="contains(@n, '.2')">
        <xsl:text> vers-decale</xsl:text>
      </xsl:if>
    </xsl:attribute>

    <xsl:choose>
      <xsl:when test="number(@n) mod 5 = 0">
        <span class="num-vers"><xsl:value-of select="@n"/></span>
      </xsl:when>
      <xsl:otherwise>
        <span class="num-vers"></span>
      </xsl:otherwise>
    </xsl:choose>

    <span class="texte-vers">
      <xsl:apply-templates/>
    </span>
  </div>
</xsl:template>



  <!-- Variantes : infobulle au survol -->
  <xsl:template match="tei:app">
    <xsl:variable name="tooltip">
      <xsl:for-each select="tei:rdg">
        <xsl:value-of select="@wit"/>
        <xsl:text>: </xsl:text>
        <xsl:value-of select="normalize-space(.)"/>
        <xsl:if test="position() != last()">
          <xsl:text>&#10;</xsl:text>
        </xsl:if>
      </xsl:for-each>
    </xsl:variable>

    <span class="variation">
      <xsl:attribute name="title">
        <xsl:value-of select="$tooltip"/>
      </xsl:attribute>
      <xsl:apply-templates select="tei:lem"/>
    </span>
  </xsl:template>

  <!-- On ignore les rdg dans le texte courant -->
  <xsl:template match="tei:rdg"/>
</xsl:stylesheet>
'''
        xslt_root = ET.XML(xslt_str.encode('utf-8'))
        transform = ET.XSLT(xslt_root)
        html_result = transform(tei_xml)

        chemin_script = os.path.dirname(os.path.abspath(__file__))
        chemin_temp_html = os.path.join(chemin_script, "preview_temp.html")
        with open(chemin_temp_html, "w", encoding="utf-8") as f:
            f.write(str(html_result))

        webbrowser.open(f"file://{chemin_temp_html}")

    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur pendant la transformation XSLT :\n{e}")

def convertir_tei_en_html_beau_ameliore(tei_text):
    html = []
    dans_tirade = False
    current_speaker = ""
    vers_buffer = []

    lignes = tei_text.splitlines()
    i = 0
    while i < len(lignes):
        ligne = lignes[i].strip()

        # Acte
        match_acte = re.match(r'<div type="act" n="(\d+)">', ligne)
        if match_acte:
            html.append(f'<h2 class="acte">ACTE {match_acte.group(1)}</h2>')
            i += 1
            continue

        # Scène
        match_scene = re.match(r'<div type="scene" n="(\d+)">', ligne)
        if match_scene:
            html.append(f'<h3 class="scene">Scène {match_scene.group(1)}</h3>')
            i += 1
            continue

        # Titre de scène
        if ligne.startswith("<head>"):
            titre = re.sub(r'</?head>', '', ligne).strip()
            html.append(f"<h4 class=\"scene-titre\">{titre}</h4>")
            i += 1
            continue

        # Didascalie
        if "<stage>" in ligne:
            texte = re.sub(r'</?stage>', '', ligne).strip()
            html.append(f"<p class=\"didascalie\"><em>{texte}</em></p>")
            i += 1
            continue

        # Début tirade
        if "<sp>" in ligne:
            dans_tirade = True
            vers_buffer = []
            i += 1
            continue

        # Locuteur
        elif "<speaker>" in ligne:
            current_speaker = re.sub(r'</?speaker>', '', ligne).strip()
            i += 1
            continue

        # Vers
        elif ligne.startswith("<l "):
            vers_lignes = []

            # Numéro du vers
            match_vers = re.match(r'<l n="([^"]+)">', ligne)
            vers_num = match_vers.group(1) if match_vers else ""

            # Regroupe jusqu'à la fin du </l>
            while not lignes[i].strip().endswith("</l>"):
                vers_lignes.append(lignes[i].strip())
                i += 1
            vers_lignes.append(lignes[i].strip())  # Ajouter la ligne contenant </l>
            i += 1

            bloc = "\n".join(vers_lignes)

            # Extraction du <lem> uniquement
            def extraire_lem(texte):
                texte = re.sub(r'<app>.*?<lem[^>]*>(.*?)</lem>.*?</app>', r'\1', texte, flags=re.DOTALL)
                texte = re.sub(r'<[^>]+>', '', texte)
                return texte.strip()

            vers_propre = extraire_lem(bloc)
            vers_buffer.append(f'<p class="vers"><span class="vers-num">{vers_num}</span> {vers_propre}</p>')
            continue

        # Fin tirade
        elif "</sp>" in ligne:
            if current_speaker:
                html.append('<div class="tirade">')
                html.append(f'  <p class="locuteur">{current_speaker} :</p>')
                html.extend(vers_buffer)
                html.append('</div>')
            current_speaker = ""
            dans_tirade = False
            vers_buffer = []
            i += 1
            continue

        else:
            i += 1

    return "\n".join(html)


def previsualiser_html_xslt():
    tei = zone_resultat_tei.get("1.0", tk.END).strip()
    if not tei:
        messagebox.showwarning("Avertissement", "Aucun contenu TEI à prévisualiser.")
        return

    try:
        # Parser le contenu TEI
        tei_xml = ET.fromstring(tei.encode("utf-8"))

        # Charger la feuille XSLT
        with open("tei-vers-html.xsl", "rb") as f:
            xslt_root = ET.XML(f.read())
        transform = ET.XSLT(xslt_root)

        # Appliquer la transformation
        html_result = transform(tei_xml)
        # Écrire un fichier HTML local dans le dossier du script
        chemin_script = os.path.dirname(os.path.abspath(__file__))
        chemin_temp_html = os.path.join(chemin_script, "preview_temp.html")

        with open(chemin_temp_html, "w", encoding="utf-8") as f:
            f.write(str(html_result))

        # Ouvrir dans le navigateur
        webbrowser.open(f"file://{chemin_temp_html}")


    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur pendant la transformation XSLT :\n{e}")

def transformer_tei_avec_xsl():
    tei_text = zone_resultat_tei.get("1.0", tk.END).strip()
    if not tei_text:
        messagebox.showwarning("Avertissement", "Aucun contenu TEI à transformer.")
        return

    try:
        # Charger TEI et XSL
        tei_doc = ET.fromstring(tei_text.encode('utf-8'))
        xsl_path = "tei-vers-html.xsl"  # Ce fichier doit être dans le même dossier que ton script
        xsl_doc = ET.parse(xsl_path)
        transform = ET.XSLT(xsl_doc)

        # Transformation
        resultat_html = transform(tei_doc)

        # Écriture dans un fichier temporaire
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html", encoding="utf-8") as f:
            f.write(str(resultat_html))
            temp_html_path = f.name

        # Ouvrir dans navigateur
        webbrowser.open(f"file://{temp_html_path}")

    except Exception as e:
        messagebox.showerror("Erreur XSLT", f"Erreur lors de la transformation : {e}")

def afficher_aide():
    exemple = r"""
Mémo

####1####             → Acte I
###1###            → Scène 1
##Titus## ##Bérénice## → Personnages présents
#Titus#            → Locuteur (début de tirade)
Témoin A Vers 1
Témoin B Vers 1

Témoin A vers 2
Témoin B vers 2

Vers partagés:
#Titus#
Rome, l'Empire***

#Bérénice#
***Eh bien?

Les états (témoins A, B, C…) doivent être saisis ligne à ligne à chaque vers.
Laissez une ligne vide pour séparer les variantes d’un nouveau vers.
Laissez une ligne vide avant et après les **didascalies**

"""
    messagebox.showinfo("Aide à la transcription", exemple)

def comparer_etats():
    texte = zone_saisie.get("1.0", tk.END).strip()
    lignes = texte.splitlines()
    sous_blocs_ignorés = set()

    dialogues = []
    current_acte = None
    current_scene = None
    current_personnages = []
    current_speaker = None
    current_bloc = []

    for ligne in lignes:
        ligne = ligne.strip()

        if re.match(r"\#\#\#\#\d+\#\#\#\#", ligne):  # Acte
            if current_bloc and current_speaker:
                dialogues.append((current_acte, current_scene, current_personnages, current_speaker, "\n".join(current_bloc)))
                current_bloc = []
            current_acte = re.findall(r"\d+", ligne)[0]
            current_scene = None
            current_personnages = []

        elif re.match(r"\#\#\#\d+\#\#\#", ligne):  # Scène
            if current_bloc and current_speaker:
                dialogues.append((current_acte, current_scene, current_personnages, current_speaker, "\n".join(current_bloc)))
                current_bloc = []
            current_scene = re.findall(r"\d+", ligne)[0]
            current_personnages = []

        elif re.match(r"(\#\#[^#]+\#\#)+", ligne):  # Personnages
            personnages = re.findall(r"\#\#([^\#\#]+)\#\#", ligne)
            current_personnages.extend(personnages)

        elif ligne.startswith("#") and ligne.endswith("#"):  # Locuteur
            if current_bloc and current_speaker:
                dialogues.append((current_acte, current_scene, current_personnages, current_speaker, "\n".join(current_bloc)))
            current_speaker = ligne[1:-1].strip()
            current_bloc = []

        elif ligne:
            current_bloc.append(ligne)

        elif not ligne and current_bloc:
            current_bloc.append("")

    if current_bloc and current_speaker:
        dialogues.append((current_acte, current_scene, current_personnages, current_speaker, "\n".join(current_bloc)))

    try:
        numero_depart = int(entree_vers.get())
    except ValueError:
        messagebox.showwarning("Erreur", "Le numéro de vers de départ doit être un entier.")
        return

    resultat_tei = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">',
        '  <teiHeader>',
        '    <fileDesc>',
        f'      <titleStmt><title></title></titleStmt>',
        '      <publicationStmt><p></p></publicationStmt>',
        '      <sourceDesc><p>Généré par TEILaTeXStudio</p></sourceDesc>',
        '    </fileDesc>',
        '  </teiHeader>',
        '  <text>',
        '    <body>'
    ]

    resultat_latex = []

    vers_courant = numero_depart
    current_acte_out = None
    current_scene_out = None
    dernier_locuteur = None

    for acte, scene, personnages, speaker, bloc in dialogues:
        if acte != current_acte_out:
            if current_acte_out is not None:
                resultat_tei.append("  </div>")
                resultat_tei.append("</div>")
                resultat_latex.append("% Fin de la scène")
                resultat_latex.append("% Fin de l'acte")

            current_acte_out = acte
            num, titre = extraire_numero_et_titre(acte)

            # TEI
            resultat_tei.append(f'<div type="act" n="{num}">')

            # LaTeX ekdosis-compatible
            resultat_latex.append(f'\\ekddiv{{head=ACTE {titre.upper()}, type=act, n={num}, depth=2}}\n')

            current_scene_out = None

        if scene != current_scene_out:
            if current_scene_out is not None:
                resultat_tei.append("  </sp>")
                resultat_tei.append("  </div>")
                resultat_latex.append("      \\end{ekdverse}\n    \\end{speech}   % Fin de la scène")

            current_scene_out = scene
            dernier_locuteur = None  # ← 🎯 AJOUT ICI

            # TEI
            resultat_tei.append(f'  <div type="scene" n="{scene}">\n    <head>Scène {scene}</head>')

            # LaTeX ekdosis-compatible
            resultat_latex.append(f'\\ekddiv{{head=Scène {scene}, type=scene, n={scene}, depth=3}}\n')

            if personnages:
                pers_tei = formatter_persname_tei(personnages)
                pers_latex = formatter_persname_latex(personnages)
                resultat_tei.append(f'    <stage>{pers_tei}.</stage>')
                resultat_latex.append(f'    \\stage{{{pers_latex}}}')

        sous_blocs = bloc.split("\n\n")
        if speaker != dernier_locuteur:
            if dernier_locuteur is not None:
                resultat_tei.append("    </sp>")
                resultat_latex.append("      \\end{ekdverse}\n    \\end{speech}")
            resultat_tei.append(f'    <sp>\n      <speaker>{speaker}</speaker>')
            resultat_latex.append("    \\begin{speech}\n      \\speaker{" + speaker + "}\n      \\begin{ekdverse}")
            dernier_locuteur = speaker

        for sous_bloc in sous_blocs:
            sous_bloc_texte = normaliser_bloc(sous_bloc)
            if sous_bloc_texte in sous_blocs_ignorés:
                speaker = speaker_suivant
                continue

            lignes = [l.strip() for l in sous_bloc.strip().splitlines() if l.strip()]

            # Didascalie seule
            if len(lignes) == 1 and lignes[0].startswith("**") and lignes[0].endswith("**"):
                didascalie = lignes[0][2:-2].strip()
                resultat_tei.append(f'      <stage>{didascalie}</stage>')
                resultat_latex.append(f'        \\didas{{{didascalie}}}')
                continue

            # Cas du vers partagé : *** à la fin (bloc A) et *** au début (bloc B)
            if all(l.endswith('***') for l in lignes) and len(lignes) >= 2:
                numero_vers_base = vers_courant  # e.g., 12
                vers_num_1 = f"{numero_vers_base}.1"
                vers_num_2 = f"{numero_vers_base}.2"

                # Nettoyage du bloc 1 (première moitié)
                partie_1 = [l.rstrip('*').strip() for l in lignes]
                tokens_1 = [l.split() for l in partie_1]
                base_1 = tokens_1[liste_ref.current()]
                temoins = [chr(65 + i) for i in range(len(partie_1))]

                # Différences pour partie 1
                differences = defaultdict(lambda: defaultdict(list))
                for i, ligne in enumerate(tokens_1):
                    if i == liste_ref.current():
                        continue
                    sm = difflib.SequenceMatcher(None, base_1, ligne)
                    for tag, i1, i2, j1, j2 in sm.get_opcodes():
                        if tag != "equal":
                            position = (i1, i2)
                            variante = " ".join(ligne[j1:j2])
                            differences[position][variante].append(temoins[i])

                ligne_tei = []
                ligne_latex = []
                segment_buffer = []
                i = 0
                while i < len(base_1):
                    matching_apps = [key for key in differences.keys() if key[0] == i]
                    if matching_apps:
                        if segment_buffer:
                            segment_texte = " ".join(segment_buffer)
                            ligne_tei.append("      " + encoder_caracteres_tei(segment_texte) + "\n")
                            ligne_latex.append("      " + echapper_caracteres_latex(segment_texte))
                            segment_buffer = []

                        start, end = max(matching_apps, key=lambda x: x[1])
                        lem = " ".join(base_1[start:end])
                        rdgs = differences[(start, end)]
                        wit_lem = [temoins[j] for j, ligne in enumerate(tokens_1) if " ".join(ligne[start:end]) == lem]

                        tei_app = [
                            f'      <app>\n',
                            f'        <lem wit="{" ".join(f"#{t}" for t in wit_lem)}">{encoder_caracteres_tei(lem)}</lem>\n'
                        ]
                        for texte_rdg, liste_temoins in rdgs.items():
                            if texte_rdg != lem:
                                wits = " ".join(f"#{t}" for t in liste_temoins)
                                tei_app.append(f'        <rdg wit="{wits}">{encoder_caracteres_tei(texte_rdg)}</rdg>\n')
                        tei_app.append(f'      </app>\n')
                        ligne_tei.extend(tei_app)

                        rdg_blocks = [
                            f'        \\rdg[wit={{{", ".join(liste_temoins)}}}]{{{echapper_caracteres_latex(texte_rdg)}}}'
                            for texte_rdg, liste_temoins in rdgs.items() if texte_rdg != lem
                        ]
                        latex_block = [f'      \\app{{',
                                       f'        \\lem[wit={{{", ".join(wit_lem)}}}]{{{echapper_caracteres_latex(lem)}}}']
                        latex_block.extend(rdg_blocks)
                        latex_block.append('      }')
                        ligne_latex.append("\n".join(latex_block))

                        i = end
                    else:
                        segment_buffer.append(base_1[i])
                        i += 1

                if segment_buffer:
                    segment_texte = " ".join(segment_buffer)
                    ligne_tei.append("      " + encoder_caracteres_tei(segment_texte) + "\n")
                    ligne_latex.append("      " + echapper_caracteres_latex(segment_texte))

                resultat_tei.append(f'<l n="{vers_num_1}">\n' + "".join(ligne_tei) + '</l>')
                vers_formate_1 = "\n".join(ligne_latex)
                # à supprimer
                #resultat_latex.append("      \\end{ekdverse}\n    \\end{speech}")
                #resultat_latex.append(f'    \\begin{{speech}}\n      \\speaker{{{speaker}}}\n      \\begin{{ekdverse}}')
                resultat_latex.append(f'        \\vnum{{{vers_num_1}}}' + '{\n' + vers_formate_1 + '\\\\    \n         }')

                # Seconde moitié — locuteur suivant
                lignes_suivantes = []
                trouver_debut = False
                trouver_texte = False
                bloc_b_complet = None

                for acte2, scene2, persos2, speaker_suivant, bloc2 in dialogues:
                    if trouver_debut:
                        lignes_brutes = bloc2.strip().splitlines()
                        lignes_b_nettoyees = []  # Pour bloc complet à ignorer
                        for ligne in lignes_brutes:
                            ligne_strip = ligne.strip()
                            if ligne_strip.startswith("***"):
                                lignes_suivantes.append(ligne_strip[3:].strip())
                                lignes_b_nettoyees.append(ligne_strip)
                                trouver_texte = True
                            elif ligne_strip and trouver_texte:
                                lignes_suivantes.append(ligne_strip)
                                lignes_b_nettoyees.append(ligne_strip)
                            elif ligne_strip == "" and trouver_texte:
                                break

                        # 🛑 Stop net si on atteint ou dépasse le bon nombre
                        if len(lignes_suivantes) >= len(lignes):
                            bloc_b_complet = "\n".join(lignes_b_nettoyees)
                            break
                    if bloc2.strip() == bloc.strip():
                        trouver_debut = True
                # ✅ Ajouter le bloc B à ignorer (version nettoyée)
                if bloc_b_complet:
                    sous_blocs_ignorés.add(normaliser_bloc(bloc_b_complet))

                if lignes_suivantes:
                    tokens_2 = [l.split() for l in lignes_suivantes]
                    base_2 = tokens_2[liste_ref.current()]
                    temoins_2 = [chr(65 + i) for i in range(len(tokens_2))]

                    differences = defaultdict(lambda: defaultdict(list))
                    for i, ligne in enumerate(tokens_2):
                        if i == liste_ref.current():
                            continue
                        sm = difflib.SequenceMatcher(None, base_2, ligne)
                        for tag, i1, i2, j1, j2 in sm.get_opcodes():
                            if tag != "equal":
                                position = (i1, i2)
                                variante = " ".join(ligne[j1:j2])
                                differences[position][variante].append(temoins_2[i])

                    ligne_tei = []
                    ligne_latex = []
                    segment_buffer = []
                    i = 0
                    while i < len(base_2):
                        matching_apps = [key for key in differences.keys() if key[0] == i]
                        if matching_apps:
                            if segment_buffer:
                                segment_texte = " ".join(segment_buffer)
                                ligne_tei.append("      " + encoder_caracteres_tei(segment_texte) + "\n")
                                ligne_latex.append("      " + echapper_caracteres_latex(segment_texte))
                                segment_buffer = []

                            start, end = max(matching_apps, key=lambda x: x[1])
                            lem = " ".join(base_2[start:end])
                            rdgs = differences[(start, end)]
                            wit_lem = [temoins_2[j] for j, ligne in enumerate(tokens_2) if
                                       " ".join(ligne[start:end]) == lem]

                            tei_app = [f'      <app>\n']
                            tei_app.append(
                                f'        <lem wit="{" ".join(f"#{t}" for t in wit_lem)}">{encoder_caracteres_tei(lem)}</lem>\n')
                            for texte_rdg, liste_temoins in rdgs.items():
                                if texte_rdg != lem:
                                    wits = " ".join(f"#{t}" for t in liste_temoins)
                                    tei_app.append(
                                        f'        <rdg wit="{wits}">{encoder_caracteres_tei(texte_rdg)}</rdg>\n')
                            tei_app.append(f'      </app>\n')
                            ligne_tei.extend(tei_app)

                            rdg_blocks = [
                                f'        \\rdg[wit={{{", ".join(liste_temoins)}}}]{{{echapper_caracteres_latex(texte_rdg)}}}'
                                for texte_rdg, liste_temoins in rdgs.items() if texte_rdg != lem
                            ]
                            latex_block = [f'      \\app{{',
                                           f'        \\lem[wit={{{", ".join(wit_lem)}}}]{{{echapper_caracteres_latex(lem)}}}']
                            latex_block.extend(rdg_blocks)
                            latex_block.append('      }')
                            ligne_latex.append("\n".join(latex_block))

                            i = end
                        else:
                            segment_buffer.append(base_2[i])
                            i += 1

                    if segment_buffer:
                        segment_texte = " ".join(segment_buffer)
                        ligne_tei.append("      " + encoder_caracteres_tei(segment_texte) + "\n")
                        ligne_latex.append("      " + echapper_caracteres_latex(segment_texte))

                    # Gérer le changement de locuteur uniquement si nécessaire
                    if speaker_suivant != dernier_locuteur:
                        resultat_tei.append("    </sp>\n    <sp>\n      <speaker>{}</speaker>".format(speaker_suivant))
                        resultat_latex.append("      \\end{ekdverse}\n    \\end{speech}")
                        resultat_latex.append(
                            f'    \\begin{{speech}}\n      \\speaker{{{speaker_suivant}}}\n      \\begin{{ekdverse}}')
                        dernier_locuteur = speaker_suivant  # 🔄 mise à jour

                    # Ajout du vers 2
                    resultat_tei.append(f'<l n="{vers_num_2}">\n' + "".join(ligne_tei) + '</l>')

                    vers_formate_2 = "\n".join(ligne_latex)
                    resultat_latex.append(f'        \\vnum{{{vers_num_2}}}' + '{\n' + '\\hspace*{10em}' + vers_formate_2 + '\\\\    \n         }')

                    # 🔁 mise à jour pour la suite du traitement
                    speaker = speaker_suivant

                # 🔚 Ignorer bloc A aussi
                sous_bloc_texte = "\n".join(lignes)
                sous_blocs_ignorés.add(sous_bloc_texte)
                vers_courant = math.ceil(numero_vers_base) + 1
                continue

            # Si ligne unique non didascalique, on ignore
            if len(lignes) < 2:
                continue

            temoins = [chr(65 + i) for i in range(len(lignes))]
            tokens = [l.split() for l in lignes]
            ref_index = liste_ref.current()
            base = tokens[ref_index]

            differences = defaultdict(lambda: defaultdict(list))

            for i, ligne in enumerate(tokens):
                if i == ref_index:
                    continue
                sm = difflib.SequenceMatcher(None, base, ligne)
                for tag, i1, i2, j1, j2 in sm.get_opcodes():
                    if tag != "equal":
                        position = (i1, i2)
                        variante = " ".join(ligne[j1:j2])
                        differences[position][variante].append(temoins[i])

            ligne_tei = []
            ligne_latex = []
            segment_buffer = []

            i = 0
            while i < len(base):
                matching_apps = [key for key in differences.keys() if key[0] == i]
                if matching_apps:
                    if segment_buffer:
                        segment_texte = " ".join(segment_buffer)
                        ligne_tei.append("      " + encoder_caracteres_tei(segment_texte) + "\n")
                        ligne_latex.append("      " + echapper_caracteres_latex(segment_texte))
                        segment_buffer = []

                    start, end = max(matching_apps, key=lambda x: x[1])
                    lem = " ".join(base[start:end])
                    rdgs = differences[(start, end)]

                    wit_lem = []
                    for j, ligne in enumerate(tokens):
                        chunk = ligne[start:end]
                        if " ".join(chunk) == lem:
                            wit_lem.append(temoins[j])

                    tei_app = [f'      <app>\n']
                    tei_app.append(f'        <lem wit="{" ".join(f"#{t}" for t in wit_lem)}">{encoder_caracteres_tei(lem)}</lem>\n')
                    for texte_rdg, liste_temoins in rdgs.items():
                        if texte_rdg != lem:
                            wits = " ".join(f"#{t}" for t in liste_temoins)
                            tei_app.append(f'        <rdg wit="{wits}">{encoder_caracteres_tei(texte_rdg)}</rdg>\n')
                    tei_app.append(f'      </app>\n')
                    ligne_tei.extend(tei_app)

                    rdg_blocks = []
                    for texte_rdg, liste_temoins in rdgs.items():
                        if texte_rdg != lem:
                            rdg_blocks.append(f'        \\rdg[wit={{{", ".join(liste_temoins)}}}]{{{echapper_caracteres_latex(texte_rdg)}}}')
                    latex_block = [f'      \\app{{',
                                   f'        \\lem[wit={{{", ".join(wit_lem)}}}]{{{echapper_caracteres_latex(lem)}}}']
                    latex_block.extend(rdg_blocks)
                    latex_block.append('      }')
                    ligne_latex.append("\n".join(latex_block))

                    i = end
                else:
                    segment_buffer.append(base[i])
                    i += 1

            if segment_buffer:
                segment_texte = " ".join(segment_buffer)
                ligne_tei.append("      " + encoder_caracteres_tei(segment_texte) + "\n")
                ligne_latex.append("      " + echapper_caracteres_latex(segment_texte))

            resultat_tei.append(f'<l n="{vers_courant}">\n' + "".join(ligne_tei) + '</l>\n')
            vers_formate = "\n".join(ligne_latex)
            resultat_latex.append(f"        \\vnum{{{vers_courant}}}{{\n{vers_formate}  \\\\    \n        }}")
            if vers_courant == int(vers_courant):
                vers_courant += 1
            else:
                vers_courant = math.ceil(vers_courant)

        if dernier_locuteur != speaker:
            resultat_tei.append("    </sp>")
            resultat_latex.append("      \\end{ekdverse}\n    \\end{speech}")

    if current_scene_out:
        resultat_tei.append("    </sp>")
        resultat_tei.append("    </div>")
        resultat_latex.append("      \\end{ekdverse}\n    \\end{speech}   % Fin de la scène")

    if current_acte_out is not None:
        resultat_tei.append("</div>")
        resultat_latex.append("% Fin de l'acte")

    zone_resultat_tei.delete("1.0", tk.END)

    resultat_tei.append('</body></text>')
    resultat_tei.append('</TEI>')
    zone_resultat_tei.insert(tk.END, "\n".join(resultat_tei) + "\n")

    zone_resultat_latex.delete("1.0", tk.END)
    zone_resultat_latex.insert(tk.END, "\n".join(resultat_latex) + "\n")

    # Mise à jour automatique de la prévisualisation HTML
    if 'zone_resultat_html' in globals():
        try:
            html = convertir_tei_en_html_beau_ameliore(zone_resultat_tei.get("1.0", tk.END))
            zone_resultat_html.delete("1.0", tk.END)
            zone_resultat_html.insert(tk.END, html)
        except Exception as e:
            print(f"[Prévisualisation HTML] Erreur : {e}")

# Interface Tkinter
fenetre = tk.Tk()
# --- Menu principal ---
menu_bar = tk.Menu(fenetre)
fenetre.config(menu=menu_bar)

# --- Menu Fichier ---
menu_fichier = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Fichier", menu=menu_fichier)

menu_fichier.add_command(label="Exporter TEI", command=exporter_tei)
menu_fichier.add_command(label="Exporter la feuille XSLT", command=exporter_xslt)
menu_fichier.add_separator()
menu_fichier.add_command(label="Exporter LaTeX", command=exporter_latex)
menu_fichier.add_command(label="Exporter le template LaTeX", command=exporter_template_latex)
menu_fichier.add_separator()
menu_fichier.add_command(label="Exporter HTML", command=previsualiser_html)
menu_fichier.add_separator()
menu_fichier.add_command(label="Quitter", command=fenetre.quit)

# --- Menu Édition ---
menu_edit = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Édition", menu=menu_edit)

menu_edit.add_command(label="Couper", accelerator="Ctrl+X", command=lambda: fenetre.focus_get().event_generate('<<Cut>>'))
menu_edit.add_command(label="Copier", accelerator="Ctrl+C", command=lambda: fenetre.focus_get().event_generate('<<Copy>>'))
menu_edit.add_command(label="Coller", accelerator="Ctrl+V", command=lambda: fenetre.focus_get().event_generate('<<Paste>>'))
menu_edit.add_command(label="Tout sélectionner", accelerator="Ctrl+A", command=lambda: fenetre.focus_get().event_generate('<<SelectAll>>'))

# --- Menu Outils ---
menu_outils = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Outils", menu=menu_outils)

menu_outils.add_command(label="Valider la structure", command=valider_structure)
menu_outils.add_command(label="Comparer les états", command=comparer_etats)

# Menu Affichage
menu_affichage = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Affichage", menu=menu_affichage)
menu_affichage.add_command(label="Prévisualisation HTML", command=previsualiser_html)

# Menu Aide
menu_aide = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Aide", menu=menu_aide)
menu_aide.add_command(label="Afficher l'aide", command=lambda: messagebox.showinfo("Aide", "Bienvenue dans TEILaTeXStudio.\n\n- Utilisez 'Fichier > Comparer' pour générer le code TEI et LaTeX.\n- Prévisualisez en HTML dans 'Affichage'.\n- Saisissez le texte au format markdown théâtral.\n\nPour plus d'aide, consultez le fichier README."))

###



# Style parchemin pour les onglets TTK
style = ttk.Style()
style.theme_use('default')

style.configure("TNotebook", background="#fdf6e3", borderwidth=0)
style.configure("TNotebook.Tab", background="#f5ebc4", foreground="#4a3c1a", padding=[10, 4], font=("Georgia", 10, "bold"))
style.map("TNotebook.Tab", background=[("selected", "#e8dbab")])

#fenetre.iconbitmap("favicon.ico")
fenetre.title("Comparateur avec scènes, personnages et locuteurs")
fenetre.update_idletasks()
fenetre.minsize(1000, fenetre.winfo_reqheight())
fenetre.bind_all("<Control-s>", lambda event: enregistrer_saisie())
fenetre.bind("<Control-f>", lambda e: rechercher())
fenetre.bind("<Control-h>", lambda e: remplacer_avance())

afficher_nagscreen()

frame_saisie = tk.LabelFrame(fenetre, text="Saisie des variantes", padx=10, pady=5, bg="#f4f4f4")
frame_saisie.pack(fill=tk.BOTH, padx=10, pady=10)

label_texte = tk.Label(frame_saisie, text="Utilisez ####a#### pour un acte, ###n### pour une scène, ##Nom## pour les personnages, et #Nom# pour le locuteur :", bg="#f4f4f4")
label_texte.pack()

zone_saisie = scrolledtext.ScrolledText(frame_saisie, height=15, undo=True, maxundo=-1)
zone_saisie.pack(fill=tk.BOTH, expand=True)

try:
    nom_auto = nom_fichier("autosave", "txt")
    if os.path.exists(nom_auto):
        with open(nom_auto, "r", encoding="utf-8") as f:
            zone_saisie.insert("1.0", f.read())
except Exception as e:
    print(f"[autosave] Impossible de charger le fichier : {e}")

def boite_initialisation_parchemin():
    champs_def = [
        ("Titre de la pièce", ""),
        ("Numéro de l'acte", ""),
        ("Numéro de la scène", ""),
        ("Nombre de scènes dans l'acte", ""),
        ("Noms des personnages (séparés par virgule)", ""),
    ]

    dialog = tk.Toplevel()
    dialog.title("Initialisation du projet")
    dialog.configure(bg="#fdf6e3")
    dialog.geometry("540x320")
    dialog.grab_set()

    police_label = ("Georgia", 11)
    police_entree = ("Georgia", 11)

    champs_vars = {}

    for label_text, default in champs_def:
        var = tk.StringVar(value=default)
        champs_vars[label_text] = var

        frame = tk.Frame(dialog, bg="#fdf6e3")
        frame.pack(padx=20, pady=5, fill=tk.X)

        label = tk.Label(frame, text=label_text, bg="#fdf6e3", fg="#4a3c1a", font=police_label)
        label.pack(side=tk.LEFT)

        # Large zone de saisie pour la ligne des personnages
        if "personnages" in label_text.lower():
            entry = tk.Entry(frame, textvariable=var, font=police_entree, width=45)
        else:
            entry = tk.Entry(frame, textvariable=var, font=police_entree, width=30)

        entry.pack(side=tk.RIGHT)

    result = {}

    def valider():
        for key, var in champs_vars.items():
            result[key] = var.get()
        dialog.destroy()

    bouton = tk.Button(dialog, text="Valider", font=("Georgia", 11, "bold"),
                       bg="#f5ebc4", fg="#4a3c1a", command=valider)
    bouton.pack(pady=20)

    dialog.bind("<Return>", lambda e: valider())
    dialog.wait_window()
    return result



def initialiser_projet():
    infos = boite_initialisation_parchemin()
    global titre_piece, numero_acte, numero_scene, nombre_scenes
    titre_piece = infos["Titre de la pièce"]
    numero_acte = infos["Numéro de l'acte"]
    numero_scene = infos["Numéro de la scène"]
    nombre_scenes = infos["Nombre de scènes dans l'acte"]
    noms_persos = infos["Noms des personnages (séparés par virgule)"]

    titre_nettoye = nettoyer_identifiant(titre_piece)
    nom_court = f"{titre_nettoye}_A{numero_acte}_S{numero_scene}of{nombre_scenes}"
    fenetre.title(f"TEILaTeXStudio – {nom_court}")

    ligne_personnages = " ".join(f"##{nom.strip()}##" for nom in noms_persos.split(",") if nom.strip())

    zone_saisie.insert("1.0",
                       f"####{numero_acte}####\n\n"
                       f"###{numero_scene}###\n\n"
                       f"{ligne_personnages}\n\n"
                       )


def autosave(event=None):
    try:
        contenu = zone_saisie.get("1.0", tk.END)
        nom_auto = nom_fichier("autosave", "txt")
        with open(nom_auto, "w", encoding="utf-8") as f:
            f.write(contenu)
    except Exception as e:
        print(f"[autosave] Erreur d'enregistrement : {e}")

zone_saisie.bind("<KeyRelease>", autosave)
zone_saisie.bind("<KeyRelease>", mettre_a_jour_menu)

frame_params = tk.LabelFrame(fenetre, text="Paramètres", padx=10, pady=5, bg="#f4f4f4")
frame_params.pack(fill=tk.X, padx=10, pady=10)

frame_bas = tk.Frame(fenetre)
frame_bas.pack(pady=10)

btn_comparer = tk.Button(frame_bas, text="générer code", command=comparer_etats)
btn_comparer.pack(side=tk.LEFT, padx=10)

btn_export_tei = tk.Button(frame_bas, text="💾 Exporter TEI", command=exporter_tei)
btn_export_tei.pack(side=tk.LEFT, padx=10)

btn_export_latex = tk.Button(frame_bas, text="💾 Exporter LaTeX", command=exporter_latex)
btn_export_latex.pack(side=tk.LEFT, padx=10)

btn_sauver_saisie = tk.Button(frame_bas, text="💾 Export saisie brute", command=enregistrer_saisie)
btn_sauver_saisie.pack(side=tk.LEFT, padx=10)

btn_remplacer = tk.Button(frame_bas, text="Remplacer (Ctrl+H)", command=remplacer_avance)
btn_remplacer.pack(side=tk.LEFT, padx=10)

btn_previsualiser = tk.Button(frame_bas, text="🌐 Preview", command=previsualiser_html)
btn_previsualiser.pack(side=tk.LEFT, padx=10)

btn_quitter = tk.Button(frame_bas, text="Exit", command=confirmer_quitter)
ajouter_bouton_validation(frame_bas)
btn_aide = tk.Button(frame_bas, text="❔ Aide", command=afficher_aide)
btn_aide.pack(side=tk.LEFT, padx=10)
btn_quitter.pack(side=tk.RIGHT, padx=10)

frame_ref = tk.Frame(frame_params, bg="#f4f4f4")
frame_ref.pack(side=tk.LEFT, padx=10)

label_ref = tk.Label(frame_ref, text="Témoin de référence :", bg="#f4f4f4")
label_ref.pack(side=tk.LEFT)

menu_ref = ttk.Combobox(frame_ref, state="readonly", width=5)
menu_ref.pack(side=tk.LEFT)
liste_ref = menu_ref

frame_vers = tk.Frame(frame_params, bg="#f4f4f4")
frame_vers.pack(side=tk.LEFT, padx=10)

label_vers = tk.Label(frame_vers, text="Numéro du 1er vers :", bg="#f4f4f4")
label_vers.pack(side=tk.LEFT)

entree_vers = tk.Entry(frame_vers, width=5)
entree_vers.insert(0, "1")
entree_vers.pack(side=tk.LEFT)

notebook = ttk.Notebook(fenetre)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# TEI
onglet_tei = tk.Frame(notebook, bg="white")
zone_resultat_tei = scrolledtext.ScrolledText(onglet_tei, height=15, undo=True, maxundo=-1)
zone_resultat_tei.pack(fill=tk.BOTH, expand=True)
notebook.add(onglet_tei, text="🧾 TEI")

# LaTeX
onglet_latex = tk.Frame(notebook, bg="white")
zone_resultat_latex = scrolledtext.ScrolledText(onglet_latex, height=15, undo=True, maxundo=-1)
zone_resultat_latex.pack(fill=tk.BOTH, expand=True)
notebook.add(onglet_latex, text="📘 LaTeX")

# HTML
onglet_html = tk.Frame(notebook, bg="white")
zone_resultat_html = scrolledtext.ScrolledText(onglet_html, height=15, undo=True, maxundo=-1, bg="white", fg="#4a3c1a", font=("Georgia", 11))
zone_resultat_html.pack(fill=tk.BOTH, expand=True)
notebook.add(onglet_html, text="🌐 html")


#appliquer_style_light(fenetre)
appliquer_style_parchemin(fenetre)

# --- Raccourcis clavier globaux ---
# Sans doute à effacer tous
fenetre.bind_all("<Control-a>", lambda event: fenetre.focus_get().event_generate('<<SelectAll>>'))
fenetre.bind_all("<Control-x>", lambda event: fenetre.focus_get().event_generate('<<Cut>>'))
fenetre.bind_all("<Control-c>", lambda event: fenetre.focus_get().event_generate('<<Copy>>'))
# fenetre.bind_all("<Control-v>", lambda event: fenetre.focus_get().event_generate('<<Paste>>'))


fenetre.mainloop()
