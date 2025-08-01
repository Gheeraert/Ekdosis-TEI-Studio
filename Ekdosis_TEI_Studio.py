# ==============================================================================
# Ekdosis-TEI Studio
# Version 1.5
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
# Date de création : mars 2025 - juillet 2025
# Licence : MIT
# ==============================================================================

from tkinter import filedialog
from tkinter import filedialog as fd, scrolledtext, ttk, font
import difflib
from collections import defaultdict
import re
import unicodedata
import sys
import math
import lxml.etree as ET
import tempfile
import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import Toplevel, Radiobutton, StringVar
import lxml.etree as LET
import os
import webbrowser
from datetime import date
import locale
import json
from bs4 import BeautifulSoup

# 1. Le mapping mois → nom français
MOIS_FR = {
    1: "janvier",  2: "février", 3: "mars",     4: "avril",
    5: "mai",      6: "juin",    7: "juillet",  8: "août",
    9: "septembre",10: "octobre",11: "novembre",12: "décembre",
}

# 2. La fonction qui formate votre date
def french_date(dt: date) -> str:
    return f"{dt.day:02d} {MOIS_FR[dt.month]} {dt.year}"

def importer_echantillon():
    exemple = """####acte 1####
####acte 1####
####acte 1####
####acte 1####

###scene 1###
###scene 1###
###scene 1###
###scene 1###

##Antiochus## ##Arsace##
##Antiochus## ##Arsace##
##Antiochus## ##Arsace##
##Antiochus## ##Arsace##

#Antiochus#
#Antiochus#
#Antiochus#
#Antiochus#

**Antiochus entre**
**Antiochus entre**
**Antiochus entre**
**Antiochus entre**

Arrestons un moment. La pompe de ces lieux,
Arrestons un moment. La pompe de ces lieux,
Arrestons un moment. La pompe de ces lieux,
Arrestons un moment. La pompe de ces lieux,

Je le voy bien, Arsace, est nouvelle à tes yeux
Je le voy bien, Arsace, est nouvelle à tes yeux
Je le vois bien, Arsace, est nouvelle à tes yeux
Je le vos bien, Arsace, est nouvelle à tes yeux

Souvent ce Cabinet***
Souvent ce Cabinet***
Souvent ce Cabinet***
Souvent ce Cabinet***

#Arsace#
#Arsace#
#Arsace#
#Arsace#

***superbe & solitaire,
***superbe & solitaire,
***superbe & solitaire,
***superbe & solitaire,

#Antiochus#
#Antiochus#
#Antiochus#
#Antiochus#

Des secrets de Titus est le dépositaire.
Des secrets de Titus est le dépositaire.
Des secrets de Titus est le dépositaire.
Des secrets de Titus est le dépositaire.

C'est icy quelquefois qu'il se cache à sa Cour,
C'est icy quelquefois qu'il se cache à sa Cour,
C'est ici quelquefois qu'il se cache à sa Cour,
C'est ici quelquefois qu'il se cache à sa Cour,    

Lors qu'il vient à la Reyne expliquer son amour
Lors qu'il vient à la Reine expliquer son amour.
Lors qu'il vient à la Reine expliquer son amour.
Lors qu'il vient à la Reine expliquer son amour.

De son Apartement cette porte est prochaine
De son Apartement cette porte est prochaine
De son Apartement cette porte est prochaine
De son Appartement cette porte est prochaine

Et cette autre conduit dans celuy de la Reyne.
Et cette autre conduit dans celuy de la Reyne.
Et cette autre conduit dans celui de la Reine.
Et cette autre conduit dans celuy de la Reine.

Va chez elle. Dy-luy qu'importun à regret,
Va chez elle. Dy-luy qu'importun à regret,
Va chés elle. Di-lui qu'importun à regret,
Va chez elle. Di-Luy qu'importun à regret,

J'ose luy demander un entretien secret.
J'ose luy demander un entretien secret.
J'ose luy demander un entretien secret.
J'ose luy demander un entretien secret.

#Arsace#
#Arsace#
#Arsace#
#Arsace#

Vous, Seigneur, importun Vous cet Amy fidelle
Vous, Seigneur, importun~? Vous cet Amy fidelle
Vous, Seigneur, importun~? Vous cet Ami fidelle
Vous, Seigneur, importun~? Vous cet Ami fidelle

Qu'un soin si gerereux interesse pour elle?
Qu'un soin si gerereux interesse pour elle?
Qu'un soin si gerereux interesse pour elle?
Qu'un soin si gerereux interesse pour elle?

Vous, cet Antiochus, son Amant autrefois;
Vous, cet Antiochus, son Amant autrefois;
Vous, cet Antiochus, son Amant autrefois;
Vous, cet Antiochus, son Amant autrefois;

Vous, que l'Orient conte entre ses plus grands Rois?
Vous, que l'Orient conte entre ses plus grands Rois?
Vous, que l'Orient conte entre ses plus grands Rois?
Vous, que l'Orient conte entre ses plus grands Rois:

Quoy déja de Titus l'Epouse en espérance
Quoi~! déja de Titus l'Epouse en espérance
Quoy~! déja de Titus l'Epouse en espérance
Quoy~! déja de Titus Epouse en espérance

Ce rang entre elle et vous met-il tant de distance~?
Ce rang entre elle et vous met-il tant de distance.
Ce rang entre elle et vous met-il tant de distance~?
Ce rang entre elle et vous met-il tant de distance~? 

#Antiochus#
#Antiochus#
#Antiochus#
#Antiochus#

Va, dis-je, et sans vouloir te charger d'autres soins,
Va, dis-je, et sans vouloir te charger d'autres soins;
Va, dis-je, et sans vouloir te charger d'autres soins?
Va, dis-je, et sans savoir te charger d'autres soins?

Voy si je puis bientost luy parler sans témoins.
Voy si je puis bientost luy parler sans témoins.
Voi si je puis bientost lui parler sans témoins.
Voi si je puis bientost luy parler sans témoins.
"""

    zone_saisie.delete("1.0", tk.END)
    zone_saisie.insert("1.0", exemple)
    messagebox.showinfo("Échantillon chargé", "Extrait de *Bérénice* inséré.")


template_ekdosis_preamble = r"""
    %
    % Template ekdosis (ekdosis) pour l'édition du théâtre classique
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
    % Affichage automatique en ekdosis-ekdosis
    % (La config ci-dessous prévient l'affichage du 
    % numéro de paragraphe à gauche)
    %
    % Pour activer la numérotation de 5 en 5 :
    \SetLineation{
    %   modulo,
        vmodulo=5
    }
    % Pour désactiver la numérotation superflue à gauche:
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
    """

template_ekdosis_debut_doc = r"""     
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
        %   \castitem{\role{xmlid=antiochus}Antiochus, \roledesc{roi de Comagène}}
        %   \castitem{\role{xmlid=arsace}Arsace, \roledesc{Confident d'Antiochus}}
        %\end{cast}
        %\set{La Scene est à Rome}
        %\normalfont

        % INJECTION DU CODE GENERE:
        """
template_ekdosis_fin_doc = r"""
    %%%%%%%%%
        \end{ekdosis}
    \end{document}
    """


def exporter_template_ekdosis():
    template_ekdosis_exemple_apparat = "\n".join([
        f"\\DeclareWitness{{{t['abbr']}}}{{{t['year']}}}{{{t['desc']}}}"
        for t in temoins
    ])
    chemin = filedialog.asksaveasfilename(
        defaultextension=".tex",
        filetypes=[("Fichier ekdosis", "*.tex")],
        title="Enregistrer le template ekdosis"
    )
    if chemin:
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(
                template_ekdosis_preamble + template_ekdosis_exemple_apparat + template_ekdosis_debut_doc + template_ekdosis_fin_doc)


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
    nag.title("Bienvenue dans Ekdosis-TEI Studio")

    # Thème parchemin
    COULEUR_FOND = "#fdf6e3"
    COULEUR_ENCADRE = "#f5ebc4"
    COULEUR_TEXTE = "#4a3c1a"
    POLICE_SERIF = "Georgia"

    nag.configure(bg=COULEUR_FOND)

    largeur_nag = 540
    hauteur_nag = 550
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
        text="Ekdosis–TEI Studio",
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
        text="""Assistant pour l'encodage des variantes des textes de théâtre

        par T. Gheeraert
        Presses de l'Université de Rouen et du Havre
        Chaire d'excellence en éditions numériques
        CEREdI (UR 3229)
        ceen_team@univ-rouen.fr""",
        font=("Georgia", 12),
        bg=COULEUR_FOND,
        fg=COULEUR_TEXTE,
        justify="center"
    )
    chaire.pack(pady=(0, 10))

    # Bouton
    def commencer():
        nag.destroy()
        initialiser_projet(mode_test=False)

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


def reset_application():
    confirmation = messagebox.askyesno("Confirmation", "Voulez-vous vraiment réinitialiser l'application ?")
    if not confirmation:
        return
    global titre_piece, numero_acte, numero_scene, nombre_scenes
    global auteur_nom_complet, editeur_nom_complet
    global vers_num

    # Réinitialisation des variables globales
    titre_piece = ""
    numero_acte = ""
    numero_scene = ""
    nombre_scenes = ""
    auteur_nom_complet = ""
    editeur_nom_complet = ""

    # Effacer le contenu des zones de texte
    zone_saisie.delete("1.0", tk.END)
    zone_resultat_tei.delete("1.0", tk.END)
    zone_resultat_ekdosis.delete("1.0", tk.END)

    # Réinitialiser la liste des témoins si elle existe
    try:
        liste_ref.set("")
        menu_ref["values"] = []
    except:
        pass

    # Réinitialiser la prévisualisation HTML si elle existe
    if 'zone_resultat_html' in globals():
        zone_resultat_html.delete("1.0", tk.END)

    initialiser_projet()


def demander_numero_vers():
    fenetre = tk.Toplevel()
    fenetre.title("Numéro du vers")
    fenetre.configure(bg="#fdf6e3")
    fenetre.grab_set()
    fenetre.resizable(False, False)
    # DEBUG Tout est collé en "dur" il faudrait passer les variables COULEUR_FOND, etc
    tk.Label(fenetre, text="Veuillez entrer le numéro du vers de départ :",
             bg="#fdf6e3", fg="#4a3c1a", font=("Georgia", 12)).pack(padx=20, pady=(20, 10))

    champ = tk.Entry(fenetre, font=("Georgia", 12), justify="center", width=10)
    champ.pack(pady=(0, 15))
    champ.focus()

    resultat = {"valeur": None}

    def valider():
        resultat["valeur"] = champ.get().strip()
        fenetre.destroy()

    bouton_valider = tk.Button(fenetre, text="Valider", command=valider,
                               bg="#fdf6e3", fg="#4a3c1a",
                               font=("Georgia", 12))
    bouton_valider.pack(pady=(0, 20))

    fenetre.bind("<Return>", lambda event: valider())
    fenetre.wait_window()

    return resultat["valeur"]


def demander_mode_saisie():
    fenetre = tk.Toplevel()
    fenetre.title("Choisissez votre mode de saisie")
    fenetre.configure(bg="#f5f0dc")  # ton parchemin doux

    # Dimensions fixes
    fenetre.geometry("400x220")
    fenetre.resizable(False, False)

    # Cadre parcheminé
    cadre = tk.Frame(fenetre, bg="#f5f0dc", bd=3, relief=tk.GROOVE)
    cadre.pack(expand=True, fill="both", padx=20, pady=20)

    # Titre
    label = tk.Label(
        cadre,
        text="Souhaitez-vous activer la saisie assistée ?",
        bg="#f5f0dc",
        fg="#4b3f2f",
        font=("Garamond", 14, "bold"),
        wraplength=360,
        justify="center"
    )
    label.pack(pady=(10, 20))

    # Boutons
    bouton_assistee = tk.Button(
        cadre,
        text="Saisie assistée",
        font=("Garamond", 12),
        bg="#e0d8b0",
        fg="black",
        relief=tk.RAISED,
        command=lambda: choisir_mode(fenetre, True)
    )
    bouton_assistee.pack(pady=5)

    bouton_libre = tk.Button(
        cadre,
        text="Saisie libre",
        font=("Garamond", 12),
        bg="#ddd4aa",
        fg="black",
        relief=tk.RAISED,
        command=lambda: choisir_mode(fenetre, False)
    )
    bouton_libre.pack(pady=5)

    # Bouton de fermeture (pour laisser l’utilisateur libre)
    bouton_annuler = tk.Button(
        cadre,
        text="Annuler",
        font=("Garamond", 11),
        bg="#cbbf9b",
        fg="black",
        command=fenetre.destroy
    )
    bouton_annuler.pack(pady=(10, 5))


def choisir_mode(fenetre, mode_assiste):
    fenetre.destroy()
    if mode_assiste:
        lancer_saisie_assistee()
    else:
        print("[INFO] Saisie libre sélectionnée.")  # ou rien


def lancer_saisie_assistee_par_menu():
    global vers_num, numero_vers, flag_numero_vers
    numero_vers = demander_numero_vers()
    flag_numero_vers = 1

    lancer_saisie_assistee()


def lancer_saisie_assistee():  # Menu principal de l'assistant de saisie
    global vers_num, numero_vers, flag_numero_vers
    fenetre = Toplevel()
    fenetre.title("Assistant de saisie")
    fenetre.configure(bg="#fdf6e3")
    fenetre.geometry("400x300")
    fenetre.grab_set()
    if flag_numero_vers != 1:
        numero_vers = vers_num  # Pour l'affichage dans le titre de la boîte
        flag_numero_vers = 0

    # Style parchemin
    cadre = tk.Frame(fenetre, bg="#fdf6e3", padx=20, pady=20)
    cadre.pack(expand=True, fill="both")

    # Texte d'intro
    tk.Label(cadre, text="Que souhaitez-vous faire ?", font=("Garamond", 14, "bold"),
             bg="#fdf6e3", wraplength=350).pack(pady=(0, 10))

    choix = StringVar()
    choix.set("dialogue")  # Valeur par défaut

    # Boutons radio
    options = [
        ("Transcrire un nouvel acte", "acte"),
        ("Transcrire une nouvelle scène", "scene"),
        ("Changer de locuteur", "locuteur"),
        ("Entrer du dialogue", "dialogue"),
        ("Fermer l’assistant", "fermer")
    ]

    for label, value in options:
        Radiobutton(cadre, text=label, variable=choix, value=value,
                    font=("Garamond", 12), bg="#fdf6e3",
                    selectcolor="#eee8d5", anchor="w", justify="left").pack(anchor="w")

    def valider_choix():
        global vers_num, numero_vers
        selection = choix.get()
        fenetre.destroy()
        if selection == "acte":
            ouvrir_saisie_acte()
        elif selection == "scene":
            ouvrir_saisie_scene()
        elif selection == "locuteur":
            ouvrir_saisie_locuteur()
        elif selection == "dialogue":
            ouvrir_saisie_vers()
        elif selection == "fermer":
            return

    tk.Button(cadre, text="Valider", command=valider_choix, bg="#e0cda9",
              font=("Garamond", 12, "bold")).pack(pady=20)


def ouvrir_saisie_vers():
    global vers_num, nombre_temoins_predefini, numero_vers
    boite = tk.Toplevel()
    boite.title(f"Saisie du vers {numero_vers}")
    boite.configure(bg="#f5f0e6")
    boite.grab_set()

    tk.Label(boite, text=f"Vers {numero_vers}", font=("Garamond", 16, "bold"),
             background="#f5f0e6").pack(pady=10)

    entrees = []

    for i in range(nombre_temoins_predefini):
        cadre = tk.Frame(boite, bg="#f5f0e6")
        cadre.pack(pady=5, padx=10, anchor="w")

        label = tk.Label(cadre, text=f"Témoin {i + 1} :", font=("Garamond", 12), bg="#f5f0e6")
        label.grid(row=0, column=0, sticky="w")

        entree = tk.Entry(cadre, width=60, font=("Courier", 11))
        entree.grid(row=0, column=1, padx=5)
        entrees.append(entree)

    # Une seule paire de cases à cocher globales
    var_debut = tk.BooleanVar()
    var_fin = tk.BooleanVar()

    cadre_check = tk.Frame(boite, bg="#f5f0e6")
    cadre_check.pack(pady=(10, 0), anchor="w", padx=10)

    tk.Checkbutton(
        cadre_check, text="Début de vers partagé",
        variable=var_debut, bg="#f5f0e6", font=("Garamond", 10)
    ).pack(anchor="w")

    tk.Checkbutton(
        cadre_check, text="Fin de vers partagé",
        variable=var_fin, bg="#f5f0e6", font=("Garamond", 10)
    ).pack(anchor="w")

    def traitement_saisie_vers(suite="meme_locuteur"):
        global numero_vers, flag
        flag = 0

        # Test : tous les champs sont-ils vides ?
        tous_vides = all(not entree.get().strip() for entree in entrees)

        # Avertissement si certains champs sont vides
        if not tous_vides:
            for i, entree in enumerate(entrees):
                if not entree.get().strip():
                    messagebox.showwarning(
                        "Champs incomplets",
                        f"La ligne du témoin {i + 1} est vide. Veuillez la remplir avant de continuer.")
                    break

        # Blocage si deux cases cochées
        if var_debut.get() and var_fin.get():
            messagebox.showerror(
                "Erreur de saisie",
                "Ne pas cocher à la fois 'début' et 'fin de vers partagé'.")
            return

        # Préparation des lignes à insérer
        lignes = []
        for i in range(nombre_temoins_predefini):
            texte = entrees[i].get().strip()
            if var_debut.get():
                if flag != 1:
                    texte = texte + "***"
                    numero_vers -= 1
                    flag = 1
                else:
                    texte = texte + "***"
            elif var_fin.get():
                texte = "***" + texte
            lignes.append(texte)

        # Si vraiment tous les champs sont vides → on ferme sans rien insérer
        if all(not ligne for ligne in lignes):
            boite.destroy()
            return

        # Insertion
        zone_saisie.insert(tk.END, "\n".join(lignes) + "\n\n")
        boite.destroy()

        # Suite logique
        if suite == "fermer":
            return
        if suite == "meme_locuteur":
            numero_vers += 1
            ouvrir_saisie_vers()
        elif suite == "changement_locuteur":
            numero_vers += 1
            ouvrir_saisie_locuteur()
        elif suite == "fin_scene":
            numero_vers += 1
            ouvrir_saisie_scene()

    # Boutons de validation
    cadre_boutons = tk.Frame(boite, bg="#f5f0e6")
    cadre_boutons.pack(pady=15)

    tk.Button(cadre_boutons, text="Didascalie",
              command=lambda: [traitement_saisie_vers("fermer"), ouvrir_didascalie(callback_apres=ouvrir_saisie_vers)],
              font=("Garamond", 10), bg="#ddd4c3").grid(row=0, column=3, padx=5)

    tk.Button(cadre_boutons, text="Même locuteur",
              command=lambda: traitement_saisie_vers("meme_locuteur")).grid(row=0, column=0, padx=5)

    tk.Button(cadre_boutons, text="Changement de locuteur",
              command=lambda: traitement_saisie_vers("changement_locuteur")).grid(row=0, column=1, padx=5)

    tk.Button(cadre_boutons, text="Nouvelle scène",
              command=lambda: traitement_saisie_vers("fin_scene")).grid(row=0, column=2, padx=5)

    # Remplace "fermer sans rien faire" par "Fermer", en copiant les vers
    tk.Button(boite, text="Fermer", command=lambda: traitement_saisie_vers("fin_scene")).pack(pady=(0, 10))


def ouvrir_didascalie(callback_apres=None):
    fenetre_dida = tk.Toplevel()
    fenetre_dida.title("Ajouter une didascalie")
    fenetre_dida.configure(bg="#fdf6e3")
    fenetre_dida.grab_set()

    cadre = tk.Frame(fenetre_dida, bg="#fdf6e3", padx=20, pady=20)
    cadre.pack(expand=True, fill="both")

    tk.Label(cadre, text="Didascalie :", font=("Garamond", 12), bg="#fdf6e3").pack()
    champ_dida = tk.Entry(cadre, width=50, font=("Garamond", 12))
    champ_dida.pack(pady=(0, 10))

    def valider_dida():
        texte = champ_dida.get().strip()
        if texte:
            zone_saisie.insert(tk.END, f"\n**{texte}**\n\n")
        fenetre_dida.destroy()
        if callback_apres:
            callback_apres()

    tk.Button(cadre, text="Insérer", command=valider_dida,
              font=("Garamond", 12), bg="#e0cda9").pack(pady=(5, 5))

    tk.Button(cadre, text="Fermer", command=fenetre_dida.destroy,
              font=("Garamond", 10), bg="#eee8d5").pack()


def ouvrir_saisie_locuteur():
    global numero_vers
    fenetre = Toplevel()
    fenetre.title("Changer de locuteur")
    fenetre.configure(bg="#fdf6e3")
    fenetre.geometry("300x200")
    fenetre.grab_set()

    cadre = tk.Frame(fenetre, bg="#fdf6e3", padx=20, pady=20)
    cadre.pack(expand=True, fill="both")

    tk.Label(cadre, text="Nom du nouveau locuteur :", font=("Garamond", 12),
             bg="#fdf6e3").pack(pady=(0, 10))

    champ_nom = tk.Entry(cadre, font=("Garamond", 12), justify="center")
    champ_nom.pack(pady=(0, 10))

    def valider(event=None):
        global vers_num, numero_vers
        nom = champ_nom.get().strip()
        if nom:
            ligne = f"#{nom}#\n"
            zone_saisie.insert(tk.END, ligne)
            fenetre.destroy()
            ouvrir_saisie_vers()  # saut automatique vers la saisie des vers
        else:
            messagebox.showwarning("Erreur", "Veuillez entrer un nom de locuteur.")

    fenetre.bind('<Return>', valider)

    tk.Button(cadre, text="Valider", command=valider,
              font=("Garamond", 12), bg="#e0cda9").pack(pady=(10, 0))

    tk.Button(cadre, text="Fermer", command=fenetre.destroy,
              font=("Garamond", 10), bg="#eee8d5").pack(pady=(5, 0))


def ouvrir_saisie_scene():
    global vers_num, numero_vers
    fenetre_scene = tk.Toplevel()
    fenetre_scene.title("Changement de scène")
    fenetre_scene.configure(bg="#fdf6e3")
    fenetre_scene.grab_set()

    tk.Label(fenetre_scene, text="Numéro de scène :", bg="#fdf6e3", font=("Garamond", 12)).pack(padx=10, pady=(10, 0))
    entree_num_scene = tk.Entry(fenetre_scene, width=30, justify="center")
    entree_num_scene.pack(padx=10, pady=5)
    entree_num_scene.focus_set()

    tk.Label(fenetre_scene, text="Personnages présents :", bg="#fdf6e3", font=("Garamond", 12)).pack(padx=10,
                                                                                                     pady=(10, 0))
    entree_personnages = tk.Entry(fenetre_scene, width=50)
    entree_personnages.insert(0, "##Nom## ##AutreNom##")  # exemple de syntaxe
    entree_personnages.pack(padx=10, pady=5)

    tk.Label(fenetre_scene, text="Premier locuteur :", bg="#fdf6e3", font=("Garamond", 12)).pack(padx=10, pady=(10, 0))
    entree_locuteur = tk.Entry(fenetre_scene, width=30)
    entree_locuteur.insert(0, "#Nom#")  # exemple de syntaxe
    entree_locuteur.pack(padx=10, pady=5)

    def valider_scene():
        global vers_num, numero_vers
        num_scene = entree_num_scene.get().strip()
        persos = entree_personnages.get().strip()
        premier = entree_locuteur.get().strip()
        if num_scene and persos and premier:
            texte_scene = f"\n###{num_scene}###\n{persos}\n{premier}\n"
            zone_saisie.insert(tk.END, texte_scene)
        fenetre_scene.destroy()
        ouvrir_saisie_vers()

    bouton_valider = tk.Button(fenetre_scene, text="Valider", command=valider_scene, bg="#e0c097")
    bouton_valider.pack(pady=(10, 5))

    bouton_fermer = tk.Button(fenetre_scene, text="Fermer", command=fenetre_scene.destroy, bg="#e0c097")
    bouton_fermer.pack(pady=(0, 10))


def ouvrir_saisie_acte():
    global versnum, numero_vers
    fenetre = Toplevel()
    fenetre.title("Nouvel acte")
    fenetre.configure(bg="#fdf6e3")
    fenetre.grab_set()

    cadre = tk.Frame(fenetre, bg="#fdf6e3", padx=20, pady=20)
    cadre.pack(expand=True, fill="both")

    tk.Label(cadre, text="Numéro de l'acte :", font=("Garamond", 12),
             bg="#fdf6e3").pack(pady=(0, 10))

    champ_acte = tk.Entry(cadre, font=("Garamond", 12), justify="center")
    champ_acte.pack(pady=(0, 10))
    fenetre.bind("<Return>", lambda event: valider())

    def valider():
        numero = champ_acte.get().strip()
        if numero.isdigit():
            ligne = f"####{numero}####\n"
            zone_saisie.insert(tk.END, ligne)
            fenetre.destroy()
            ouvrir_saisie_scene()
        else:
            messagebox.showwarning("Erreur", "Veuillez entrer un numéro d'acte valide.")

    bouton = tk.Button(cadre, text="Valider", command=valider,
                       font=("Garamond", 12), bg="#e0cda9")
    bouton.pack(pady=(10, 0))

    # Bouton pour quitter sans valider
    tk.Button(cadre, text="Fermer", command=fenetre.destroy,
              font=("Garamond", 10), bg="#eee8d5").pack(pady=(5, 0))


vers_actuel = 1
bloc_saisie = []


def traitement_saisie(textes, action):
    global vers_actuel, bloc_saisie

    # On stocke les textes saisis pour ce vers
    bloc_saisie.append((vers_actuel, textes))

    if action == "meme":
        vers_actuel += 1
        ouvrir_boite_saisie_vers(vers_actuel, temoins, traitement_saisie)

    elif action == "changement":
        ouvrir_boite_changement_locuteur()

    elif action == "fin":
        messagebox.showinfo("Scène terminée", f"{len(bloc_saisie)} vers encodés.")
        # Ici on pourrait injecter dans la zone de saisie principale par exemple.


def initialiser_projet(mode_test=False):
    # DEBUG - MODE TEST NON BLOQUANT
    if mode_test:
        infos = {
            "Prénom de l'auteur": "Jean",
            "Nom de l'auteur": "Racine",
            "Titre de la pièce": "Phèdre",
            "Numéro de l'acte": "1",
            "Numéro de la scène": "1",
            "Nombre de scènes dans l'acte": "5",
            "Numéro du vers de départ": "1",
            "Noms des personnages (séparés par virgule)": "Phèdre, Hippolyte, Théramène",
            "Nombre de témoins": "3",
            "Nom de l'éditeur (vous)": "Manutius",
            "Prénom de l'éditeur": "Aldo"
        }
    else:
        ### FIN DU BLOC TEST - A SUPPRIMER
        infos = boite_initialisation_parchemin()

    # Déclaration des variables globales
    global prenom_auteur, nom_auteur, auteur_nom_complet, titre_piece, numero_acte
    global numero_scene, nombre_scenes, nombre_temoins, nombre_temoins_predefini
    global nom_editeur, prenom_editeur, editeur_nom_complet
    global vers_num, numero_vers, noms_persos
    global temoins_collectes
    #
    prenom_auteur = infos["Prénom de l'auteur"]
    nom_auteur = infos["Nom de l'auteur"]
    titre_piece = infos["Titre de la pièce"]
    numero_acte = infos["Numéro de l'acte"]
    numero_scene = infos["Numéro de la scène"]
    nombre_scenes = infos["Nombre de scènes dans l'acte"]
    vers_num = infos["Numéro du vers de départ"]
    vers_num = int(vers_num)
    entree_vers.delete(0, tk.END)  # combobox
    entree_vers.insert(0, str(vers_num))
    numero_vers = vers_num  # pour utilisation locale dans les boîtes de saisie
    noms_persos = infos["Noms des personnages (séparés par virgule)"]
    nombre_temoins = infos["Nombre de témoins"]
    nombre_temoins_predefini = int(nombre_temoins)
    nom_editeur = infos["Nom de l'éditeur (vous)"]
    prenom_editeur = infos["Prénom de l'éditeur"]

    auteur_nom_complet = f"{prenom_auteur} {nom_auteur}"
    editeur_nom_complet = f"{prenom_editeur} {nom_editeur}"
    titre_nettoye = nettoyer_identifiant(titre_piece)
    nom_court = f"{titre_nettoye}_A{numero_acte}_S{numero_scene}of{nombre_scenes}"
    fenetre.title(f"Ekdosis-TEI Studio – {nom_court}")

    ligne_personnages = " ".join(f"##{nom.strip()}##" for nom in noms_persos.split(",") if nom.strip())

    zone_saisie.insert("1.0",
                       f"####{numero_acte}####\n\n"
                       f"###{numero_scene}###\n\n"
                       f"{ligne_personnages}\n\n"
                       )

    temoins_collectes = collecter_temoins(nombre_temoins_predefini)

    sauvegarder_configuration(infos, temoins_collectes)

    demander_mode_saisie_post_initialisation()


def demander_mode_saisie_post_initialisation():
    fenetre_mode = tk.Toplevel()
    fenetre_mode.title("Mode de saisie")
    fenetre_mode.configure(bg="#fdf6e3")
    fenetre_mode.geometry("400x220")
    fenetre_mode.resizable(False, False)
    fenetre_mode.grab_set()

    cadre = tk.Frame(fenetre_mode, bg="#fdf6e3", bd=3, relief=tk.GROOVE)
    cadre.pack(expand=True, fill="both", padx=20, pady=20)

    label = tk.Label(
        cadre,
        text="Souhaitez-vous activer la saisie assistée ?",
        bg="#fdf6e3",
        fg="#4b3f2f",
        font=("Garamond", 14, "bold"),
        wraplength=360,
        justify="center"
    )
    label.pack(pady=(10, 20))

    bouton_assistee = tk.Button(
        cadre,
        text="Oui, saisie assistée",
        font=("Garamond", 12),
        bg="#e0d8b0",
        fg="black",
        relief=tk.RAISED,
        command=lambda: [fenetre_mode.destroy(), ouvrir_saisie_locuteur()]
    )
    bouton_assistee.pack(pady=5)

    bouton_libre = tk.Button(
        cadre,
        text="Non, rester en mode libre",
        font=("Garamond", 12),
        bg="#ddd4aa",
        fg="black",
        relief=tk.RAISED,
        command=fenetre_mode.destroy
    )
    bouton_libre.pack(pady=5)

    bouton_annuler = tk.Button(
        cadre,
        text="Annuler",
        font=("Garamond", 11),
        bg="#cbbf9b",
        fg="black",
        command=fenetre_mode.destroy
    )
    bouton_annuler.pack(pady=(10, 5))


# A SUPPRIMER
# def demander_infos_initiales():
#    global titre_piece, numero_acte, numero_scene, nombre_scenes
#
#    titre_piece = simpledialog.askstring("Titre de la pièce", "Entrez le titre de la pièce :")
#    numero_acte = simpledialog.askstring("Numéro de l'acte", "Entrez le numéro de l'acte (ex: 1) :")
#    numero_scene = simpledialog.askstring("Numéro de la scène", "Entrez le numéro de la scène (ex: 1) :")
#    nombre_scenes = simpledialog.askstring("Nombre total de scènes dans l'acte","Entrez le nombre total de scènes dans l'acte :")
#
#    if not all([titre_piece, numero_acte, numero_scene, nombre_scenes]):
#        messagebox.showerror(
#            "Erreur",
#            "Toutes les informations sont obligatoires."
#            )
#        fenetre.destroy()

def demander_un_temoin_parchemin(numero):
    fenetre = tk.Toplevel()
    fenetre.title(f"Témoin {numero + 1}")
    fenetre.configure(bg="#f5f0dc")

    style = ttk.Style()
    style.configure("TLabel", background="#f5f0dc", font=("Garamond", 12))
    style.configure("TEntry", font=("Garamond", 12))
    style.configure("TButton", font=("Garamond", 12, "bold"))

    # Centrage
    fenetre.update_idletasks()
    largeur_fenetre = fenetre.winfo_width()
    hauteur_fenetre = fenetre.winfo_height()
    largeur_ecran = fenetre.winfo_screenwidth()
    hauteur_ecran = fenetre.winfo_screenheight()
    position_x = (largeur_ecran // 2) - (largeur_fenetre // 2)
    position_y = (hauteur_ecran // 2) - (hauteur_fenetre // 2)
    fenetre.geometry(f"+{position_x}+{position_y}")

    # Texte explicatif
    explication = tk.Label(fenetre, text=f"Définition de l'apparat pour export.\n"
                                         f"Donnez les caractéristiques du témoin numéro {numero + 1}",
                           justify="center", font=("Garamond", 11), padx=10, pady=10)
    explication.pack()
    ###
    tk.Label(fenetre, text="Abréviation :", bg="#f5f0dc", font=("Garamond", 12)).pack(padx=10, pady=(10, 0))
    entry_abbr = ttk.Entry(fenetre, width=40)
    entry_abbr.pack(padx=10, pady=5)
    entry_abbr.focus_set()

    tk.Label(fenetre, text="Année :", bg="#f5f0dc", font=("Garamond", 12)).pack(padx=10, pady=(10, 0))
    entry_year = ttk.Entry(fenetre, width=40)
    entry_year.pack(padx=10, pady=5)

    tk.Label(fenetre, text="Description :", bg="#f5f0dc", font=("Garamond", 12)).pack(padx=10, pady=(10, 0))
    entry_desc = ttk.Entry(fenetre, width=40)
    entry_desc.pack(padx=10, pady=5)

    result = {}

    def valider():
        abbr = entry_abbr.get().strip()
        year = entry_year.get().strip()
        desc = entry_desc.get().strip()
        if abbr and year and desc:
            result["abbr"] = abbr
            result["year"] = year
            result["desc"] = desc
            fenetre.destroy()

    fenetre.bind('<Return>', lambda event: valider())

    bouton = ttk.Button(fenetre, text="Valider", command=valider)
    bouton.pack(pady=15)

    fenetre.grab_set()
    fenetre.wait_window()

    return result if result else None


def collecter_temoins(nb_temoins):
    temoins = []
    for i in range(nb_temoins):
        donnees = demander_un_temoin_parchemin(i)
        if not donnees:
            return None  # ou [] si tu veux juste ignorer
        temoins.append(donnees)
    return temoins


def nom_fichier(base, extension):
    try:
        titre_nettoye = nettoyer_identifiant(titre_piece)
        return f"{titre_nettoye}_A{numero_acte}_S{numero_scene}_of{nombre_scenes}_{base}.{extension}"
    except NameError:
        # Variables non encore définies : nom provisoire
        return f"temp_{base}.{extension}"


def sauvegarder_configuration(infos, temoins_collectes):
    if not infos or not temoins_collectes:
        messagebox.showerror("Erreur", "Impossible de sauvegarder : informations incomplètes.")
        return

    config = infos.copy()  # Copie des infos de base
    config["Temoins"] = temoins_collectes  # Ajout des témoins

    titre_nettoye = nettoyer_identifiant(infos["Titre de la pièce"])
    nom_fichier = f"{titre_nettoye}_config.json"

    chemin_fichier = os.path.join(os.getcwd(), nom_fichier)

    try:
        with open(chemin_fichier, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("Sauvegarde", f"Configuration sauvegardée dans {nom_fichier}.")
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {e}")


def sauvegarder_config(chemin_fichier):
    global prenom_auteur, nom_auteur, titre_piece, numero_acte, numero_scene
    global nombre_scenes, vers_num, noms_persos
    global nombre_temoins_predefini, nom_editeur, prenom_editeur
    global temoins_collectes

    if os.path.exists(chemin_fichier):
        reponse = messagebox.askyesno(
            "Fichier existant",
            f"Le fichier '{os.path.basename(chemin_fichier)}' existe déjà.\n\nVoulez-vous l'écraser ?"
        )
        if not reponse:
            return  # utilisateur refuse → on annule

    config = {
        "Prénom de l'auteur": prenom_auteur,
        "Nom de l'auteur": nom_auteur,
        "Titre de la pièce": titre_piece,
        "Numéro de l'acte": numero_acte,
        "Numéro de la scène": numero_scene,
        "Nombre de scènes dans l'acte": nombre_scenes,
        "Numéro du vers de départ": vers_num,
        "Noms des personnages (séparés par virgule)": noms_persos,
        "Nombre de témoins": nombre_temoins_predefini,
        "Nom de l'éditeur (vous)": nom_editeur,
        "Prénom de l'éditeur": prenom_editeur,
        "Temoins": temoins_collectes
    }

    try:
        with open(chemin_fichier, "w", encoding="utf-8") as f:
            json.dump(config, indent=4, ensure_ascii=False)
        messagebox.showinfo("Succès", "Configuration sauvegardée avec succès.")
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {e}")


def sauvegarder_config_sous():
    global prenom_auteur, nom_auteur, titre_piece, numero_acte, numero_scene
    global nombre_scenes, vers_num, noms_persos
    global nombre_temoins_predefini, nom_editeur, prenom_editeur
    global temoins_collectes, nom_court, titre_nettoye

    titre_nettoye = nettoyer_identifiant(titre_piece)
    nom_court = f"{titre_nettoye}_A{numero_acte}_S{numero_scene}of{nombre_scenes}"

    if nom_court:
        fichier_defaut = nom_court + "_config.json"
    else:
        fichier_defaut = "nouveau_config.json"

    fichier = filedialog.asksaveasfilename(
        title="Enregistrer la configuration sous...",
        initialfile=fichier_defaut,
        defaultextension=".json",
        filetypes=[("Fichiers JSON", "*.json")]
    )
    if not fichier:
        return
    # vérifier si le fichier existe déjà ===
    if os.path.exists(fichier):
        reponse = messagebox.askyesno(
            "Fichier existant",
            f"Le fichier '{os.path.basename(fichier)}' existe déjà.\n\nVoulez-vous l'écraser ?"
        )
        if not reponse:
            return  # L'utilisateur refuse → on annule la sauvegarde

    config = {
        "Prénom de l'auteur": prenom_auteur,
        "Nom de l'auteur": nom_auteur,
        "Titre de la pièce": titre_piece,
        "Numéro de l'acte": numero_acte,
        "Numéro de la scène": numero_scene,
        "Nombre de scènes dans l'acte": nombre_scenes,
        "Numéro du vers de départ": vers_num,
        "Noms des personnages (séparés par virgule)": noms_persos,
        "Nombre de témoins": nombre_temoins_predefini,
        "Nom de l'éditeur (vous)": nom_editeur,
        "Prénom de l'éditeur": prenom_editeur,
        "Temoins": temoins_collectes
    }

    try:
        with open(fichier, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("Succès", "Configuration sauvegardée avec succès.")
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {e}")


def charger_configuration():
    global prenom_auteur, nom_auteur, auteur_nom_complet, titre_piece, numero_acte
    global numero_scene, nombre_scenes, nombre_temoins, nombre_temoins_predefini
    global nom_editeur, prenom_editeur, editeur_nom_complet, noms_persos
    global vers_num, numero_vers, temoins_collectes
    global config_en_cours

    chemin_fichier = filedialog.askopenfilename(
        title="Charger une configuration",
        filetypes=[("Fichiers JSON", "*.json")]
    )

    if not chemin_fichier:
        return  # L'utilisateur a annulé

    try:
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur de chargement : {e}")
        return

    # Mise à jour des variables globales
    prenom_auteur = config["Prénom de l'auteur"]
    nom_auteur = config["Nom de l'auteur"]
    titre_piece = config["Titre de la pièce"]
    numero_acte = config["Numéro de l'acte"]
    numero_scene = config["Numéro de la scène"]
    nombre_scenes = config["Nombre de scènes dans l'acte"]
    vers_num = int(config["Numéro du vers de départ"])
    entree_vers.delete(0, tk.END)
    entree_vers.insert(0, str(vers_num))
    numero_vers = vers_num
    noms_persos = config["Noms des personnages (séparés par virgule)"]
    nombre_temoins = config["Nombre de témoins"]
    nombre_temoins_predefini = int(nombre_temoins)
    nom_editeur = config["Nom de l'éditeur (vous)"]
    prenom_editeur = config["Prénom de l'éditeur"]

    auteur_nom_complet = f"{prenom_auteur} {nom_auteur}"
    editeur_nom_complet = f"{prenom_editeur} {nom_editeur}"

    temoins_collectes = config.get("Temoins", [])

    config_en_cours = config.copy()

    editer_config_apres_chargement(config)

    messagebox.showinfo("Chargement réussi", f"Configuration '{os.path.basename(chemin_fichier)}' chargée avec succès.")


def editer_config_courant():
    if not config_en_cours:
        messagebox.showwarning("Avertissement", "Aucune configuration chargée ou créée.")
        return
    editer_config_apres_chargement(config_en_cours)


def editer_config_apres_chargement(config):
    global prenom_auteur, nom_auteur, titre_piece, numero_acte, numero_scene
    global nombre_scenes, vers_num, numero_vers, noms_persos
    global nombre_temoins, nombre_temoins_predefini
    global nom_editeur, prenom_editeur, auteur_nom_complet, editeur_nom_complet
    global temoins_collectes
    global config_en_cours

    fenetre = tk.Toplevel()
    fenetre.title("Éditer la configuration")
    fenetre.configure(bg="#f5f0dc")

    champs = {
        "Prénom de l'auteur": config.get("Prénom de l'auteur", ""),
        "Nom de l'auteur": config.get("Nom de l'auteur", ""),
        "Titre de la pièce": config.get("Titre de la pièce", ""),
        "Numéro de l'acte": config.get("Numéro de l'acte", ""),
        "Numéro de la scène": config.get("Numéro de la scène", ""),
        "Nombre de scènes dans l'acte": config.get("Nombre de scènes dans l'acte", ""),
        "Numéro du vers de départ": config.get("Numéro du vers de départ", ""),
        "Noms des personnages (séparés par virgule)": config.get("Noms des personnages (séparés par virgule)", ""),
        "Nombre de témoins": config.get("Nombre de témoins", ""),
        "Nom de l'éditeur (vous)": config.get("Nom de l'éditeur (vous)", ""),
        "Prénom de l'éditeur": config.get("Prénom de l'éditeur", "")
    }

    entrees = {}
    for i, (label, valeur) in enumerate(champs.items()):
        tk.Label(fenetre, text=label, bg="#f5f0dc", font=("Garamond", 12)).grid(row=i, column=0, sticky="e", pady=5,
                                                                                padx=5)
        entree = tk.Entry(fenetre, font=("Garamond", 12), width=40)
        entree.insert(0, valeur)
        entree.grid(row=i, column=1, pady=5, padx=5)
        entrees[label] = entree

    # Récupérer les témoins déjà présents
    temoins_initiaux = config.get("Temoins", [])
    temoins_collectes_temp = []

    temoins_initiaux = config.get("Temoins", [])

    cadre_temoins = tk.LabelFrame(fenetre, text="Témoins", bg="#f5f0dc", font=("Garamond", 12, "bold"))
    cadre_temoins.grid(row=len(champs), column=0, columnspan=2, pady=15, padx=10, sticky="ew")

    entrees_temoins = []

    for temoin in temoins_initiaux:
        frame = tk.Frame(cadre_temoins, bg="#f5f0dc")
        frame.pack(fill="x", padx=5, pady=2)

        entry_abbr = tk.Entry(frame, font=("Garamond", 11), width=10)
        entry_abbr.insert(0, temoin.get("abbr", ""))
        entry_abbr.pack(side="left", padx=(0, 5))

        entry_year = tk.Entry(frame, font=("Garamond", 11), width=10)
        entry_year.insert(0, temoin.get("year", ""))
        entry_year.pack(side="left", padx=(0, 5))

        entry_desc = tk.Entry(frame, font=("Garamond", 11), width=40)
        entry_desc.insert(0, temoin.get("desc", ""))
        entry_desc.pack(side="left", padx=(0, 5))

        entrees_temoins.append((entry_abbr, entry_year, entry_desc))

        # === Fonction de validation ===

    def valider_modifications():
        nonlocal temoins_collectes_temp

        nouveau_config = {label: entree.get() for label, entree in entrees.items()}

        prenom_auteur = nouveau_config["Prénom de l'auteur"]
        nom_auteur = nouveau_config["Nom de l'auteur"]
        titre_piece = nouveau_config["Titre de la pièce"]
        numero_acte = nouveau_config["Numéro de l'acte"]
        numero_scene = nouveau_config["Numéro de la scène"]
        nombre_scenes = nouveau_config["Nombre de scènes dans l'acte"]
        vers_num = int(nouveau_config["Numéro du vers de départ"])
        numero_vers = vers_num
        noms_persos = nouveau_config["Noms des personnages (séparés par virgule)"]
        nombre_temoins = nouveau_config["Nombre de témoins"]
        nombre_temoins_predefini = int(nombre_temoins)
        nom_editeur = nouveau_config["Nom de l'éditeur (vous)"]
        prenom_editeur = nouveau_config["Prénom de l'éditeur"]

        auteur_nom_complet = f"{prenom_auteur} {nom_auteur}"
        editeur_nom_complet = f"{prenom_editeur} {nom_editeur}"

        # === Zone de texte regénérée - à SUPPRIMER ! Ne pas tout effacer!!
        # zone_saisie.delete("1.0", tk.END)
        # ligne_personnages = " ".join(f"##{nom.strip()}##" for nom in noms_persos.split(",") if nom.strip())
        # zone_saisie.insert("1.0",
        #                   f"####{numero_acte}####\n\n"
        #                   f"###{numero_scene}###\n\n"
        #                   f"{ligne_personnages}\n\n"
        #                   )
        #
        titre_nettoye = nettoyer_identifiant(titre_piece)
        nom_court = f"{titre_nettoye}_A{numero_acte}_S{numero_scene}of{nombre_scenes}"
        fenetre.title(f"Ekdosis-TEI Studio – {nom_court}")

        # === Ici, on reconstruit la liste des témoins à partir des entrées
        temoins_collectes_temp = []
        for entry_abbr, entry_year, entry_desc in entrees_temoins:
            abbr = entry_abbr.get().strip()
            year = entry_year.get().strip()
            desc = entry_desc.get().strip()
            if abbr and year and desc:
                temoins_collectes_temp.append({"abbr": abbr, "year": year, "desc": desc})

        if len(temoins_collectes_temp) != nombre_temoins_predefini:
            reponse = messagebox.askyesno(
                "Nombre de témoins différent",
                f"Vous avez saisi {len(temoins_collectes_temp)} témoins, mais {nombre_temoins_predefini} sont attendus.\n\nVoulez-vous resaisir les témoins maintenant ?"
            )
            if reponse:
                temoins_collectes_temp = collecter_temoins(nombre_temoins_predefini)

        # On affecte à la vraie variable globale
        temoins_collectes.clear()
        temoins_collectes.extend(temoins_collectes_temp)
        config_en_cours.update({
            "Prénom de l'auteur": prenom_auteur,
            "Nom de l'auteur": nom_auteur,
            "Titre de la pièce": titre_piece,
            "Numéro de l'acte": numero_acte,
            "Numéro de la scène": numero_scene,
            "Nombre de scènes dans l'acte": nombre_scenes,
            "Numéro du vers de départ": vers_num,
            "Noms des personnages (séparés par virgule)": noms_persos,
            "Nombre de témoins": nombre_temoins,
            "Nom de l'éditeur (vous)": nom_editeur,
            "Prénom de l'éditeur": prenom_editeur,
            "Temoins": temoins_collectes
        })

        globals()["prenom_auteur"] = prenom_auteur
        globals()["nom_auteur"] = nom_auteur
        globals()["titre_piece"] = titre_piece
        globals()["numero_acte"] = numero_acte
        globals()["numero_scene"] = numero_scene
        globals()["nombre_scenes"] = nombre_scenes
        globals()["vers_num"] = vers_num
        globals()["numero_vers"] = numero_vers
        globals()["noms_persos"] = noms_persos
        globals()["nombre_temoins"] = nombre_temoins
        globals()["nombre_temoins_predefini"] = nombre_temoins_predefini
        globals()["nom_editeur"] = nom_editeur
        globals()["prenom_editeur"] = prenom_editeur
        globals()["auteur_nom_complet"] = auteur_nom_complet
        globals()["editeur_nom_complet"] = editeur_nom_complet
        globals()["temoins_collectes"] = temoins_collectes

        fenetre.destroy()

    bouton_valider = tk.Button(fenetre, text="Valider", font=("Garamond", 12, "bold"), command=valider_modifications)
    bouton_valider.grid(row=len(champs) + 1, column=0, columnspan=2, pady=15)
    fenetre.bind("<Return>", lambda event: valider_modifications())

    fenetre.grab_set()
    fenetre.wait_window()


def charger_texte_zone_saisie():
    chemin_fichier = filedialog.askopenfilename(
        title="Charger un texte saisi",
        filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
    )

    if not chemin_fichier:
        return  # L'utilisateur a annulé

    try:
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            contenu = f.read()

        zone_saisie.delete("1.0", tk.END)
        zone_saisie.insert("1.0", contenu)

        # ➔ Nouveau traitement du nom de base
        nom_fichier_base = os.path.splitext(os.path.basename(chemin_fichier))[0]

        # Enlever la fin _saisie si présente
        if nom_fichier_base.endswith("_saisie"):
            nom_fichier_base_sans_saisie = nom_fichier_base[:-7]  # on enlève "_saisie"
        else:
            nom_fichier_base_sans_saisie = nom_fichier_base

        # Corriger le format _of6 ➔ of6
        nom_fichier_config_base = nom_fichier_base_sans_saisie.replace("_of", "of")

        # Construire le chemin du fichier de config
        dossier_base = os.path.dirname(chemin_fichier)
        chemin_config = os.path.join(dossier_base, nom_fichier_config_base + "_config.json")

        # Message de confirmation
        messagebox.showinfo("Chargement réussi", f"Le texte '{os.path.basename(chemin_fichier)}' a été chargé.")

        # Vérifier la config associée
        if not os.path.exists(chemin_config):
            # on cherche dans le dossier frère (remonter d’un niveau puis descendre)
            sibling = os.path.normpath(
                os.path.join(
                    os.path.dirname(chemin_config),  # dossier actuel
                    os.pardir,  # ../
                    "<nom_du_dossier_frere>",  # remplacer par le nom du dossier cible
                    os.path.basename(chemin_config)  # même fichier
                )
            )
            if os.path.exists(sibling):
                chemin_config = sibling
            else:
                messagebox.showwarning(
                    "Configuration absente",
                    f"Aucun fichier de configuration '{nom_fichier_config_base}_config.json' trouvé.\n\n"
                    f"Recherché ici :\n"
                    f" • {chemin_config}\n"
                    f" • {sibling}"
                )
                return


    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors du chargement du texte : {e}")


def normaliser_bloc(bloc):
    return "\n".join([l for l in bloc.strip().splitlines() if l.strip()])

def valider_structure_amelioree():
    texte = zone_saisie.get("1.0", "end-1c")
    lignes = texte.split("\n")
    zone_saisie.tag_remove("erreur", "1.0", tk.END)
    zone_saisie.tag_remove("valide", "1.0", tk.END)

    erreurs = []
    blocs_valides = 0
    a_scene = False
    locuteur_en_cours = None
    ligne_locuteur = None

    zone_saisie.tag_config("erreur", background="misty rose")
    zone_saisie.tag_config("valide", background="pale green")

    i = 0
    while i < len(lignes):
        ligne = lignes[i].strip()
        ligne_num = i + 1

        if ligne.count("#") % 2 != 0:
            erreurs.append(f"Ligne {ligne_num} : nombre impair de dièses.")
        if ligne.count("*") % 2 != 0:
            erreurs.append(f"Ligne {ligne_num} : nombre impair d'astérisques.")

        # Balise acte = autorisé, mais pas obligatoire, donc on saute sans rien imposer
        if re.fullmatch(r"####.*####", ligne):
            a_scene = False
            i += 1
            continue

        if re.fullmatch(r"###.*###", ligne):
            a_scene = True
            i += 1
            continue

        if re.fullmatch(r"(##[^\#]+##\s*)+", ligne):
            if not a_scene:
                erreurs.append(f"Ligne {ligne_num} : personnages présents hors d'une scène.")
            j = i + 1
            locuteur_trouvé = False
            while j < len(lignes):
                ligne_suiv = lignes[j].strip()
                if re.fullmatch(r"####.*####", ligne_suiv) or re.fullmatch(r"###.*###", ligne_suiv):
                    break
                if re.fullmatch(r"#[^#]+#", ligne_suiv):
                    locuteur_trouvé = True
                    break
                j += 1
            if not locuteur_trouvé:
                erreurs.append(f"Ligne {ligne_num} : aucun locuteur (#Nom#) trouvé après les personnages.")
            i += 1
            continue

        if re.fullmatch(r"#[^#]+#", ligne):
            if not a_scene:
                erreurs.append(f"Ligne {ligne_num} : locuteur défini hors d'une scène.")
            if re.fullmatch(r"#[^#]+#", ligne):
                if not a_scene:
                    erreurs.append(f"Ligne {ligne_num} : locuteur défini hors d'une scène.")
                if locuteur_en_cours:
                    erreurs.append(f"Ligne {ligne_locuteur} : locuteur '{locuteur_en_cours}' sans contenu.")
                locuteur_en_cours = ligne[1:-1].strip()
                ligne_locuteur = ligne_num

        j = i + 1
        while j < len(lignes):
            variantes = 0
            lignes_bloc = []
            indices_bloc = []
            while j < len(lignes):
                l = lignes[j].strip()
                if (not l or
                        re.fullmatch(r"#[^#]+#", l) or
                        re.fullmatch(r"###.*###", l) or
                        re.fullmatch(r"####.*####", l) or
                        re.fullmatch(r"(##[^\#]+##\s*)+", l)):
                    break
                variantes += 1
                lignes_bloc.append(l)
                indices_bloc.append(j)
                j += 1
                if variantes == nombre_temoins_predefini:
                    # Ajout du contrôle sur le nombre de mots (hors lignes #####)
                    lignes_bloc_a_tester = [ligne for ligne in lignes_bloc if not ligne.startswith("#####")]
                    if lignes_bloc_a_tester:  # Évite les blocs qui ne contiennent QUE des ##### !
                        nb_mots = [len(ligne.split()) for ligne in lignes_bloc_a_tester]
                        if len(set(nb_mots)) > 1:
                            erreur_msg = (
                                f"Lignes {indices_bloc[0] + 1}-{indices_bloc[-1] + 1} : variantes de longueur inégale ({nb_mots}) pour '{locuteur_en_cours}'."
                            )
                            erreurs.append(erreur_msg)
                            # Couleur jaune sur toutes les lignes du bloc
                            zone_saisie.tag_configure("desaligne", background="#fff2cc")
                            for idx in indices_bloc:
                                debut = f"{idx + 1}.0"
                                fin = f"{idx + 1}.end"
                                zone_saisie.tag_add("desaligne", debut, fin)
                    blocs_valides += 1
                    debut = f"{j - variantes}.0"
                    fin = f"{j}.end"
                    zone_saisie.tag_add("valide", debut, fin)
                    variantes = 0
                    lignes_bloc = []
                    indices_bloc = []
                    break
            if variantes != 0:
                erreurs.append(
                    f"Ligne {ligne_num} : {variantes} variante(s) incomplètes pour '{locuteur_en_cours}', {nombre_temoins_predefini} attendue(s)."
                )
            break

        locuteur_en_cours = None
        i = j
        continue

        if ligne:
            if locuteur_en_cours:
                erreurs.append(f"Ligne {ligne_num} : vers trouvé sans locuteur déclaré.")
            i += 1
            continue

        i += 1

    # Tests globaux de structure : scène et locuteur seulement !
    if not any(re.fullmatch(r"###.*###", l.strip()) for l in lignes):
        erreurs.append("Aucune scène (###...###) n’est définie.")
    if not any(re.fullmatch(r"#[^#]+#", l.strip()) for l in lignes):
        erreurs.append("Aucun locuteur (#Nom#) n’est défini.")

    # Coloration/surlignement et messages d'erreur : inchangés
    zone_saisie.tag_remove("erreur", "1.0", tk.END)
    zone_saisie.tag_remove("valide", "1.0", tk.END)

    if erreurs:
        zone_saisie.tag_configure("erreur", background="#ffb3b3")
        premiere_erreur_ligne = None

        for err in erreurs:
            if "Ligne" in err:
                match = re.search(r"Ligne (\d+)", err)
                if match:
                    ligne_erronnee = int(match.group(1))
                    debut = f"{ligne_erronnee}.0"
                    fin = f"{ligne_erronnee}.end"
                    zone_saisie.tag_add("erreur", debut, fin)
                    if premiere_erreur_ligne is None:
                        premiere_erreur_ligne = ligne_erronnee

        reponse = messagebox.askyesno(
            "Erreurs détectées",
            f"{len(erreurs)} erreurs détectées.\nVoulez-vous voir la liste détaillée ?"
        )
        if reponse:
            messagebox.showerror("Détail des erreurs", "\n".join(erreurs))

        if premiere_erreur_ligne:
            zone_saisie.see(f"{premiere_erreur_ligne}.0")

        return False
    else:
        messagebox.showinfo(
            "Validation réussie",
            f"Structure valide.\nNombre de blocs de variantes valides : {blocs_valides}"
        )
        return True

# Remplacement automatique
valider_structure = valider_structure_amelioree

# Fonction ci-dessous à débugger...
def valider_tei_bien_forme(tei_text):
    try:
        LET.fromstring(tei_text.encode('utf-8'))
        messagebox.showinfo("Validation TEI", "Le document TEI est bien formé (XML valide)!")
    except Exception as e:
        messagebox.showerror("Erreur TEI", f"Erreur XML: {e}")



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


def echapper_caracteres_ekdosis(texte):
    # Remplace & par \&,
    # et ~, ~~... par des espacements LaTeX adaptés :
    # ~   → ~ (espace insécable LaTeX)
    # ~~  → \enspace
    # ~~~ → \quad
    #~~~~ → \qquad
    # >4  → \hspace*{Nx1em}
    #
    texte = texte.replace("&", r"\&")
    # Remplace les séries de ~ par l’espace adapté
    def replace_tildes(match):
        n = len(match.group(0))
        if n == 1:
            return "~"
        elif n == 2:
            return r"\enspace"
        elif n == 3:
            return r"\quad"
        elif n == 4:
            return r"\qquad"
        else:
            return r"\hspace*{" + str(n) + "em}"
    return re.sub(r'~+', replace_tildes, texte)


def encoder_caracteres_tei(texte):
    """
    Échappe & (hors entités), et remplace ~ par &#160;.
    """
    # Évite les doubles échappements : échappe & seulement si ce n’est pas une entité
    texte = re.sub(r'&(?!#?\w+;)', '&amp;', texte)

    # Remplace les ~ successifs par des espaces insécables
    return re.sub(r'~+', lambda m: "&#160;" * len(m.group(0)), texte)



def rechercher(zone):
    terme = simpledialog.askstring("Rechercher", "Mot ou expression à chercher :")
    if terme:
        zone.tag_remove("found", "1.0", tk.END)
        start_pos = zone.index(tk.INSERT)
        found_any = False
        # Option insensible à la casse avec nocase=1
        while True:
            start_pos = zone.search(terme, start_pos, stopindex=tk.END, nocase=1)
            if not start_pos:
                break
            end_pos = f"{start_pos}+{len(terme)}c"
            zone.tag_add("found", start_pos, end_pos)
            if not found_any:
                # Scroll to first found occurrence
                zone.see(start_pos)
                # Facultatif : sélectionne aussi la première occurrence
                zone.tag_remove(tk.SEL, "1.0", tk.END)
                zone.tag_add(tk.SEL, start_pos, end_pos)
                zone.focus()
                found_any = True
            start_pos = end_pos
        zone.tag_config("found", background="yellow")

def remplacer_avance(zone):
    terme = simpledialog.askstring("Remplacer", "Mot à rechercher :")
    if not terme:
        return

    remplacement = simpledialog.askstring("Remplacer", f"Remplacer « {terme} » par :")
    if remplacement is None:
        return

    sensible_casse = messagebox.askyesno("Casse", "Faire la recherche en respectant la casse (majuscules/minuscules) ?")

    contenu = zone.get("1.0", tk.END)
    count = 0
    index = "1.0"

    while True:
        index = zone.search(terme, index, nocase=not sensible_casse, stopindex=tk.END)
        if not index:
            break

        fin_index = f"{index}+{len(terme)}c"
        zone.tag_add("remplacer", index, fin_index)
        zone.tag_config("remplacer", background="yellow")

        zone.see(index)
        zone.focus()

        confirmer = messagebox.askyesno("Remplacer ?",
                                        f"Remplacer cette occurrence de « {terme} » par « {remplacement} » ?")
        zone.tag_delete("remplacer")

        if confirmer:
            zone.delete(index, fin_index)
            zone.insert(index, remplacement)
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
    zone_resultat_ekdosis.configure(font=police_zone)

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
        if isinstance(widget, tk.Toplevel) and widget.title() == "Bienvenue dans Ekdosis-TEI Studio":
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
        zone_resultat_ekdosis.configure(bg="white", font=police_zone)
    except:
        pass


def confirmer_quitter():
    if messagebox.askokcancel("Quitter",
                              "Voulez-vous vraiment quitter ?\nLes modifications non sauvegardées seront perdues."):
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
        if os.path.exists(fichier):
            reponse = messagebox.askyesno(
                "Fichier existant",
                f"Le fichier '{os.path.basename(fichier)}' existe déjà.\n\nVoulez-vous l'écraser ?"
            )
            if not reponse:
                return
        with open(fichier, "w", encoding="utf-8") as f:
            f.write(contenu)
        messagebox.showinfo("Succès", f"Fichier TEI enregistré :\n{fichier}")


def exporter_ekdosis():
    global nombre_temoins_predefini
    contenu = zone_resultat_ekdosis.get("1.0", tk.END).strip()
    if not contenu:
        messagebox.showwarning("Avertissement", "Aucun contenu ekdosis à enregistrer.")
        return

    from tkinter.simpledialog import askinteger

    try:
        nb_temoins = int(nombre_temoins_predefini)
    except Exception:
        nb_temoins = askinteger(
            "Nombre de témoins manquant",
            "Le nombre de témoins est introuvable ou invalide.\nVeuillez l’entrer manuellement :",
            minvalue=1
        )
        if nb_temoins is None:
            messagebox.showinfo("Annulé", "Saisie annulée par l'utilisateur.")
            return
        else:
            nombre_temoins_predefini = str(nb_temoins)

    temoins = temoins_collectes
    if not temoins:
        messagebox.showwarning("Annulé",
                               "La collecte des témoins a été annulée.\n"
                               "Vous pouvez exporter toutefois le LaTeX sans le template\n"
                               "en copiant-collant le code généré ci-dessous\n"
                               "et en l'insérant dans le template fourni sur le dépôt"
                               )
        return

    if len(temoins) != nb_temoins:
        messagebox.showwarning(
            "Incohérence",
            f"Le nombre de témoins collectés ({len(temoins)}) ne correspond pas "
            f"au nombre attendu ({nb_temoins}). L'export sera à vérifier."
        )

    declarations_temoins = "\n".join([
        f"\\DeclareWitness{{{t['abbr']}}}{{{t['year']}}}{{{t['desc']}}}"
        for t in temoins
    ])

    titlepage_bloc = "\n".join([
        "\\begin{titlepage}",
        "    \\centering",
        f"    {{\\Huge \\textbf{{\\MakeUppercase{{{titre_piece}}}}} \\par}}",
        "    \\vspace{1.5cm}",
        f"    {{\\LARGE {auteur_nom_complet} \\par}}",
        "    \\vspace{2cm}",
        f"    {{\\Large \\textit{{Édition critique par {editeur_nom_complet}}} \\par}}",
        "    \\vspace{2cm}",
        "    {\\large \\today}",
        "    \\vfill",
        "\\end{titlepage}",
    ])

    contenu_complet = (
            template_ekdosis_preamble +
            declarations_temoins +
            template_ekdosis_debut_doc +
            "\n" +
            titlepage_bloc +
            contenu +
            "\n" +
            template_ekdosis_fin_doc
    )

    fichier = fd.asksaveasfilename(
        defaultextension=".tex",
        filetypes=[("Fichiers ekdosis", "*.tex")],
        initialfile=nom_fichier("ekdosis", "tex"),
        title="Enregistrer le fichier ekdosis"
    )

    if fichier:
        if os.path.exists(fichier):
            reponse = messagebox.askyesno(
                "Fichier existant",
                f"Le fichier '{os.path.basename(fichier)}' existe déjà.\n\nVoulez-vous l'écraser ?"
            )
            if not reponse:
                return
        with open(fichier, "w", encoding="utf-8") as f:
            f.write(contenu_complet)
        messagebox.showinfo("Succès", f"Fichier ekdosis enregistré :\n{fichier}")


def enregistrer_saisie():
    valider_structure()
    contenu = zone_saisie.get("1.0", tk.END).strip()
    if not contenu:
        messagebox.showwarning("Avertissement", "Aucune saisie à enregistrer.")
        return

    fichier_txt = fd.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Fichiers texte", "*.txt")],
        initialfile=nom_fichier("saisie", "txt"),
        title="Enregistrer la saisie"
    )

    if fichier_txt:
        # Chemin du fichier config associé
        fichier_config = fichier_txt.replace("_saisie.txt", "_config.json")

        # Vérification combinée
        if os.path.exists(fichier_txt) or os.path.exists(fichier_config):
            reponse = messagebox.askyesno(
                "Fichiers existants",
                "La saisie ou la configuration existe déjà.\nVoulez-vous écraser ?"
            )
            if not reponse:
                return

        # Sauvegarder la saisie
        with open(fichier_txt, "w", encoding="utf-8") as f:
            f.write(contenu)

        messagebox.showinfo("Succès", "Saisie enregistrée.")

import os
import tkinter as tk
from tkinter import filedialog as fd, messagebox

def enregistrer_preview(html_result):
    fichier_html = fd.asksaveasfilename(
        defaultextension=".html",
        filetypes=[("Fichiers HTML", "*.html")],
        initialfile=nom_fichier("preview", "html"),
        title="Enregistrer le preview HTML"
    )

    if fichier_html:
        if os.path.exists(fichier_html):
            reponse = messagebox.askyesno(
                "Fichier existant",
                f"Le fichier {os.path.basename(fichier_html)} existe déjà.\nVoulez-vous l’écraser ?"
            )
            if not reponse:
                return
        try:
            with open(fichier_html, "w", encoding="utf-8") as f:
                f.write(str(html_result))
            messagebox.showinfo("Succès", f"Preview HTML enregistré sous:\n{fichier_html}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d’enregistrer le fichier: {e}")

def enregistrer_triple():
    global html_result

    # Vérifier si html_result est défini dans l'espace global
    if "html_result" not in globals():
        messagebox.showwarning("Avertissement", "Aucun aperçu HTML à enregistrer. Lancez d'abord le 'Preview'.")
        return

    if html_result is None:
        messagebox.showwarning("Avertissement", "Aucun aperçu HTML à enregistrer. Lancez d'abord le 'Preview'.")
        return

    # S’il s’agit d’un widget Text
    if hasattr(html_result, "get"):
        html = html_result.get("1.0", tk.END).strip()
    else:
        html = str(html_result).strip()

    if not html:
        messagebox.showwarning("Avertissement", "Aucun aperçu HTML à enregistrer. Lancez d'abord le 'Preview'.")
        return

    # 1. Récupération des contenus
    raw = zone_saisie.get("1.0", tk.END).strip()
    tei = zone_resultat_tei.get("1.0", tk.END).strip()
    if hasattr(html_result, "get"):
        html = html_result.get("1.0", tk.END).strip()
    else:
        html = str(html_result).strip()
    ekdosis_body = zone_resultat_ekdosis.get("1.0", tk.END).strip()

    # 2. Vérifications d’existence de contenu
    if not raw:
        return messagebox.showwarning("Avertissement", "Aucune saisie à enregistrer.")
    if not tei:
        return messagebox.showwarning("Avertissement", "Aucun contenu TEI à enregistrer.")
    if not html:
        return messagebox.showwarning("Avertissement", "Aucun aperçu HTML à enregistrer.")
    if not ekdosis_body:
        return messagebox.showwarning("Avertissement", "Aucun contenu Ekdosis à enregistrer.")

    # 3. Choix du dossier racine
    root_dir = fd.askdirectory(title="Choisissez le dossier racine")
    if not root_dir:
        return

    # 4. Noms par défaut
    default_txt  = nom_fichier("saisie",  "txt")
    default_xml  = nom_fichier("tei",     "xml")
    default_html = nom_fichier("preview", "html")
    default_ekdosis = nom_fichier("ekdosis", "tex")

    # 5. Confirmation / modification des basenames
    txt_name  = simpledialog.askstring("Nom fichier texte", "Nom du fichier de transcription (.txt) :", initialvalue=default_txt)
    if txt_name is None: return

    xml_name  = simpledialog.askstring("Nom fichier TEI", "Nom du fichier TEI (.xml) :", initialvalue=default_xml)
    if xml_name is None: return

    html_name = simpledialog.askstring("Nom fichier HTML", "Nom du fichier HTML (.html) :", initialvalue=default_html)
    if html_name is None: return

    ekdosis_name = simpledialog.askstring("Nom fichier Ekdosis", "Nom du fichier Ekdosis (.tex) :", initialvalue=default_ekdosis)
    if ekdosis_name is None: return

    # 6. Construction des chemins et création des dossiers
    chemins = {
        "Saisie": os.path.join(root_dir, "transcriptions", txt_name),
        "TEI"   : os.path.join(root_dir, "xml-tei",      xml_name),
        "HTML"  : os.path.join(root_dir, "html", "fichiers-originaux", html_name),
        "Ekdosis": os.path.join(root_dir, "ekdosis", ekdosis_name),
    }
    for path in chemins.values():
        os.makedirs(os.path.dirname(path), exist_ok=True)

    # 7. Vérif. d’écrasement
    existants = [p for p in chemins.values() if os.path.exists(p)]
    if existants:
        liste = "\n".join(os.path.basename(p) for p in existants)
        if not messagebox.askyesno(
            "Fichiers existants",
            f"Les fichiers suivants existent déjà :\n\n{liste}\n\nVoulez-vous les écraser ?"
        ):
            return

    # 8. Construction de l’export Ekdosis AUTONOME (préambule, témoins, titlepage, contenu, fin)
    try:
        # --- A. Déclarations des témoins
        try:
            nb_temoins = int(nombre_temoins_predefini)
        except Exception:
            from tkinter.simpledialog import askinteger
            nb_temoins = askinteger(
                "Nombre de témoins manquant",
                "Le nombre de témoins est introuvable ou invalide.\nVeuillez l’entrer manuellement :",
                minvalue=1
            )
            if nb_temoins is None:
                messagebox.showinfo("Annulé", "Saisie annulée par l'utilisateur.")
                return
            else:
                nombre_temoins_predefini = str(nb_temoins)

        temoins = temoins_collectes if 'temoins_collectes' in globals() else []
        if not temoins:
            messagebox.showwarning("Annulé",
                                   "La collecte des témoins a été annulée.\n"
                                   "Vous pouvez exporter toutefois le LaTeX sans le template\n"
                                   "en copiant-collant le code généré ci-dessous\n"
                                   "et en l'insérant dans le template fourni sur le dépôt"
                                   )
            declarations_temoins = ""
        else:
            if len(temoins) != nb_temoins:
                messagebox.showwarning(
                    "Incohérence",
                    f"Le nombre de témoins collectés ({len(temoins)}) ne correspond pas "
                    f"au nombre attendu ({nb_temoins}). L'export sera à vérifier."
                )
            declarations_temoins = "\n".join([
                f"\\DeclareWitness{{{t['abbr']}}}{{{t['year']}}}{{{t['desc']}}}"
                for t in temoins
            ])

        # --- B. Bloc titlepage (avec fallback questions si variables manquantes)
        try:
            titre = titre_piece
        except Exception:
            titre = simpledialog.askstring("Titre", "Titre de la pièce :") or "Titre inconnu"
        try:
            auteur = auteur_nom_complet
        except Exception:
            auteur = simpledialog.askstring("Auteur", "Nom de l'auteur :") or "Auteur inconnu"
        try:
            editeur = editeur_nom_complet
        except Exception:
            editeur = simpledialog.askstring("Éditeur", "Nom de l'éditeur :") or "Éditeur inconnu"

        titlepage_bloc = "\n".join([
            "\\begin{titlepage}",
            "    \\centering",
            f"    {{\\Huge \\textbf{{\\MakeUppercase{{{titre}}}}} \\par}}",
            "    \\vspace{1.5cm}",
            f"    {{\\LARGE {auteur} \\par}}",
            "    \\vspace{2cm}",
            f"    {{\\Large \\textit{{Édition critique par {editeur}}} \\par}}",
            "    \\vspace{2cm}",
            "    {\\large \\today}",
            "    \\vfill",
            "\\end{titlepage}",
        ])

        # --- C. Préambule et balises (à adapter si globalement défini)
        preamble = (
            "\\documentclass{book}\n"
            "\\usepackage[main=french,spanish,latin]{babel}\n"
            "\\usepackage[T1]{fontenc}\n"
            "\\usepackage{fontspec}\n"
            "\\usepackage{csquotes}\n"
            "\\usepackage[teiexport, divs=ekdosis, poetry=verse]{ekdosis}\n"
            "\\usepackage{setspace}\n"
            "\\usepackage{lettrine}\n"
            "\\usepackage{hyperref}\n"
            "\\usepackage{zref-user,zref-abspage}\n"
            "% ... autres commandes utiles (optionnel)\n\n"
        )
        debut_doc = "\\begin{document}\n\\begin{ekdosis}\n"
        fin_doc = "\n\\end{ekdosis}\n\\end{document}\n"

        ekdosis_full = (
            preamble +
            declarations_temoins + "\n" +
            debut_doc +
            titlepage_bloc + "\n" +
            ekdosis_body + "\n" +
            fin_doc
        )

        # --- D. Écriture des fichiers
        with open(chemins["Saisie"], "w", encoding="utf-8") as f:
            f.write(raw)
        with open(chemins["TEI"], "w", encoding="utf-8") as f:
            f.write(tei)
        with open(chemins["HTML"], "w", encoding="utf-8") as f:
            f.write(html)
        with open(chemins["Ekdosis"], "w", encoding="utf-8") as f:
            f.write(ekdosis_full)
    except Exception as e:
        return messagebox.showerror("Erreur", f"Impossible d'enregistrer : {e}")

    # 9. Message de succès
    msg = "\n".join(f"{clé} → {chemin}" for clé, chemin in chemins.items())
    messagebox.showinfo("Succès", "Fichiers enregistrés :\n\n" + msg)


def nettoyer_html_unique():
    try:
        if not editeur_nom_complet:
            messagebox.showinfo("Configuration", "Chargez d'abord le fichier de configuration")
            return
    except NameError:
        messagebox.showinfo("Configuration", "Chargez d'abord le fichier de configuration")
        return

    filepath = filedialog.askopenfilename(
        title="Sélectionnez un fichier HTML à nettoyer",
        filetypes=[("Fichiers HTML", "*.html *.htm")]
    )
    if not filepath:
        return

    filename = os.path.basename(filepath)
    titre = filename.split('_')[0].capitalize()

    # Extrait "AI" = Acte I et scène
    match_acte = re.search(r'_A(\d+)', filename)
    acte = f"Acte {match_acte.group(1)}" if match_acte else "Acte ?"
    match_scene = re.search(r'_S([0-9]+)', filename)
    scene = f"scène {match_scene.group(1)}" if match_scene else ""

    def roman_to_int(roman):
        roman = roman.strip().upper().replace("ACTE", "").strip()
        roman_dict = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
            'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10
        }
        if roman.isdigit():
            return roman
        return str(roman_dict.get(roman, roman))

    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    except:
        locale.setlocale(locale.LC_TIME, "")
    today_str = french_date(date.today())

    # Calcul du nom de fichier XML (sans _preview)
    nom_fichier_html = os.path.basename(filepath)
    nom_base = os.path.splitext(nom_fichier_html)[0].replace("_preview", "")
    nom_fichier_xml = nom_base + "_tei.xml"
    chemin_vers_xml = f"../xml-tei/{nom_fichier_xml}"

    bloc_credit = f'''
    <div class="bloc-credit">
    <div class="credit-line">Jean Racine – <span class="italic">{titre}</span>, {acte}</div>
    <div class="credit-line">Édition critique par {editeur_nom_complet}</div>
    <div class="credit-line">Document généré le {today_str} depuis Ekdosis-TEI Studio</div>
    <div class="credit-line"><a href="{chemin_vers_xml}" download>Télécharger le XML</a></div>
    </div>
    '''

    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Suppression des balises <head>, <style>, <footer>, <html>, <body>
    if soup.head:
        soup.head.decompose()
    for tag in soup.find_all(['style', 'footer']):
        tag.decompose()
    for tag in soup.find_all(['html', 'body']):
        tag.unwrap()

    # Supprimer bloc-credit complet s’il existe
    bloc = soup.find('div', class_='bloc-credit')
    if bloc:
        bloc.decompose()

    # Supprimer toutes les lignes orphelines "credit-line"
    for tag in soup.find_all('div', class_='credit-line'):
        tag.decompose()

    html = str(soup)

    # --- Enrobage avec structure éditoriale ---
    header_html = '''<html lang="fr">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta charset="UTF-8">
<title>Édition TEI</title>
<link rel="stylesheet" href="../../../css/portail.css">
</head>
<body>
  <div id="container">
    <aside id="menu-lateral">Chargement du menu…</aside>
    <main>
      <div id="header"></div>
'''

    footer_html = '''
      <div id="footer"></div>
    </main>
  </div>
<script src="../../../js/header.js"></script>
<script src="../../../js/footer.js"></script>
<script src="../../../../js/menu-lateral.js"></script>
</body>
</html>
'''

    contenu_final = header_html + bloc_credit + "\n" + html.strip() + footer_html

    num_acte = roman_to_int(acte)

    # Nom du fichier sans "_preview" avant .html
    base_filename = os.path.basename(filepath)
    if "_preview" in base_filename:
        output_filename = base_filename.replace("_preview", "")
    else:
        output_filename = f"acte_{num_acte}.html"

    # Dossier parent
    parent_dir = os.path.dirname(os.path.dirname(filepath))
    save_path = os.path.join(parent_dir, output_filename)

    if not messagebox.askokcancel("Confirmation", f"Le fichier sera enregistré sous :\n{save_path}\n\nConfirmer ?"):
        return

    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(contenu_final)

    messagebox.showinfo("Succès", f"Fichier HTML nettoyé enregistré :\n{save_path}")

    chemin_vers_xml = f"../xml-tei/{nom_fichier_xml}"

    # Recherche du dernier <l n="..."> dans le fichier XML correspondant

    # Construction du chemin absolu vers le fichier XML
    xml_absolu = os.path.normpath(os.path.join(os.path.dirname(filepath), "..", "..", "xml-tei", nom_fichier_xml))

    dernier_num_vers = None

    # DEBUG
    print(f"📄 Nom du fichier XML attendu : {nom_fichier_xml}")
    print(f"🔍 Chemin absolu vers le fichier XML : {xml_absolu}")
    # DEBUG

    if os.path.exists(xml_absolu):
        print("✅ Fichier XML trouvé.")
        try:
            with open(xml_absolu, 'r', encoding='utf-8') as f:
                xml_content = f.read()

            soup_xml = BeautifulSoup(xml_content, 'xml')
            lignes = []

            for l in soup_xml.find_all('l'):
                n = l.get('n')
                if n:
                    n = n.strip()
                    try:
                        val = float(n)
                        lignes.append(val)
                        print(f"✅ <l n=\"{n}\"> accepté")
                    except ValueError:
                        print(f"❌ <l n=\"{n}\"> ignoré (non convertible en float)")

            print(f"📊 Numéros de vers extraits : {lignes}")
            if lignes:
                dernier_num_vers = max(lignes)
                print(f"📌 Dernier numéro trouvé : {dernier_num_vers}")

        except Exception as e:
            print("❌ Erreur lors de l'analyse du XML avec BeautifulSoup :", e)
    else:
        print("❌ Le fichier XML n'existe pas :", xml_absolu)

    if dernier_num_vers is not None:
        messagebox.showinfo("Dernier vers", f"Dernier vers numéroté : {dernier_num_vers}")

def fusionner_html():

    html_files = filedialog.askopenfilenames(
        title="Sélectionnez les fichiers HTML à fusionner",
        filetypes=[("Fichiers HTML", "*.html *.htm")]
    )
    if not html_files:
        return

    html_files = sorted(html_files, key=lambda x: os.path.basename(x).lower())
    titre = simpledialog.askstring("Titre", "Titre de la pièce (ex : La Thébaïde):")
    if not titre:
        return
    acte = simpledialog.askstring("Acte", "Numéro d'acte (ex : Acte I):")
    if not acte:
        return

    def roman_to_int(roman):
        roman = roman.strip().upper().replace("ACTE", "").strip()
        roman_dict = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
            'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10
        }
        if roman.isdigit():
            return roman
        return str(roman_dict.get(roman, roman))

    today_str = french_date(date.today())

    bloc_credit_perso = f'''
<div class="bloc-credit">
<div class="credit-line">Jean Racine – <span class="italic">{titre}</span>, acte {acte}</div>
<div class="credit-line">Édition critique par {editeur_nom_complet}</div>
<div class="credit-line">Document généré le {today_str} depuis Ekdosis-TEI Studio</div>
</div>
'''

    num_acte = roman_to_int(re.sub(r"Acte\s*", "", acte, flags=re.IGNORECASE))
    def_name = f"acte_{num_acte}.html"
    save_path = filedialog.asksaveasfilename(
        defaultextension=".html",
        filetypes=[("Fichiers HTML", "*.html")],
        initialfile=def_name,
        title="Enregistrer l'acte fusionné"
    )
    if not save_path:
        return

    merged = []

    for idx, filepath in enumerate(html_files):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        content = re.sub(r'<style.*?>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'</body>\s*</html>\s*$', '', content, flags=re.IGNORECASE)

        if idx == 0:
            parts = re.split(r'(<body[^>]*>)', content, maxsplit=1, flags=re.IGNORECASE | re.DOTALL)
            if len(parts) < 3:
                messagebox.showerror("Erreur", "Impossible de repérer le <body> dans le premier fichier.")
                return
            pre_body = parts[0] + parts[1]
            google_fonts_line = '<link href="https://fonts.googleapis.com/css2?family=Old+Standard+TT:wght@400;700&display=swap" rel="stylesheet">\n'
            pre_body = re.sub(r'(<head[^>]*>)', r'\1\n' + google_fonts_line, pre_body, count=1, flags=re.IGNORECASE)
            merged.append(pre_body)

            body_inside = parts[2]
            body_inside = re.sub(r'<link rel="stylesheet" href="../../../css/edition.css">', '', body_inside, flags=re.IGNORECASE)
            body_inside = '<link rel="stylesheet" href="../../../css/edition.css">\n' + body_inside
            lines = body_inside.splitlines()
            filtered = [line for line in lines if not (
                'bloc-credit' in line or 'logo-credit' in line or 'credit-line' in line
            )]
            merged.append(bloc_credit_perso + "\n" + "\n".join(filtered))
        else:
            content = re.sub(r'<\/?body[^>]*>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'<\/?html[^>]*>', '', content, flags=re.IGNORECASE)
            lines = content.splitlines()
            filtered = [line for line in lines if not (
                'bloc-credit' in line or 'logo-credit' in line or 'credit-line' in line
            )]
            merged.append("\n".join(filtered))

    merged.append("\n</body>\n</html>")
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write("".join(merged))

    messagebox.showinfo("Succès", f"Acte HTML fusionné enregistré :\n{save_path}")

def fusionner_markdown():
    import os
    from tkinter import filedialog, messagebox

    md_files = filedialog.askopenfilenames(
        title="Fichiers Markdown à fusionner",
        filetypes=[("Fichiers Markdown ou texte", "*.md *.txt")]
    )
    if not md_files:
        return

    md_files = sorted(md_files, key=lambda x: os.path.basename(x).lower())
    save_path = filedialog.asksaveasfilename(
        defaultextension=".md",
        filetypes=[("Fichiers Markdown", "*.md")],
        initialfile="fusion.md",
        title="Enregistrer le Markdown fusionné"
    )
    if not save_path:
        return

    merged = []
    for filepath in md_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            merged.append(f.read().strip())

    with open(save_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(merged))

    messagebox.showinfo("Succès", f"Fichier Markdown fusionné enregistré :\n{save_path}")

def fusionner_tei():
    import os, re
    from tkinter import filedialog, messagebox

    files = filedialog.askopenfilenames(
        title="Fichiers TEI à fusionner",
        filetypes=[("TEI XML", "*.xml")]
    )
    if not files:
        return

    files = sorted(files, key=lambda p: os.path.basename(p).lower())
    docs = []
    for path in files:
        try:
            with open(path, encoding="utf-8") as f:
                docs.append(f.read())
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire {path} :\n{e}")
            return

    body_open_re = re.compile(r'^(.*?<body[^>]*>)', re.DOTALL | re.IGNORECASE)
    body_close_re = re.compile(r'(</body>.*)$', re.DOTALL | re.IGNORECASE)
    body_content_re = re.compile(r'<body[^>]*>(.*?)</body>', re.DOTALL | re.IGNORECASE)

    first = docs[0]
    m_open = body_open_re.match(first)
    m_close = body_close_re.search(first)
    m_body = body_content_re.search(first)
    if not (m_open and m_close and m_body):
        messagebox.showerror("Erreur", "Le premier fichier ne contient pas de <body>…</body> valide.")
        return

    header = m_open.group(1)
    footer = m_close.group(1)
    bodies = [m_body.group(1)]

    for idx, doc in enumerate(docs[1:], start=2):
        m = body_content_re.search(doc)
        if not m:
            messagebox.showerror("Erreur", f"Fichier n°{idx} : pas de <body>…</body> trouvé.")
            return
        bodies.append(m.group(1))

    merged = header + "\n".join(bodies) + footer
    save_path = filedialog.asksaveasfilename(
        defaultextension=".xml",
        filetypes=[("TEI XML", "*.xml")],
        initialfile="acte_fusionne.xml",
        title="Enregistrer le TEI fusionné"
    )
    if not save_path:
        return

    try:
        with open(save_path, "w", encoding="utf-8") as out:
            out.write(merged)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d'écrire le fichier :\n{e}")
        return

    messagebox.showinfo("Succès", f"TEI fusionné enregistré :\n{save_path}")

def fusionner_ekdosis():
    import os
    import re
    from tkinter import filedialog, messagebox, simpledialog
    from datetime import date

    # 1. Sélection des fichiers
    files = filedialog.askopenfilenames(
        title="Fichiers Ekdosis à fusionner",
        filetypes=[("Fichiers LaTeX Ekdosis", "*.tex")]
    )
    if not files:
        return

    files = sorted(files, key=lambda p: os.path.basename(p).lower())

    # 2. Demande du titre et de l'acte
    titre = simpledialog.askstring("Titre", "Titre de la pièce (ex : La Thébaïde):")
    if not titre:
        return
    acte = simpledialog.askstring("Acte", "Numéro d'acte (ex : Acte I):")
    if not acte:
        return

    today_str = french_date(date.today())
    bloc_credit = (
        "%% ====================================\n"
        f"%% Racine – {titre}, acte {acte}\n"
        f"%% Édition critique par {editeur_nom_complet}\n"
        f"%% Document généré le {today_str} depuis Ekdosis-TEI Studio\n"
        "%% ====================================\n\n"
    )

    merged = [bloc_credit]
    n = len(files)

    for idx, path in enumerate(files):
        try:
            with open(path, encoding="utf-8") as f:
                doc = f.read()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire {path} :\n{e}")
            return

        # Supprimer la page de titre dans tous les fichiers sauf le premier
        if idx > 0:
            doc = re.sub(
                r'\\begin\{titlepage\}.*?\\end\{titlepage\}',
                '',
                doc,
                flags=re.DOTALL
            )

        # Premier fichier : on garde tout SAUF la fin (on retire \end{ekdosis} et \end{document})
        if idx == 0:
            doc = doc.lstrip()
            doc = re.sub(
                r'\\end\{ekdosis\}\s*\\end\{document\}\s*$',
                '',
                doc,
                flags=re.DOTALL
            )
            merged.append(doc)
        # Fichiers intermédiaires : on garde uniquement le corps
        elif idx < n - 1:
            # Supprimer tout avant \begin{ekdosis}
            doc = re.sub(r'(?s)^.*?\\begin\{ekdosis\}', '', doc)
            # Supprimer \end{ekdosis} et \end{document}
            doc = re.sub(
                r'\\end\{ekdosis\}\s*\\end\{document\}\s*$',
                '',
                doc,
                flags=re.DOTALL
            )
            merged.append(doc)
        # Dernier fichier : on garde tout après \begin{ekdosis}, et on garde la fin
        else:
            doc = re.sub(r'(?s)^.*?\\begin\{ekdosis\}', '', doc)
            merged.append(doc)

    # Nettoyage des retours à la ligne superflus
    fusion = '\n'.join(frag.strip('\n') for frag in merged)
    fusion = fusion.replace('{#####}', '')

    # 4. Boîte de dialogue pour sauvegarder le résultat
    save_path = filedialog.asksaveasfilename(
        defaultextension=".tex",
        filetypes=[("Fichiers LaTeX Ekdosis", "*.tex")],
        initialfile="fusion_ekdosis.tex",
        title="Enregistrer l'acte Ekdosis fusionné"
    )
    if not save_path:
        return

    try:
        with open(save_path, "w", encoding="utf-8") as out:
            out.write(fusion)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d'écrire le fichier :\n{e}")
        return

    messagebox.showinfo("Succès", f"Fichier Ekdosis fusionné enregistré :\n{save_path}")


def formatter_persname_ekdosis(noms):
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
    global auteur_nom_complet, editeur_nom_complet, titre_piece, numero_acte, numero_scene, html_result

    tei = zone_resultat_tei.get("1.0", tk.END).strip()
    if not tei:
        messagebox.showwarning("Avertissement", "Aucun contenu TEI à prévisualiser.")
        return

    temoins_dict = {}
    try:
        temoins_collectes_local = globals().get("temoins_collectes")
        if temoins_collectes_local:
            temoins_dict = {t["abbr"]: t["year"] for t in temoins_collectes_local}
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de la collecte des témoins :\n{e}")
        return

    try:
        parser = LET.XMLParser(remove_blank_text=True)
        tei_xml = LET.fromstring(tei.encode("utf-8"), parser)

        # Remplacer tous les @wit dans <rdg> et <lem>
        ns = {"tei": "http://www.tei-c.org/ns/1.0"}
        for node in tei_xml.xpath(".//tei:rdg | .//tei:lem", namespaces=ns):
            wit_attr = node.get("wit")
            if wit_attr:
                abbrs = [abbr.lstrip("#") for abbr in wit_attr.strip().split()]
                new_wits = [temoins_dict.get(abbr, abbr) for abbr in abbrs]
                node.set("wit", ", ".join(new_wits))  # <-- ici le patch élégant

        # Insertion facultative du bloc de métadonnées en tête de sortie
        # Mise en français pour la date avec fallback
        try:
            locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
        except:
            locale.setlocale(locale.LC_TIME, "")  # fallback silencieux

        # Insertion facultative du bloc de métadonnées en tête de sortie
        # Supprimer tout bloc <metadonnees> existant pour éviter les doublons
        for ancien in tei_xml.xpath(".//tei:metadonnees", namespaces={"tei": "http://www.tei-c.org/ns/1.0"}):
            ancien.getparent().remove(ancien)

        try:
            if all(var.strip() for var in
                   [auteur_nom_complet, editeur_nom_complet, titre_piece, numero_acte, numero_scene]):

                # Éviter les doublons si déjà présent
                if not tei_xml.xpath(".//tei:metadonnees", namespaces={"tei": "http://www.tei-c.org/ns/1.0"}):
                    bloc = LET.Element("{http://www.tei-c.org/ns/1.0}metadonnees")

                    # Nettoyage
                    auteur_nom_complet = auteur_nom_complet.strip('" ')
                    editeur_nom_complet = editeur_nom_complet.strip('" ')
                    titre_piece = titre_piece.strip('" ')
                    numero_acte = numero_acte.strip()
                    numero_scene = numero_scene.strip()

                    # Format de la date
                    try:
                        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
                    except:
                        locale.setlocale(locale.LC_TIME, "")  # fallback silencieux

                    # Ligne 1 à 3 : informations institutionnelles
                    LET.SubElement(bloc,
                                   "{http://www.tei-c.org/ns/1.0}credit").text = "Texte généré par Ekdosis-TEI Studio"
                    LET.SubElement(bloc,
                                   "{http://www.tei-c.org/ns/1.0}credit").text = "Chaire d'excellence en Éditions numériques"
                    LET.SubElement(bloc,
                                   "{http://www.tei-c.org/ns/1.0}credit").text = "Université de Rouen Normandie - Région Normandie"
                    # Ligne blanche (séparateur visuel)
                    LET.SubElement(bloc,
                                   "{http://www.tei-c.org/ns/1.0}credit").text = "\u00A0"  # U+00A0 = espace insécable

                    # Ligne 4 : auteur + titre italique + acte/scène
                    credit_auteur_titre = LET.Element("{http://www.tei-c.org/ns/1.0}credit")
                    credit_auteur_titre.text = auteur_nom_complet + " – "

                    hi = LET.SubElement(credit_auteur_titre, "{http://www.tei-c.org/ns/1.0}hi")
                    hi.set("rend", "italic")
                    hi.text = titre_piece
                    hi.tail = f", Acte {numero_acte}, Scène {numero_scene}"
                    LET.SubElement(bloc,
                                   "{http://www.tei-c.org/ns/1.0}credit").text = "Licence Creative Commons - CC-BY-NC-SA"

                    bloc.append(credit_auteur_titre)

                    # Ligne 5 : éditeur
                    LET.SubElement(bloc,
                                   "{http://www.tei-c.org/ns/1.0}credit").text = f"Édition critique par {editeur_nom_complet}"

                    # Ligne 6 : date
                    LET.SubElement(bloc,
                                   "{http://www.tei-c.org/ns/1.0}credit").text = "Document généré le " + french_date(date.today())

                    # Insertion en tête
                    tei_xml.insert(0, bloc)
        except Exception as e:
            print(f"[INFO] Bloc <metadonnees> non inséré : {e}")

        # XSLT complet avec belle mise en page ET infobulles avec années
        xslt_str = '''<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.tei-c.org/ns/1.0"
  exclude-result-prefixes="tei">

  <xsl:output method="html" encoding="UTF-8" indent="yes"/>

<xsl:template match="tei:stage[@type='DI']">

  <!-- on récupère SET, PROX… depuis @ana -->
  <xsl:variable name="func" select="substring-after(@ana, '#')" />

  <!-- table de conversion Galleron → label humain -->
  <xsl:variable name="label">
    <xsl:choose>
      <xsl:when test="$func='SPC'">parole</xsl:when>
      <xsl:when test="$func='ASP'">aspect</xsl:when>
      <xsl:when test="$func='TMP'">temps</xsl:when>
      <xsl:when test="$func='EVT'">événement</xsl:when>
      <xsl:when test="$func='SET'">décor</xsl:when>
      <xsl:when test="$func='PROX'">proxémie</xsl:when>
      <xsl:when test="$func='ATT'">attitude</xsl:when>
      <xsl:when test="$func='VOI'">voix</xsl:when>
      <xsl:otherwise><xsl:value-of select="$func"/></xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <!-- on stocke à la fois le code et le label -->
  <div class="stage-implicite"
       data-type="{$func}"
       data-label="{$label}">
    <xsl:apply-templates select="tei:l"/>
  </div>
</xsl:template>

  
  <xsl:template match="/tei:TEI">
    <html lang="fr">
      <head>
        <meta charset="UTF-8"/>
        <title>Édition TEI</title>
        <xsl:text disable-output-escaping="yes">
            <![CDATA[<link href="https://fonts.googleapis.com/css2?family=IM+Fell+DW+Pica&display=swap" rel="stylesheet">]]>
        </xsl:text>
        <xsl:text disable-output-escaping="yes">
            <![CDATA[<link href="https://fonts.googleapis.com/css2?family=EB+Garamond&display=swap" rel="stylesheet">]]>
        </xsl:text>
        <xsl:text disable-output-escaping="yes">
            <![CDATA[<link href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro&display=swap" rel="stylesheet">]]>
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
          .ligne-logos-gauche {
           display: flex;
           align-items: center;
           gap: 1em;
           margin-bottom: 0.5em;
          }
          .logo-credit {
           width: 200px;
           height: auto;
           opacity: 0.85;
          }
          .logo-ekdosis {
           width: 50px;
           height: auto;
           opacity: 0.9;
          }
          .bloc-credit {
           font-family: 'Source Sans Pro', sans-serif;
           font-size: 0.8em;
           color: #3a3a3a;
           margin: 1.5em 0;
           padding: 0.6em 1.1em;
           border: 1px solid #ccc2b2;
           background: #fefdf8;
           line-height: 1.2;
           text-align: left;
           max-width: 650px;
           margin-left: auto;
           margin-right: auto;
          border-radius: 6px;
          box-shadow: 1px 1px 3px rgba(0, 0, 0, 0.04);
          }
         .italic {
          font-style: italic;
          color: darkred;
          }
          .bold {
          font-weight: bold;
          }
          .underline {
          text-decoration: underline;
          }
          .acte-titre-sans-variation {
          font-weight: bold;
          margin-top: 1.5em;
          margin-bottom: 0.5em;
          margin-left: 11em;
          }
          .scene-titre-sans-variation {
          font-weight: bold;
          margin-top: 1.5em;
          margin-bottom: 0.5em;
          margin-left: 11em;
          }
        .scene-titre {
          font-style: italic;
          margin-bottom: 0.5em;
          margin-left: 0em;
        }
        .acte, .scene, .personnages {
            font-weight: bold;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            margin-left: 11em;
          }
          .titre-piece {
            font-style: italic;
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
          /* Container englobant tes vers interprétés */
          /* Titre unique au-dessus du premier bloc implicite */
          .didas-implicites-label {
           text-align: right;
           font-style: normal;
           color: #777;
           font-weight: bold;
           font-size: 0.9em;
           margin: 0.5em 0 0.2em; /* espace au-dessus et dessous */
          }
          .stage-implicite {
           position: relative;        /* pour pouvoir placer le label en absolu */
           padding-right: 6em;        /* espace à droite pour le label */
           margin: 0.5em 0;           /* un peu d’air au-dessus et en dessous */
          }
          .stage-implicite::after {
           content: attr(data-label);  /* récupère la valeur de data-type */
           position: absolute;
           top: 0;                    /* aligne en haut du premier vers */
           right: 0;                  /* plaque contre la marge droite du container */
           font-style: italic;
           color: #777;               /* gris discret */
           font-size: 0.85em;         /* un peu plus petit que le texte courant */
           white-space: nowrap;       /* ne pas couper le mot-clé */
          }
          .variation {
            position: relative;
            border-bottom: 1px dotted #8b5e3c;
            cursor: help;
          }
          .variation::after {
            content: attr(data-tooltip);
            position: absolute;
            top: 1.5em;
            left: 0;
            background: #fef3c7;
            color: #111;
            padding: 0.5em;
            border: 1px solid #e0b973;
            border-radius: 6px;
            font-size: 0.8em;
            white-space: pre-line;
            display: none;
            z-index: 1000;
            max-width: 400px;
            overflow-wrap: break-word;
          }
          .variation:hover::after {
            display: block;
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
            margin-left: 14em;
          }
        </style>
      <link rel="icon" href="https://www.normandie.fr/sites/default/files/2021-03/favicon.ico" type="image/x-icon"/>
      </head>
      <body>
        <xsl:apply-templates select="tei:metadonnees"/>
        <xsl:if test=".//tei:stage[@type='DI']">
            <div class="didas-implicites-label">didas. implicites</div>
        </xsl:if>
        <xsl:apply-templates select="tei:text"/>
      </body>
    </html>
  </xsl:template>

<xsl:template match="tei:seg">
  <xsl:apply-templates/>
</xsl:template>

 <!-- ACTES ET SCENES -->
 <!-- Acte : titre sans variante -->
<xsl:template match="tei:div[@type='act']/tei:head">
  <div class="acte-titre-sans-variation">
    <xsl:apply-templates/>
  </div>
</xsl:template>

<!-- Acte : titre sans variante -->
<xsl:template match="tei:div[@type='act']/tei:head">
  <div class="acte-titre-sans-variation">
    <xsl:apply-templates/>
  </div>
</xsl:template>

<!-- Acte : titre AVEC variante (cas d'<app> dans <head>) -->
<xsl:template match="tei:div[@type='act']/tei:head/tei:app">
  <div class="acte-titre">
    <span class="variation">
      <xsl:attribute name="data-tooltip">
        <xsl:variable name="tooltip">
          <xsl:for-each select="tei:rdg">
            <xsl:value-of select="@wit"/>
            <xsl:text>: </xsl:text>
            <xsl:value-of select="normalize-space(.)"/>
            <xsl:text>&#10;&#10;</xsl:text>
          </xsl:for-each>
        </xsl:variable>
        <xsl:value-of select="$tooltip"/>
      </xsl:attribute>
      <xsl:apply-templates select="tei:lem"/>
    </span>
  </div>
</xsl:template>

<xsl:template match="tei:div[@type='scene']/tei:head">
  <div class="scene-titre-sans-variation">
    <xsl:apply-templates/>
  </div>
</xsl:template>

<xsl:template match="tei:div[@type='scene']/tei:head/tei:app">
  <div class="scene-titre">
    <span class="variation">
      <xsl:attribute name="data-tooltip">
        <xsl:variable name="tooltip">
          <xsl:for-each select="tei:rdg">
            <xsl:value-of select="@wit"/>
            <xsl:text>: </xsl:text>
            <xsl:value-of select="normalize-space(.)"/>
            <xsl:text>&#10;&#10;</xsl:text>
          </xsl:for-each>
        </xsl:variable>
        <xsl:value-of select="$tooltip"/>
      </xsl:attribute>
      <xsl:apply-templates select="tei:lem"/>
    </span>
  </div>
</xsl:template>


  <!-- DIDASCALIES - plusieurs cas de figure -->

  <!-- Liste de personnages (avec variantes en tooltip sur <app>) -->
<xsl:template match="tei:stage[@type='characters']">
  <div class="personnages">
    <xsl:apply-templates/>
  </div>
</xsl:template>

<xsl:template match="tei:stage[@type='characters']/tei:app">
  <span class="variation" style="font-variant: small-caps;">
    <xsl:attribute name="data-tooltip">
      <xsl:variable name="tooltip">
        <xsl:for-each select="tei:rdg">
          <xsl:value-of select="@wit"/>
          <xsl:text>: </xsl:text>
          <xsl:value-of select="normalize-space(.)"/>
          <xsl:text>&#10;&#10;</xsl:text>
        </xsl:for-each>
      </xsl:variable>
      <xsl:value-of select="$tooltip"/>
    </xsl:attribute>
    <xsl:apply-templates select="tei:lem"/>
  </span>
</xsl:template>

<!-- Didascalies ordinaires -->
<xsl:template match="tei:stage">
  <p class="didascalie"><em><xsl:apply-templates/></em></p>
</xsl:template>

  <!-- Bloc de parole -->
  <xsl:template match="tei:sp">
  <div class="locuteur">
    <xsl:apply-templates select="tei:speaker"/>
  </div>
  <div class="tirade">
    <xsl:apply-templates select="tei:stage | tei:l"/>
  </div>
</xsl:template>

<xsl:template match="tei:speaker">
  <span style="font-variant: small-caps;">
    <xsl:apply-templates/>
  </span>
</xsl:template>

<xsl:template match="tei:speaker/tei:app">
  <span class="variation" style="font-variant: small-caps;">
    <xsl:attribute name="data-tooltip">
      <xsl:variable name="tooltip">
        <xsl:for-each select="tei:rdg">
          <xsl:value-of select="@wit"/>
          <xsl:text>: </xsl:text>
          <xsl:value-of select="normalize-space(.)"/>
          <xsl:text>&#10;&#10;</xsl:text>
        </xsl:for-each>
      </xsl:variable>
      <xsl:value-of select="$tooltip"/>
    </xsl:attribute>
    <xsl:apply-templates select="tei:lem"/>
  </span>
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

  <!-- Apparatus -->
  <xsl:template match="tei:app">
    <xsl:variable name="tooltip">
      <xsl:for-each select="tei:rdg">
        <xsl:variable name="t" select="normalize-space(.)"/>
        <xsl:value-of select="@wit"/>
        <xsl:text>: </xsl:text>
        <xsl:value-of select="$t"/>
        <xsl:text>&#10;&#10;</xsl:text>
      </xsl:for-each>
    </xsl:variable>
    <span class="variation">
      <xsl:attribute name="data-tooltip">
        <xsl:value-of select="$tooltip"/>
      </xsl:attribute>
      <xsl:apply-templates select="tei:lem"/>
    </span>
  </xsl:template>

<xsl:template match="tei:hi">
  <span>
    <xsl:attribute name="class">
      <xsl:value-of select="@rend"/>
    </xsl:attribute>
    <xsl:apply-templates/>
  </span>
</xsl:template>

<xsl:template match="tei:metadonnees">
  <div class="bloc-credit">
    <div class="ligne-logos-gauche">
      <img src="logos.png" alt="Logos" class="logo-credit"/>
    </div>
    <xsl:apply-templates select="tei:credit"/>
  </div>
</xsl:template>


  <xsl:template match="tei:credit">
    <div class="credit-line">
    <xsl:apply-templates/>
  </div>
  </xsl:template>

<!-- A SUPPRIMER - Ignorer les rdg dans le texte principal -->
  <xsl:template match="tei:rdg"/>
</xsl:stylesheet>
'''
        xslt_root = LET.XML(xslt_str.encode('utf-8'))
        transform = LET.XSLT(xslt_root)
        html_result = transform(tei_xml)

        chemin_script = os.path.dirname(os.path.abspath(__file__))
        chemin_temp_html = os.path.join(chemin_script, "preview_temp.html")
        with open(chemin_temp_html, "w", encoding="utf-8") as f:
            f.write(str(html_result))

        webbrowser.open(f"file://{chemin_temp_html}")

        # Proposition d’enregistrement
        enregistrer_preview(html_result)

    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur pendant la transformation XSLT :\n{e}")


def convertir_tei_en_html(tei_text):
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

        # Début de tirade
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

        # Didascalie complète (sur une seule ligne, à généraliser plus tard)
        # Didascalie complète
        elif ligne.startswith("<stage>"):
            stage_lignes = []

            # Regrouper toutes les lignes jusqu'à </stage>
            while "</stage>" not in lignes[i]:
                stage_lignes.append(lignes[i].strip())
                i += 1
            stage_lignes.append(lignes[i].strip())  # Ajouter la ligne contenant </stage>
            i += 1

            bloc_stage = "\n".join(stage_lignes)

            # Nouvelle fonction : nettoyer tout le contenu de <stage>
            def nettoyer_stage(texte):
                # Enlever toutes les balises TEI (app, lem, rdg, etc.)
                texte = re.sub(r'<[^>]+>', '', texte, flags=re.DOTALL)
                return texte.strip()

            texte_stage = nettoyer_stage(bloc_stage)

            if texte_stage:
                if dans_tirade:
                    vers_buffer.append(f'<p class="didascalie"><em>{texte_stage}</em></p>')
                else:
                    html.append(f'<p class="didascalie"><em>{texte_stage}</em></p>')

            continue



        # Vers
        elif ligne.startswith("<l "):
            vers_lignes = []

            match_vers = re.match(r'<l n="([^"]+)">', ligne)
            vers_num = match_vers.group(1) if match_vers else ""

            while not lignes[i].strip().endswith("</l>"):
                vers_lignes.append(lignes[i].strip())
                i += 1
            vers_lignes.append(lignes[i].strip())  # Ajouter le </l>
            i += 1

            bloc = "\n".join(vers_lignes)

            def extraire_lem(texte):
                texte = re.sub(r'<app>.*?<lem[^>]*>(.*?)</lem>.*?</app>', r'\1', texte, flags=re.DOTALL)
                texte = re.sub(r'<[^>]+>', '', texte)  # Nettoyer les tags restants
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

####Acte I####             → Acte I
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

def mettre_a_jour_numeros(*args):
    numeros_lignes.configure(state="normal")
    numeros_lignes.delete("1.0", "end")
    total_lignes = int(zone_saisie.index("end-1c").split('.')[0])
    lignes = "\n".join(str(i) for i in range(1, total_lignes + 1))
    numeros_lignes.insert("1.0", lignes)
    numeros_lignes.configure(state="disabled")

def synchroniser_scroll(*args):
    zone_saisie.yview(*args)
    numeros_lignes.yview(*args)

def mettre_a_jour_scroll(*args):
    scroll.set(*args)
    numeros_lignes.yview_moveto(args[0])

def ajouter_espace_si_necessaire(mot):
    if not mot:
        return ""
    if re.match(r".*[\.\,\;\:\!\?\)\]]$", mot):
        return mot + " "
    return mot + " "

def extraire_blocs_et_dialogue(lignes, nb_temoins):
    def detecter_bloc(prefix, n):
        blocs = []
        bloc_acte = []
        bloc_scene = []
        indices = []
        for i, l in enumerate(lignes):
            l_strip = l.strip()
            # Pour 3 dièses : commence par '###', finit par '###', MAIS pas 4 ou plus !
            if prefix == "###":
                if l_strip.startswith("###") and l_strip.endswith("###") and not l_strip.startswith(
                        "####") and not l_strip.endswith("####"):
                    blocs.append(l_strip)
                    indices.append(i)
            # Pour 4 dièses : idem, mais 4 dièses pile
            elif prefix == "####":
                if l_strip.startswith("####") and l_strip.endswith("####") and not l_strip.startswith(
                        "#####") and not l_strip.endswith("#####"):
                    blocs.append(l_strip)
                    indices.append(i)
            # Pour 2 dièses, cas particulier personnages
            elif prefix == "##":
                if l_strip.startswith("##") and not l_strip.startswith("###"):
                    blocs.append(l_strip)
                    indices.append(i)
        if len(blocs) != n:
            print(f"[AVERTISSEMENT] {len(blocs)} blocs trouvés pour préfixe {prefix}, {n} attendus.")
        return blocs, indices

    # 1. Bloc à 4 dièses (optionnel)
    bloc_acte, idx_acte = detecter_bloc("####", nb_temoins)
    bloc_scene, idx_scene = [], []
    bloc_persos, idx_persos = [], []

    start_idx = max(idx_acte) + 1 if bloc_acte else 0

    # 2. Bloc à 3 dièses (obligatoire)
    bloc_scene, idx_scene = detecter_bloc("###", nb_temoins)
    start_idx = max(idx_scene) + 1 if bloc_scene else start_idx

    # 3. Bloc à 2 dièses (obligatoire)
    bloc_persos, idx_persos = detecter_bloc("##", nb_temoins)
    start_idx = max(idx_persos) + 1 if bloc_persos else start_idx

    # 4. Le reste : dialogue pur, à partir de start_idx
    lignes_dialogue = lignes[start_idx:]

    dialogues = []
    i = 0
    while i < len(lignes_dialogue):
        bloc_locuteur = []
        # Bloc de variantes de locuteur
        while (
                i < len(lignes_dialogue)
                and lignes_dialogue[i].strip().startswith("#")
                and lignes_dialogue[i].strip().endswith("#")
        ):
            bloc_locuteur.append(lignes_dialogue[i].strip())
            i += 1

        if bloc_locuteur:
            if len(bloc_locuteur) != nb_temoins:
                print(
                    f"[ERREUR] Bloc de locuteur mal formé : {len(bloc_locuteur)} lignes détectées, {nb_temoins} attendues.")
            # Texte associé à ce bloc de locuteur (jusqu’au prochain bloc #...#)
            bloc_texte = []
            while (
                    i < len(lignes_dialogue)
                    and not (lignes_dialogue[i].strip().startswith("#") and lignes_dialogue[i].strip().endswith("#"))
            ):
                bloc_texte.append(lignes_dialogue[i])
                i += 1
            dialogues.append((bloc_locuteur, "\n".join(bloc_texte)))
        else:
            i += 1

    # Nettoyage optionnel : on vire les blocs vides (au cas où)
    dialogues = [(loc, bloc) for loc, bloc in dialogues if bloc.strip()]

    return (
        bloc_acte if bloc_acte else None,
        bloc_scene if bloc_scene else None,
        bloc_persos if bloc_persos else None,
        dialogues
    )

def encoder_balise_complete(texte):
    """
    Applique encoder_caracteres_tei à l’intérieur d’une balise complète <...>...</...>,
    sans toucher aux chevrons.
    """
    match = re.match(r'^(<[^>]+>)(.*?)(</[^>]+>)$', texte)
    if match:
        balise_ouv, contenu, balise_ferm = match.groups()
        contenu_encode = encoder_caracteres_tei(contenu)
        return f"{balise_ouv}{contenu_encode}{balise_ferm}"
    else:
        # Si ce n’est pas une balise complète, encoder normalement
        return encoder_caracteres_tei(texte)

def est_balise_complete(token):
    return bool(re.match(r'^<[^>]+>.*?</[^>]+>$', token))

def remplacer_tildes_par_espaces_insecables(texte):
    return texte.replace("~", "&#160;")

def aligner_variantes_par_mot(tokens, temoins, ref_index):
    ligne_tei = []
    ligne_ekdosis = []

    max_len = max(len(t) for t in tokens)

    for i in range(max_len):
        mots_colonne = defaultdict(list)

        for j, ligne in enumerate(tokens):
            mot = ligne[i] if i < len(ligne) else ""
            mots_colonne[mot].append(temoins[j])

        lemme = tokens[ref_index][i] if i < len(tokens[ref_index]) else ""

        if len(mots_colonne) == 1:
            # Pas de variante
            if est_balise_complete(lemme):
                lemme_traite = encoder_balise_complete(lemme)
            else:
                lemme_traite = encoder_caracteres_tei(lemme)

            ligne_tei.append(lemme_traite + " ")
            ligne_ekdosis.append(echapper_caracteres_ekdosis(lemme))
            continue

        # Variante
        ligne_tei.append("\n      <app>\n")
        if est_balise_complete(lemme):
            lemme_affiche = encoder_balise_complete(lemme)
        else:
            lemme_affiche = encoder_caracteres_tei(ajouter_espace_si_necessaire(lemme))
        ligne_tei.append(
            f'        <lem wit="{" ".join(f"#{t}" for t in mots_colonne.get(lemme, []))}">{lemme_affiche}</lem>\n'
        )

        for mot, wits in mots_colonne.items():
            if mot != lemme:
                if est_balise_complete(mot):
                    mot_affiche = encoder_balise_complete(mot)
                else:
                    mot_affiche = encoder_caracteres_tei(ajouter_espace_si_necessaire(mot))
                ligne_tei.append(
                    f'        <rdg wit="{" ".join(f"#{t}" for t in wits)}">{mot_affiche}</rdg>\n'
                )
        ligne_tei.append("      </app>\n")

        # Ekdosis
        ekdo = [f' \n      \\app{{']
        ekdo.append(
            f'        \\lem[wit={{{", ".join(mots_colonne.get(lemme, []))}}}]{{{echapper_caracteres_ekdosis(lemme)}}}'
        )
        for mot, wits in mots_colonne.items():
            if mot != lemme:
                ekdo.append(
                    f'        \\rdg[wit={{{", ".join(wits)}}}]{{{echapper_caracteres_ekdosis(mot)}}}'
                )
        ekdo.append("      }")
        ligne_ekdosis.append("\n".join(ekdo))

    return ligne_tei, ligne_ekdosis

def speaker_aligned_output(speaker_list, temoins, ref_index, aligner_fonction):
    #
    # Retourne la bonne chaîne <speaker> ou \speaker pour la liste de locuteurs,
    # en tenant compte des variantes et en évitant les répétitions inutiles.
    #
    cleaned = [l.strip("#").strip() for l in speaker_list]
    if all(n == cleaned[0] for n in cleaned):
        # Tous identiques: un seul nom
        return cleaned[0], cleaned[0]
    else:
        tokens = [[n] for n in cleaned]
        ligne_tei, ligne_ekdosis = aligner_fonction(tokens, temoins, ref_index)
        return "".join(ligne_tei).strip(), "".join(ligne_ekdosis).strip()

def verifier_et_comparer():
    if valider_structure():
        comparer_etats()
    else:
        reponse = messagebox.askyesno(
            "Structure incorrecte",
            "Des erreurs ont été détectées dans la structure.\n"
            "Souhaitez-vous quand même générer le code ?"
        )
        if reponse:
            comparer_etats()


def tokenizer_avec_balises(texte):
    # Capture tout bloc <balise>…</balise> comme unité indivisible
    return re.findall(r'<[^>]+>.*?</[^>]+>|\S+', texte)



def comparer_etats():
    stage_implicite_type = None
    implicit_counter = 0
    texte = zone_saisie.get("1.0", tk.END).strip()
    lignes = texte.splitlines()

    # Étape : remplacer les italiques Markdown _..._ par des balises TEI <hi>
    def convertir_italique_tei(texte):
        return re.sub(r'_(.+?)_', r'<hi rend="italic">\1</hi>', texte)

    lignes = [convertir_italique_tei(l) for l in lignes]

    sous_blocs_ignorés = set()
    resultat_ekdosis = []

    dialogues = []
    current_acte = None
    current_scene = None
    current_personnages = []
    current_speaker = None
    current_bloc = []

    bloc_acte, bloc_scene, bloc_persos, dialogues = extraire_blocs_et_dialogue(lignes, nombre_temoins_predefini)

    print("ACTE :", bloc_acte)
    print("SCENE :", bloc_scene)
    print("PERSOS :", bloc_persos)
    print("DIALOGUES :", dialogues)

    # ------------- ACTE -------------
    if bloc_acte:
        tokens = [[l.strip("#").strip()] for l in bloc_acte]
        ref_index = liste_ref.current()
        temoins = [chr(65 + i) for i in range(nombre_temoins_predefini)]
        ligne_tei, ligne_ekdosis = aligner_variantes_par_mot(tokens, temoins, ref_index)
        # Injection dans le résultat TEI (juste après ouverture du <div type="act">)
        tei_head = '    <head>' + "".join(ligne_tei).strip() + '</head>'
        # (garde le résultat à réinjecter juste après l’ouverture de l’acte)
        head_acte_ekdosis = tokens[ref_index][0]
        # possibilité d'affichage de l'acte en ajoutant head={head_acte_ekdosis}
        ekddiv_acte = f'\\ekddiv{{type=act, n={numero_acte}, depth=2}}'
        ekdosis_head = "\n".join(ligne_ekdosis).strip()  # variantes (ou rien si pas de variantes)
        ekdosis_head = f"\\stage{{{ekdosis_head}}}"

    else:
        tei_head = None
        ekddiv_acte = None
        ekdosis_head = None

    # ------------- SCENE -------------
    if bloc_scene:
        tokens = [[l.strip("#").strip()] for l in bloc_scene]
        ref_index = liste_ref.current()
        temoins = [chr(65 + i) for i in range(nombre_temoins_predefini)]
        ligne_tei_scene, ligne_ekdosis_scene = aligner_variantes_par_mot(tokens, temoins, ref_index)
        tei_scene_head = '    <head>' + "".join(ligne_tei_scene).strip() + '</head>'

        # Génération du \ekddiv et du titre encapsulé dans \stage{}
        head_scene_ekdosis = tokens[ref_index][0]
        # possibilité d'afficher head={head_scene_ekdosis}
        ekddiv_scene = f'\\ekddiv{{type=scene, n={numero_scene}, depth=3}}'
        ekdosis_scene_head = "\n".join(ligne_ekdosis_scene).strip()
        if ekdosis_scene_head:
            ekdosis_scene_head = f"\\stage{{{ekdosis_scene_head}}}"

    # ------------- PERSONNAGES -------------
    if bloc_persos:
        tokens = [[l.replace("#", "").strip()] for l in bloc_persos]
        ref_index = liste_ref.current()
        temoins = [chr(65 + i) for i in range(nombre_temoins_predefini)]
        ligne_tei_persos, ligne_ekdosis_persos = aligner_variantes_par_mot(tokens, temoins, ref_index)
        tei_persos_stage = "    <stage type='personnages'>" + "".join(ligne_tei_persos).strip() + '</stage>'
        ekdosis_persos_stage = "\\stage{" + "".join(ligne_ekdosis_persos).strip() + "}"
    else:
        tei_persos_stage = None
        ekdosis_persos_stage = None

    print('DIALOGUES =', dialogues)
    try:
        numero_depart = int(entree_vers.get())
    except ValueError:
        messagebox.showwarning("Erreur", "Le numéro de vers de départ doit être un entier.")
        return

    # Valeurs par défaut pour le header
    titre = globals().get("titre_piece", "").strip() or "Titre non renseigné"
    auteur = globals().get("auteur_nom_complet", "").strip() or "Auteur inconnu"
    editeur = globals().get("editeur_nom_complet", "").strip() or "Éditeur scientifique inconnu"
    num_acte = globals().get("numero_acte", "").strip() or "?"
    num_scene = globals().get("numero_scene", "").strip() or "?"

    # Construction sécurisée du header TEI
    aujourdhui = french_date(date.today())
    resultat_ekdosis = []
    resultat_tei = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">',
        '  <teiHeader>',
        '    <fileDesc>',
        f'      <titleStmt>',
        f'        <title>{titre}</title>',
        f'        <author>{auteur}</author>',
        f'        <editor>{editeur}</editor>',
        f'      </titleStmt>',
        '      <publicationStmt>',
        '        <publisher>Presses de l\'Université de Rouen et du Havre</publisher>',
        '        <pubPlace>Rouen</pubPlace>',
        f'       <date>{aujourdhui}</date>',
        '      </publicationStmt>',
        '      <sourceDesc>',
        f'        <p>généré par Ekdosis-TEI Studio – Acte {num_acte}, Scène {num_scene}</p>',
        '      </sourceDesc>',
        '    </fileDesc>',
        '  </teiHeader>',
        '  <text>',
        '    <body>'
    ]

    vers_courant = numero_depart
    dernier_locuteur = None
    changement_locuteur_deja_traite = False  # ← ajoute cette ligne ici

    # === Construction de la chaîne ===
    # === TEI ===

    if bloc_acte:
        print("DEBUG: bloc_acte =", bloc_acte)
        resultat_tei.append(f'<div type="act" n="{num_acte}">')

    if tei_head:
        resultat_tei.append(tei_head)

    if bloc_scene:
        resultat_tei.append(f'  <div type="scene" n="{num_scene}">')

    if tei_scene_head:
        resultat_tei.append(tei_scene_head)

    if tei_persos_stage:
        resultat_tei.append(tei_persos_stage)

    # === EKDOSIS ===
    if bloc_acte:
        if ekddiv_acte:
            resultat_ekdosis.append(ekddiv_acte)
        if ekdosis_head:
            resultat_ekdosis.append(ekdosis_head)
    if bloc_scene:
        if ekddiv_scene:
            resultat_ekdosis.append(ekddiv_scene)
        if ekdosis_scene_head:
            resultat_ekdosis.append(ekdosis_scene_head)
    if ekdosis_persos_stage:
        resultat_ekdosis.append(ekdosis_persos_stage)

    for speaker, bloc in dialogues:
        speakers = speaker if isinstance(speaker, list) else [speaker]

        sous_blocs = bloc.split("\n\n")

        if speakers != dernier_locuteur:
            if dernier_locuteur is not None:
                resultat_tei.append("    </sp>")
                resultat_ekdosis.append("      \\end{ekdverse}\n    \\end{speech}")

            # ALIGNE VARIANTES
            tokens = [[l.strip("#").strip()] for l in speakers]
            temoins = [chr(65 + i) for i in range(len(speakers))]
            ref_index = liste_ref.current()
            ligne_tei, ligne_ekdosis = aligner_variantes_par_mot(tokens, temoins, ref_index)
            tei_speaker = "".join(ligne_tei).strip()
            ekdosis_speaker = "".join(ligne_ekdosis).strip()

            resultat_tei.append(f'    <sp>\n      <speaker>{tei_speaker}</speaker>')
            resultat_ekdosis.append(
                "    \\begin{speech}\n      \\speaker{" + ekdosis_speaker + "}\n      \\begin{ekdverse}")
            dernier_locuteur = speakers  # On mémorise toujours la liste (pour la prochaine itération)

        for sous_bloc in sous_blocs:
            sous_bloc_texte = normaliser_bloc(sous_bloc)
            if sous_bloc_texte in sous_blocs_ignorés:
                speaker = speaker_suivant
                continue

            lignes = [l.strip() for l in sous_bloc.strip().splitlines() if l.strip()]

            # Traitement des didascalies implicites
            # Didascalies implicites
            m = re.match(r'^\$\$(.+)\$\$$', lignes[0])
            if stage_implicite_type is None \
                    and len(lignes) == nombre_temoins_predefini \
                    and len(set(lignes)) == 1 \
                    and m:
                # la fonction éditoriale, ex. "SET" ou "PROX"
                func = m.group(1).strip().upper()
                # on génère un xml:id unique (ici fondé sur un compteur)
                implicit_counter += 1
                xml_id = f"implicite{implicit_counter}"
                # DI = didascalie interne
                resultat_tei.append(
                    f'      <stage xml:id="{xml_id}" type="DI" ana="#{func}">'
                )
                stage_implicite_type = func
                continue

            # … puis, quand tu détectes la ligne de clôture "$$" :
            if stage_implicite_type is not None and re.match(r'^\$\$\s*fin\s*\$\$$', lignes[0]):
                resultat_tei.append('      </stage>')
                stage_implicite_type = None
                continue


            # Didascalies
            if all(l.startswith('**') for l in lignes) and len(lignes):
                print('didascalie reperee')
                temoins = [chr(65 + i) for i in range(len(lignes))]
                # On retire *toutes* les étoiles au début et à la fin (même si >2), puis on strip
                didascalies_nettoyees = [re.sub(r'^\*+\s*|\s*\*+$', '', l).strip() for l in lignes]
                # Pour les didascalies, en général, tu veux un alignement "texte entier" (pas split par mot)
                tokens = [[d] for d in didascalies_nettoyees]
                ref_index = liste_ref.current()

                ligne_tei, ligne_ekdosis = aligner_variantes_par_mot(tokens, temoins, ref_index)

                resultat_tei.append('      <stage type="stage-direction">\n' + "".join(ligne_tei) + '      </stage>\n')
                resultat_ekdosis.append(
                    '      \\didas{' +
                    "".join(ligne_ekdosis) +
                    '}'
                )

                # NE PAS toucher à vers_courant ici! On ne l’incrémente ni le décrémente.
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
                ligne_tei, ligne_ekdosis = aligner_variantes_par_mot(tokens_1, temoins, liste_ref.current())

                # Ajout du premier demi-vers
                resultat_tei.append(f'<l n="{vers_num_1}">\n' + "".join(ligne_tei) + '</l>')
                vers_formate_1 = " ".join(part.strip() for part in ligne_ekdosis)
                resultat_ekdosis.append(
                    f'        \\vnum{{{vers_num_1}}}' + '{\n' + vers_formate_1 + '\\\\    \n         }')

                # ✅ Initialisation du bloc B
                bloc_b_complet = None
                lignes_suivantes = []
                trouver_debut = False
                trouver_texte = False
                speaker_suivant = None

                for speaker2, bloc2 in dialogues:
                    if trouver_debut:
                        lignes_brutes = bloc2.strip().splitlines()
                        lignes_b_nettoyees = []
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
                        if len(lignes_suivantes) >= len(lignes):
                            bloc_b_complet = "\n".join(lignes_b_nettoyees)
                            speaker_suivant = speaker2
                            break
                    if bloc2.strip() == bloc.strip():
                        trouver_debut = True

                # ✅ Ajout du bloc B à ignorer (entier)
                if bloc_b_complet:
                    sous_blocs_ignorés.add(normaliser_bloc(bloc_b_complet))

                if lignes_suivantes:
                    tokens_2 = [l.split() for l in lignes_suivantes]
                    temoins_2 = [chr(65 + i) for i in range(len(tokens_2))]

                    ligne_tei, ligne_ekdosis = aligner_variantes_par_mot(tokens_2, temoins_2, liste_ref.current())

                    # ✅ Changement de locuteur si nécessaire
                    if speaker_suivant and speaker_suivant != dernier_locuteur:
                        # Pour éviter tout bug, assure que speaker_suivant est une liste :
                        speakers = speaker_suivant if isinstance(speaker_suivant, list) else [speaker_suivant]
                        temoins = [chr(65 + i) for i in range(len(speakers))]
                        ref_index = liste_ref.current()

                        # On aligne ou on prend direct, selon uniformité
                        tei_speaker, ekdosis_speaker = speaker_aligned_output(
                            speakers, temoins, ref_index, aligner_variantes_par_mot
                        )

                        # Fermeture puis ouverture de balises de locuteur
                        resultat_tei.append(f"    </sp>\n    <sp>\n      <speaker>{tei_speaker}</speaker>")
                        resultat_ekdosis.append("      \\end{ekdverse}\n    \\end{speech}")
                        resultat_ekdosis.append(
                            f"    \\begin{{speech}}\n      \\speaker{{{ekdosis_speaker}}}\n      \\begin{{ekdverse}}"
                        )
                        dernier_locuteur = speaker_suivant  # mise à jour
                        changement_locuteur_deja_traite = True

                    # ✅ Ajout du second demi-vers
                    resultat_tei.append(f'<l n="{vers_num_2}">\n' + "".join(ligne_tei) + '</l>')

                    vers_formate_2 = " ".join(part.strip() for part in ligne_ekdosis)
                    # ekdosis peu intuitif sur la numérotation des vers
                    # • lineation=none         → désactive la colonne de numérotation à gauche
                    # • modulo + vmodulo=0     → désactive l’affichage périodique des numéros à droite
                    resultat_ekdosis.append("""        \\SetLineation{
                                lineation=none,
                                modulo,
                                vmodulo=0
                            }""")
                    resultat_ekdosis.append(
                        f'        \\vnum{{{vers_num_2}}}' + '{\n' + '\\hspace*{5em}' + vers_formate_2 + '\\\\    \n         }')
                    resultat_ekdosis.append(f'        \\resetvlinenumber[{math.ceil(numero_vers_base) + 1}]')
                    resultat_ekdosis.append("        \\SetLineation{vmodulo=5}")

                # ✅ Ignorer aussi le bloc A (le premier demi-vers)
                sous_bloc_texte = "\n".join(lignes)
                sous_blocs_ignorés.add(sous_bloc_texte)
                vers_courant = math.ceil(numero_vers_base) + 1
                continue

            # Si ligne unique non didascalique, on ignore
            if len(lignes) < 2:
                continue

            # Cas spécial : variantes vers entier (toutes lignes commencent par 5 dièses)
            if all(l.startswith('#####') for l in lignes) and len(lignes):
                print('vers entier à traiter repere')
                temoins = [chr(65 + i) for i in range(len(lignes))]
                ref_index = liste_ref.current()
                # On enlève les 5 dièses et on strippe chaque vers
                vers_variantes = [l[5:].strip() for l in lignes]

                tei = '      <app>\n'

                # D'abord le lem (variante de référence)
                tei += f'        <lem wit="#{temoins[ref_index]}">{encoder_caracteres_tei(vers_variantes[ref_index])}</lem>\n'

                # Puis les autres variantes (rdg)
                for idx, vers in enumerate(vers_variantes):
                    if idx != ref_index:
                        wit = f"#{temoins[idx]}"
                        tei += f'        <rdg wit="{wit}">{encoder_caracteres_tei(vers)}</rdg>\n'

                tei += '      </app>\n'
                resultat_tei.append(f'<l n="{vers_courant}">\n{tei}</l>\n')

                # Pour Ekdosis :
                ekdo = ['      \\app{']
                ekdo.append(
                    f'        \\lem[wit={{{temoins[ref_index]}}}]{{{echapper_caracteres_ekdosis(vers_variantes[ref_index])}}}')
                for idx, vers in enumerate(vers_variantes):
                    if idx == ref_index:
                        continue
                    ekdo.append(f'        \\rdg[wit={{{temoins[idx]}}}]{{{echapper_caracteres_ekdosis(vers)}}}')
                ekdo.append("      }")
                resultat_ekdosis.append(
                    f"        \\vnum{{{vers_courant}}}{{\n{chr(10).join(ekdo)}  \\\\    \n        }}")

                # Incrémenter le numéro de vers
                if vers_courant == int(vers_courant):
                    vers_courant += 1
                else:
                    vers_courant = math.ceil(vers_courant)
                continue

            # Conversion italique inline _mot_ → <hi rend="italic">mot</hi>
            def convertir_italique_tei(texte):
                return re.sub(r'_(.+?)_', r'<hi rend="italic">\1</hi>', texte)

            lignes = [convertir_italique_tei(l) for l in lignes]

            temoins = [chr(65 + i) for i in range(len(lignes))]

            tokens = [tokenizer_avec_balises(l) for l in lignes]

            ref_index = liste_ref.current()

            ligne_tei, ligne_ekdosis = aligner_variantes_par_mot(tokens, temoins, ref_index)

            resultat_tei.append(f'<l n="{vers_courant}">\n' + "".join(ligne_tei) + '</l>\n')
            vers_formate = " ".join(ligne_ekdosis)
            resultat_ekdosis.append(f"        \\vnum{{{vers_courant}}}{{\n{vers_formate}  \\\\    \n        }}")

            if vers_courant == int(vers_courant):
                vers_courant += 1
            else:
                vers_courant = math.ceil(vers_courant)

        if dernier_locuteur != speaker and not changement_locuteur_deja_traite:
            resultat_tei.append("    </sp>")
            resultat_ekdosis.append("      \\end{ekdverse}\n    \\end{speech}")

        changement_locuteur_deja_traite = False  # ← réinitialisation à chaque itération

    resultat_tei.append('</sp>')
    resultat_ekdosis.append("      \\end{ekdverse}\n    \\end{speech}")

    if bloc_scene:
        resultat_tei.append('</div>')
    if bloc_acte:
        resultat_tei.append('</div>')

    zone_resultat_tei.delete("1.0", tk.END)

    resultat_tei.append('</body></text>')
    ### Ci-dessous comportement normal de fermeture
    resultat_tei.append('</TEI>')
    zone_resultat_tei.insert(tk.END, "\n".join(resultat_tei) + "\n")

    zone_resultat_ekdosis.delete("1.0", tk.END)
    zone_resultat_ekdosis.insert(tk.END, "\n".join(resultat_ekdosis) + "\n")

    # Mise à jour automatique de la prévisualisation HTML
    if 'zone_resultat_html' in globals():
        try:
            html = convertir_tei_en_html(zone_resultat_tei.get("1.0", tk.END))
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

menu_fichier.add_command(label="Charger un échantillon de test", command=importer_echantillon)
menu_fichier.add_separator()
menu_fichier.add_command(label="Réinitialiser la saisie", command=reset_application)
menu_fichier.add_command(label="Charger une configuration", command=charger_configuration)
menu_fichier.add_command(label="Sauvegarder la configuration sous...", command=sauvegarder_config_sous)
menu_fichier.add_command(label="Éditer la configuration en cours", command=editer_config_courant)
menu_fichier.add_separator()
menu_fichier.add_command(label="Charger un texte saisi", command=charger_texte_zone_saisie)
menu_fichier.add_command(label="Exporter la saisie (txt)", command=enregistrer_saisie)
menu_fichier.add_separator()
menu_fichier.add_command(label="Exporter TEI", command=exporter_tei)
menu_fichier.add_command(label="Exporter la feuille XSLT", command=exporter_xslt)
menu_fichier.add_separator()
menu_fichier.add_command(label="Exporter ekdosis", command=exporter_ekdosis)
menu_fichier.add_command(label="Exporter le template ekdosis", command=exporter_template_ekdosis)
menu_fichier.add_separator()
menu_fichier.add_command(label="Exporter HTML", command=previsualiser_html)
menu_fichier.add_separator()
menu_fichier.add_command(label="Quitter", command=fenetre.quit)

# --- Menu Édition ---
menu_edit = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Édition", menu=menu_edit)

menu_edit.add_command(label="Couper", accelerator="Ctrl+X",
                      command=lambda: fenetre.focus_get().event_generate('<<Cut>>'))
menu_edit.add_command(label="Copier", accelerator="Ctrl+C",
                      command=lambda: fenetre.focus_get().event_generate('<<Copy>>'))
menu_edit.add_command(label="Coller", accelerator="Ctrl+V",
                      command=lambda: fenetre.focus_get().event_generate('<<Paste>>'))
menu_edit.add_command(label="Tout sélectionner", accelerator="Ctrl+A",
                      command=lambda: fenetre.focus_get().event_generate('<<SelectAll>>'))
menu_edit.add_separator()
menu_edit.add_command(label="Rechercher", command=lambda: rechercher(zone_saisie))

# --- Menu Outils ---
menu_outils = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Outils", menu=menu_outils)

menu_outils.add_command(label="Lancer l’assistant de saisie", command=lancer_saisie_assistee_par_menu)
menu_outils.add_command(label="Valider la structure", command=valider_structure)
menu_outils.add_command(label="Comparer les états", command=comparer_etats)
menu_edit.add_separator()
menu_outils.add_command(label="Fusionner HTML", command=fusionner_html)
menu_outils.add_command(label="Fusionner Markdown", command=fusionner_markdown)
menu_outils.add_command(label="Fusionner TEI", command=fusionner_tei)
menu_outils.add_command(label="Fusionner Ekdosis", command=fusionner_ekdosis)
menu_outils.add_command(label="Préparer html pour visualisation", command=nettoyer_html_unique)

# Menu Affichage
menu_affichage = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Affichage", menu=menu_affichage)
menu_affichage.add_command(label="Prévisualisation HTML", command=previsualiser_html)

# Menu Aide
menu_aide = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Aide", menu=menu_aide)
menu_aide.add_command(
    label="Afficher l'aide",
    command=afficher_aide
)

###

# Style parchemin pour les onglets TTK
style = ttk.Style()
style.theme_use('default')

style.configure("TNotebook", background="#fdf6e3", borderwidth=0)
style.configure("TNotebook.Tab", background="#f5ebc4", foreground="#4a3c1a", padding=[10, 4],
                font=("Georgia", 10, "bold"))
style.map("TNotebook.Tab", background=[("selected", "#e8dbab")])

# fenetre.iconbitmap("favicon.ico")
fenetre.title("Comparateur avec scènes, personnages et locuteurs")
fenetre.update_idletasks()
fenetre.minsize(1000, fenetre.winfo_reqheight())
fenetre.bind_all("<Control-s>", lambda event: enregistrer_saisie())
#fenetre.bind("<Control-f>", lambda e: rechercher())
#fenetre.bind("<Control-h>", lambda e: remplacer_avance())

afficher_nagscreen()

frame_saisie = tk.LabelFrame(fenetre, text="Saisie des variantes", padx=10, pady=5, bg="#f4f4f4")
frame_saisie.pack(fill=tk.BOTH, padx=10, pady=10)

label_texte = tk.Label(frame_saisie,
                       text="Utilisez ####a#### pour un acte, ###n### pour une scène, ##Nom## pour les personnages, et #Nom# pour le locuteur :",
                       bg="#f4f4f4")
label_texte.pack()

# Frame contenant la numérotation et la zone de saisie
frame_saisie = tk.Frame(fenetre)  # ou root ou autre conteneur

# Numérotation des lignes (non éditable)
numeros_lignes = tk.Text(frame_saisie, width=4, padx=4, takefocus=0,
                         border=0, background='lightgrey', state='disabled',
                         wrap='none', font=("Courier", 10))
numeros_lignes.pack(side="left", fill="y")

# Zone de texte principale
zone_saisie = tk.Text(frame_saisie, wrap="none", undo=True, font=("Courier", 10))
scroll = tk.Scrollbar(frame_saisie, command=synchroniser_scroll)
zone_saisie.configure(yscrollcommand=mettre_a_jour_scroll)
zone_saisie.pack(side="left", fill="both", expand=True)
scroll.pack(side="right", fill="y")

# Intégration dans l'interface
frame_saisie.pack(fill="both", expand=True)

zone_saisie.bind('<Control-f>', lambda e: rechercher(zone_saisie))
menu_edit.add_command(label="Remplacement avancé dans la saisie", command=lambda: remplacer_avance(zone_saisie))
zone_saisie.bind("<KeyRelease>", mettre_a_jour_numeros)
zone_saisie.bind("<MouseWheel>", lambda e: (zone_saisie.yview_scroll(int(-1*(e.delta/120)), "units"), mettre_a_jour_numeros()))
zone_saisie.bind("<Button-1>", lambda e: zone_saisie.after(10, mettre_a_jour_numeros))

# Mise à jour initiale
mettre_a_jour_numeros()

try:
    nom_auto = nom_fichier("autosave", "txt")
    if os.path.exists(nom_auto):
        with open(nom_auto, "r", encoding="utf-8") as f:
            zone_saisie.insert("1.0", f.read())
except Exception as e:
    print(f"[autosave] Impossible de charger le fichier : {e}")

def boite_initialisation_parchemin():
    champs_def = [
        ("Nom de l'auteur", ""),
        ("Prénom de l'auteur", ""),
        ("Titre de la pièce", ""),
        ("Numéro de l'acte", ""),
        ("Numéro de la scène", ""),
        ("Nombre de scènes dans l'acte", ""),
        ("Noms des personnages (séparés par virgule)", ""),
        ("Numéro du vers de départ", ""),
        ("Nombre de témoins", ""),
        ("Nom de l'éditeur (vous)", ""),
        ("Prénom de l'éditeur", ""),
    ]

    dialog = tk.Toplevel()
    dialog.title("Initialisation du projet")
    dialog.configure(bg="#fdf6e3")
    dialog.geometry("640x500")
    dialog.minsize(600, 500)
    dialog.resizable(True, True)
    dialog.grab_set()

    police_label = ("Georgia", 11)
    police_entree = ("Georgia", 11)

    champs_vars = {}

    for label_text, default in champs_def:
        var = tk.StringVar(value=default)
        champs_vars[label_text] = var

        frame = tk.Frame(dialog, bg="#fdf6e3")
        frame.pack(padx=20, pady=5, fill=tk.X)

        label = tk.Label(frame, text=label_text, bg="#fdf6e3", fg="#4a3c1a",
                         font=police_label, wraplength=250, anchor="w", justify="left", width=35)
        label.pack(side=tk.LEFT)

        entry = tk.Entry(frame, textvariable=var, font=police_entree, width=30)
        entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)

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

btn_comparer = tk.Button(frame_bas, text="Générer code", command=verifier_et_comparer)
btn_comparer.pack(side=tk.LEFT, padx=10)

btn_export_tei = tk.Button(frame_bas, text="💾 Exporter TEI", command=exporter_tei)
btn_export_tei.pack(side=tk.LEFT, padx=10)

btn_export_ekdosis = tk.Button(frame_bas, text="💾 Exporter ekdosis", command=exporter_ekdosis)
btn_export_ekdosis.pack(side=tk.LEFT, padx=10)

btn_sauver_saisie = tk.Button(frame_bas, text="💾 Export saisie brute", command=enregistrer_saisie)
btn_sauver_saisie.pack(side=tk.LEFT, padx=10)

btn_remplacer = tk.Button(frame_bas, text="💾 Export complet", command=enregistrer_triple)
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

# choix du lemme - témoin de référence. Important!
label_ref = tk.Label(frame_ref, text="Témoin de référence :", bg="#f4f4f4")
label_ref.pack(side=tk.LEFT)

menu_ref = ttk.Combobox(frame_ref, state="readonly", width=5)
menu_ref.pack(side=tk.LEFT)
temoins = ["B", "A", "C"]  # exemple
temoins.sort()  # tri alphabétique
menu_ref['values'] = temoins
menu_ref.set(temoins[0])  # sélection par défaut
liste_ref = menu_ref

frame_vers = tk.Frame(frame_params, bg="#f4f4f4")
frame_vers.pack(side=tk.LEFT, padx=10)

###  DEBUG
### Ligne sans doute à supprimer pour éviter les ambiguités
### le numéro du vers étant initialisé par ailleurs
label_vers = tk.Label(frame_vers, text="Numéro du 1er vers :", bg="#f4f4f4")
label_vers.pack(side=tk.LEFT)

entree_vers = tk.Entry(frame_vers, width=5)
entree_vers.insert(0, "1")  # valeur temporaire par défaut
entree_vers.pack(side=tk.LEFT)

notebook = ttk.Notebook(fenetre)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# TEI
onglet_tei = tk.Frame(notebook, bg="white")
zone_resultat_tei = scrolledtext.ScrolledText(onglet_tei, height=15, undo=True, maxundo=-1)
zone_resultat_tei.pack(fill=tk.BOTH, expand=True)
notebook.add(onglet_tei, text="🧾 TEI")
zone_saisie.bind('<Control-f>', lambda e: rechercher(zone_resultat_tei))
menu_edit.add_command(label="Remplacement avancé dans le TEI", command=lambda: remplacer_avance(zone_resultat_tei))

# ekdosis
onglet_ekdosis = tk.Frame(notebook, bg="white")
zone_resultat_ekdosis = scrolledtext.ScrolledText(onglet_ekdosis, height=15, undo=True, maxundo=-1)
zone_resultat_ekdosis.pack(fill=tk.BOTH, expand=True)
notebook.add(onglet_ekdosis, text="📘 ekdosis")
zone_saisie.bind('<Control-f>', lambda e: rechercher(zone_resultat_ekdosis))

# HTML
onglet_html = tk.Frame(notebook, bg="white")
zone_resultat_html = scrolledtext.ScrolledText(onglet_html, height=15, undo=True, maxundo=-1, bg="white", fg="#4a3c1a",
                                               font=("Georgia", 11))
zone_resultat_html.pack(fill=tk.BOTH, expand=True)
notebook.add(onglet_html, text="🌐 html")
zone_saisie.bind('<Control-f>', lambda e: rechercher(zone_resultat_html))

# appliquer_style_light(fenetre)
appliquer_style_parchemin(fenetre)

# --- Raccourcis clavier globaux ---
zone_saisie.bind("<Control-f>", lambda e: rechercher(zone_saisie))
zone_resultat_tei.bind("<Control-f>", lambda e: rechercher(zone_resultat_tei))

# Sans doute à effacer tous
fenetre.bind_all("<Control-a>", lambda event: fenetre.focus_get().event_generate('<<SelectAll>>'))
fenetre.bind_all("<Control-x>", lambda event: fenetre.focus_get().event_generate('<<Cut>>'))
fenetre.bind_all("<Control-c>", lambda event: fenetre.focus_get().event_generate('<<Copy>>'))
# fenetre.bind_all("<Control-v>", lambda event: fenetre.focus_get().event_generate('<<Paste>>'))


fenetre.mainloop()
