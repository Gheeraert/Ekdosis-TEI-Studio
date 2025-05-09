# ==============================================================================
# Ekdosis-TEI Studio
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
from tkinter import filedialog
from tkinter import filedialog as fd, messagebox, scrolledtext, ttk, font, simpledialog
import difflib
from collections import defaultdict
import re
import unicodedata
import os
import sys
import math
import lxml.etree as ET
import lxml.etree as LET
import tempfile
import webbrowser
import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter.simpledialog import askinteger
from tkinter import Toplevel, Radiobutton, StringVar
import lxml.etree as LET
import os, webbrowser
from datetime import date
import locale


def importer_echantillon():
    exemple = """####1####
###1###
##Antiochus## ##Arsace##

#Antiochus#

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
***superbe & solitaire,
***superbe & solitaire,
***superbe & solitaire,
***superbe & solitaire,

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
Va, dis-je, et sans vouloir te charger d'autres soins,
Va, dis-je, et sans vouloir te charger d'autres soins;
Va, dis-je, et sans vouloir te charger d'autres soins?
Va, dis-je, et sans savoir te charger d'autres soins?

Voy si je puis bientost luy parler sans témoins.
Voy si je puis bientost luy parler sans témoins.
Voi si je puis bientost lui parler sans témoins.
Voi si je puis bientost luy parler sans témoins.

###2###
##Antiochus##
#Antiochus#
HE bien, Antiochus, es-tu toûjours le mesme ?
HE bien, Antiochus, es-tu toûjours le mesme ?
HE bien, Antiochus, es-tu toûjours le mesme ?
HE bien, Antiochus, es-tu toûjours le mesme ?

Voy si je puis bientost luy parler sans témoins.
Voy si je puis bientost luy parler sans témoins.
Voi si je puis bientost lui parler sans témoins.
Voi si je puis bientost luy parler sans témoins.

###3###
##Antiochus##, ##Titus##, ##Bérénice##
#Bérénice#
Dans un mois, dans un an comment souffrirons-nous
Dans un mois, dans un an, comment souffrirons-nous
Dans un mois dans un an comment souffrirons-nous
Dans un mois, dans un an comment souffrirez-vous

Seigneur que tant de mers me séparent de vous
Seigneur que tant de mers me séparent de nous
Seigneur, que tant de mers me séparent de vous
Seigneur que tant de mers me séparent de vous

Que le jour recommance et que le jours finisse
Que le jour recommence et que le jours finisse
Que le jour recommence et que le jours finisse
Que le jour recommence et que le jours finisse

Sans que jamais Titus puisse voir Bérénice
Sans que jamais Titus puisse voir Bérénice
Sans que jamais Titus puisse voir Bérénice
Sans que jamais Titus puisse voir Bérénice

Sans que de tour le jour je puisse voir Titus.
Sans que de tour le jour je puisse voir Titus.
Sans que de tour le jour je puisse voir Titus.
Sans que de tour le jour, je puisse voir Titus!"""

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
    \SetLineation{
    %   modulo,
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
    template_ekdosis_exemple_apparat = r"""
        \DeclareWitness{A}{1670}{Description de A}
        \DeclareWitness{B}{1671}{Description de B}
        \DeclareWitness{C}{1672}{Description de C}
        \DeclareWitness{D}{1673}{Description de D}
        """
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
        text = """Assistant pour l'encodage des variantes des textes de théâtre
        
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

def lancer_saisie_assistee(): # Menu principal de l'assistant de saisie
    global vers_num, numero_vers, flag_numero_vers
    fenetre = Toplevel()
    fenetre.title("Assistant de saisie")
    fenetre.configure(bg="#fdf6e3")
    fenetre.geometry("400x300")
    fenetre.grab_set()
    if flag_numero_vers != 1 :
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

    tk.Label(fenetre_scene, text="Personnages présents :", bg="#fdf6e3", font=("Garamond", 12)).pack(padx=10, pady=(10, 0))
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
    #DEBUG - MODE TEST NON BLOQUANT
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
    global vers_num, numero_vers
    #
    prenom_auteur = infos["Prénom de l'auteur"]
    nom_auteur = infos["Nom de l'auteur"]
    titre_piece = infos["Titre de la pièce"]
    numero_acte = infos["Numéro de l'acte"]
    numero_scene = infos["Numéro de la scène"]
    nombre_scenes = infos["Nombre de scènes dans l'acte"]
    vers_num = infos["Numéro du vers de départ"]
    vers_num=int(vers_num)
    entree_vers.delete(0, tk.END) # combobox
    entree_vers.insert(0, str(vers_num))
    numero_vers = vers_num # pour utilisation locale dans les boîtes de saisie
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

def collecter_temoins(nb_temoins):
    temoins = []
    for i in range(nb_temoins):
        donnees = demander_un_temoin_parchemin(i)
        if not donnees:
            return []  # pour ignorer
        temoins.append(donnees)
    return temoins

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


def echapper_caracteres_ekdosis(texte):
    """Échappe les caractères spéciaux ekdosis comme l’esperluette."""
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

        confirmer = messagebox.askyesno("Remplacer ?",
                                        f"Remplacer cette occurrence de « {terme} » par « {remplacement} » ?")
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

    temoins = collecter_temoins(nb_temoins)
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

    contenu_complet = (
            template_ekdosis_preamble +
            declarations_temoins +
            template_ekdosis_debut_doc +
            "\n" +
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
        with open(fichier, "w", encoding="utf-8") as f:
            f.write(contenu_complet)
        messagebox.showinfo("Succès", f"Fichier ekdosis enregistré :\n{fichier}")


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
    global auteur_nom_complet, editeur_nom_complet, titre_piece, numero_acte, numero_scene

    tei = zone_resultat_tei.get("1.0", tk.END).strip()
    if not tei:
        messagebox.showwarning("Avertissement", "Aucun contenu TEI à prévisualiser.")
        return

    reponse = messagebox.askyesno("Apparat critique",
                                  "Souhaitez-vous préciser les métadonnées des témoins pour l'apparat critique ?")
    temoins_dict = {}

    if reponse:
        try:
            temoins = collecter_temoins(int(nombre_temoins_predefini))
            temoins_dict = {t["abbr"]: t["year"] for t in temoins}
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
                                   "{http://www.tei-c.org/ns/1.0}credit").text = "Document généré le " + date.today().strftime(
                        "%d %B %Y")

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
          .acte, .scene, .personnages {
            font-weight: bold;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            margin-left: 11em;
          }
          .titre-piece {
            font-style: italic;
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
        <xsl:apply-templates select="tei:text"/>
      </body>
    </html>
  </xsl:template>

<xsl:template match="tei:seg">
  <xsl:apply-templates/>
</xsl:template>

  <!-- Acte -->
  <xsl:template match="tei:div[@type='act']">
    <div class="acte">ACTE <xsl:value-of select="@n"/></div>
    <xsl:apply-templates/>
  </xsl:template>

  <!-- Titre de scène -->
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
                dialogues.append(
                    (current_acte, current_scene, current_personnages, current_speaker, "\n".join(current_bloc)))
                current_bloc = []
            current_acte = re.findall(r"\d+", ligne)[0]
            current_scene = None
            current_personnages = []

        elif re.match(r"\#\#\#\d+\#\#\#", ligne):  # Scène
            if current_bloc and current_speaker:
                dialogues.append(
                    (current_acte, current_scene, current_personnages, current_speaker, "\n".join(current_bloc)))
                current_bloc = []
            current_scene = re.findall(r"\d+", ligne)[0]
            current_personnages = []

        elif re.match(r"(\#\#[^#]+\#\#)+", ligne):  # Personnages
            personnages = re.findall(r"\#\#([^\#\#]+)\#\#", ligne)
            current_personnages.extend(personnages)

        elif ligne.startswith("#") and ligne.endswith("#"):  # Locuteur
            if current_bloc and current_speaker:
                dialogues.append(
                    (current_acte, current_scene, current_personnages, current_speaker, "\n".join(current_bloc)))
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

    # Valeurs par défaut pour le header
    titre = globals().get("titre_piece", "").strip() or "Titre non renseigné"
    auteur = globals().get("auteur_nom_complet", "").strip() or "Auteur inconnu"
    editeur = globals().get("editeur_nom_complet", "").strip() or "Éditeur scientifique inconnu"
    acte = globals().get("numero_acte", "").strip() or "?"
    scene = globals().get("numero_scene", "").strip() or "?"

    # Construction sécurisée du header TEI
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
        f'       <date>{date.today().strftime("%d %B %Y")}</date>',
        '      </publicationStmt>',
        '      <sourceDesc>',
        f'        <p>généré par Ekdosis-TEI Studio – Acte {acte}, Scène {scene}</p>',
        '      </sourceDesc>',
        '    </fileDesc>',
        '  </teiHeader>',
        '  <text>',
        '    <body>'
    ]

    resultat_ekdosis = []

    vers_courant = numero_depart
    current_acte_out = None
    current_scene_out = None
    dernier_locuteur = None

    for acte, scene, personnages, speaker, bloc in dialogues:
        if acte != current_acte_out:
            if current_acte_out is not None:
                resultat_tei.append("  </div>")
                resultat_tei.append("</div>")
                resultat_ekdosis.append("% Fin de la scène")
                resultat_ekdosis.append("% Fin de l'acte")

            current_acte_out = acte
            num, titre = extraire_numero_et_titre(acte)

            # TEI
            resultat_tei.append(f'<div type="act" n="{num}">')

            # ekdosis ekdosis-compatible
            resultat_ekdosis.append(f'\\ekddiv{{head=ACTE {titre.upper()}, type=act, n={num}, depth=2}}\n')

            current_scene_out = None

        if scene != current_scene_out:
            if current_scene_out is not None:
                resultat_tei.append("  </sp>")
                resultat_tei.append("  </div>")
                resultat_ekdosis.append("      \\end{ekdverse}\n    \\end{speech}   % Fin de la scène")

            current_scene_out = scene
            dernier_locuteur = None  # ← 🎯 AJOUT ICI

            # TEI
            resultat_tei.append(f'  <div type="scene" n="{scene}">\n    <head>Scène {scene}</head>')

            # ekdosis ekdosis-compatible
            resultat_ekdosis.append(f'\\ekddiv{{head=Scène {scene}, type=scene, n={scene}, depth=3}}\n')

            if personnages:
                pers_tei = formatter_persname_tei(personnages)
                pers_ekdosis = formatter_persname_ekdosis(personnages)
                resultat_tei.append(f'    <stage>{pers_tei}.</stage>')
                resultat_ekdosis.append(f'    \\stage{{{pers_ekdosis}}}')

        sous_blocs = bloc.split("\n\n")
        if speaker != dernier_locuteur:
            if dernier_locuteur is not None:
                resultat_tei.append("    </sp>")
                resultat_ekdosis.append("      \\end{ekdverse}\n    \\end{speech}")
            resultat_tei.append(f'    <sp>\n      <speaker>{speaker}</speaker>')
            resultat_ekdosis.append("    \\begin{speech}\n      \\speaker{" + speaker + "}\n      \\begin{ekdverse}")
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
                resultat_ekdosis.append(f'        \\didas{{{didascalie}}}')
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
                ligne_ekdosis = []
                segment_buffer = []
                i = 0
                while i < len(base_1):
                    matching_apps = [key for key in differences.keys() if key[0] == i]
                    if matching_apps:
                        if segment_buffer:
                            segment_texte = " ".join(segment_buffer)
                            ligne_tei.append("      " + encoder_caracteres_tei(segment_texte) + "\n")
                            ligne_ekdosis.append("      " + echapper_caracteres_ekdosis(segment_texte))
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
                            f'        \\rdg[wit={{{", ".join(liste_temoins)}}}]{{{echapper_caracteres_ekdosis(texte_rdg)}}}'
                            for texte_rdg, liste_temoins in rdgs.items() if texte_rdg != lem
                        ]
                        ekdosis_block = [f'      \\app{{',
                                         f'        \\lem[wit={{{", ".join(wit_lem)}}}]{{{echapper_caracteres_ekdosis(lem)}}}']
                        ekdosis_block.extend(rdg_blocks)
                        ekdosis_block.append('      }')
                        ligne_ekdosis.append("\n".join(ekdosis_block))

                        i = end
                    else:
                        segment_buffer.append(base_1[i])
                        i += 1

                if segment_buffer:
                    segment_texte = " ".join(segment_buffer)
                    ligne_tei.append("      " + encoder_caracteres_tei(segment_texte) + "\n")
                    ligne_ekdosis.append("      " + echapper_caracteres_ekdosis(segment_texte))

                resultat_tei.append(f'<l n="{vers_num_1}">\n' + "".join(ligne_tei) + '</l>')
                vers_formate_1 = "\n".join(ligne_ekdosis)
                # à supprimer
                # resultat_ekdosis.append("      \\end{ekdverse}\n    \\end{speech}")
                # resultat_ekdosis.append(f'    \\begin{{speech}}\n      \\speaker{{{speaker}}}\n      \\begin{{ekdverse}}')
                resultat_ekdosis.append(
                    f'        \\vnum{{{vers_num_1}}}' + '{\n' + vers_formate_1 + '\\\\    \n         }')

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
                    ligne_ekdosis = []
                    segment_buffer = []
                    i = 0
                    while i < len(base_2):
                        matching_apps = [key for key in differences.keys() if key[0] == i]
                        if matching_apps:
                            if segment_buffer:
                                segment_texte = " ".join(segment_buffer)
                                ligne_tei.append("      " + encoder_caracteres_tei(segment_texte) + "\n")
                                ligne_ekdosis.append("      " + echapper_caracteres_ekdosis(segment_texte))
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
                                f'        \\rdg[wit={{{", ".join(liste_temoins)}}}]{{{echapper_caracteres_ekdosis(texte_rdg)}}}'
                                for texte_rdg, liste_temoins in rdgs.items() if texte_rdg != lem
                            ]
                            ekdosis_block = [f'      \\app{{',
                                             f'        \\lem[wit={{{", ".join(wit_lem)}}}]{{{echapper_caracteres_ekdosis(lem)}}}']
                            ekdosis_block.extend(rdg_blocks)
                            ekdosis_block.append('      }')
                            ligne_ekdosis.append("\n".join(ekdosis_block))

                            i = end
                        else:
                            segment_buffer.append(base_2[i])
                            i += 1

                    if segment_buffer:
                        segment_texte = " ".join(segment_buffer)
                        ligne_tei.append("      " + encoder_caracteres_tei(segment_texte) + "\n")
                        ligne_ekdosis.append("      " + echapper_caracteres_ekdosis(segment_texte))

                    # Gérer le changement de locuteur uniquement si nécessaire
                    if speaker_suivant != dernier_locuteur:
                        resultat_tei.append("    </sp>\n    <sp>\n      <speaker>{}</speaker>".format(speaker_suivant))
                        resultat_ekdosis.append("      \\end{ekdverse}\n    \\end{speech}")
                        resultat_ekdosis.append(
                            f'    \\begin{{speech}}\n      \\speaker{{{speaker_suivant}}}\n      \\begin{{ekdverse}}')
                        dernier_locuteur = speaker_suivant  # 🔄 mise à jour

                    # Ajout du vers 2
                    resultat_tei.append(f'<l n="{vers_num_2}">\n' + "".join(ligne_tei) + '</l>')

                    vers_formate_2 = "\n".join(ligne_ekdosis)
                    resultat_ekdosis.append(
                        f'        \\vnum{{{vers_num_2}}}' + '{\n' + '\\hspace*{10em}' + vers_formate_2 + '\\\\    \n         }')

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
            ligne_ekdosis = []
            segment_buffer = []

            i = 0
            while i < len(base):
                matching_apps = [key for key in differences.keys() if key[0] == i]
                if matching_apps:
                    if segment_buffer:
                        segment_texte = " ".join(segment_buffer)
                        ligne_tei.append("      " + encoder_caracteres_tei(segment_texte) + "\n")
                        ligne_ekdosis.append("      " + echapper_caracteres_ekdosis(segment_texte))
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
                    tei_app.append(
                        f'        <lem wit="{" ".join(f"#{t}" for t in wit_lem)}">{encoder_caracteres_tei(lem)}</lem>\n')
                    for texte_rdg, liste_temoins in rdgs.items():
                        if texte_rdg != lem:
                            wits = " ".join(f"#{t}" for t in liste_temoins)
                            tei_app.append(f'        <rdg wit="{wits}">{encoder_caracteres_tei(texte_rdg)}</rdg>\n')
                    tei_app.append(f'      </app>\n')
                    ligne_tei.extend(tei_app)

                    rdg_blocks = []
                    for texte_rdg, liste_temoins in rdgs.items():
                        if texte_rdg != lem:
                            rdg_blocks.append(
                                f'        \\rdg[wit={{{", ".join(liste_temoins)}}}]{{{echapper_caracteres_ekdosis(texte_rdg)}}}')
                    ekdosis_block = [f'      \\app{{',
                                     f'        \\lem[wit={{{", ".join(wit_lem)}}}]{{{echapper_caracteres_ekdosis(lem)}}}']
                    ekdosis_block.extend(rdg_blocks)
                    ekdosis_block.append('      }')
                    ligne_ekdosis.append("\n".join(ekdosis_block))

                    i = end
                else:
                    segment_buffer.append(base[i])
                    i += 1

            if segment_buffer:
                segment_texte = " ".join(segment_buffer)
                ligne_tei.append("      " + encoder_caracteres_tei(segment_texte) + "\n")
                ligne_ekdosis.append("      " + echapper_caracteres_ekdosis(segment_texte))

            resultat_tei.append(f'<l n="{vers_courant}">\n' + "".join(ligne_tei) + '</l>\n')
            vers_formate = "\n".join(ligne_ekdosis)
            resultat_ekdosis.append(f"        \\vnum{{{vers_courant}}}{{\n{vers_formate}  \\\\    \n        }}")
            if vers_courant == int(vers_courant):
                vers_courant += 1
            else:
                vers_courant = math.ceil(vers_courant)

        if dernier_locuteur != speaker:
            resultat_tei.append("    </sp>")
            resultat_ekdosis.append("      \\end{ekdverse}\n    \\end{speech}")

    if current_scene_out:
        resultat_tei.append("    </sp>")
        resultat_tei.append("    </div>")
        resultat_ekdosis.append("      \\end{ekdverse}\n    \\end{speech}   % Fin de la scène")

    if current_acte_out is not None:
        resultat_tei.append("</div>")
        resultat_ekdosis.append("% Fin de l'acte")

    zone_resultat_tei.delete("1.0", tk.END)

    resultat_tei.append('</body></text>')
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

menu_fichier.add_command(label="Réinitialiser la saisie", command=reset_application)
menu_fichier.add_command(label="Charger un échantillon de test", command=importer_echantillon)
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

# --- Menu Outils ---
menu_outils = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Outils", menu=menu_outils)

menu_outils.add_command(label="Lancer l’assistant de saisie", command=lancer_saisie_assistee_par_menu)
menu_outils.add_command(label="Valider la structure", command=valider_structure)
menu_outils.add_command(label="Comparer les états", command=comparer_etats)

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
fenetre.bind("<Control-f>", lambda e: rechercher())
fenetre.bind("<Control-h>", lambda e: remplacer_avance())

afficher_nagscreen()

frame_saisie = tk.LabelFrame(fenetre, text="Saisie des variantes", padx=10, pady=5, bg="#f4f4f4")
frame_saisie.pack(fill=tk.BOTH, padx=10, pady=10)

label_texte = tk.Label(frame_saisie,
                       text="Utilisez ####a#### pour un acte, ###n### pour une scène, ##Nom## pour les personnages, et #Nom# pour le locuteur :",
                       bg="#f4f4f4")
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

btn_comparer = tk.Button(frame_bas, text="générer code", command=comparer_etats)
btn_comparer.pack(side=tk.LEFT, padx=10)

btn_export_tei = tk.Button(frame_bas, text="💾 Exporter TEI", command=exporter_tei)
btn_export_tei.pack(side=tk.LEFT, padx=10)

btn_export_ekdosis = tk.Button(frame_bas, text="💾 Exporter ekdosis", command=exporter_ekdosis)
btn_export_ekdosis.pack(side=tk.LEFT, padx=10)

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
entree_vers.insert(0, "1") # valeur temporaire par défaut
entree_vers.pack(side=tk.LEFT)

notebook = ttk.Notebook(fenetre)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# TEI
onglet_tei = tk.Frame(notebook, bg="white")
zone_resultat_tei = scrolledtext.ScrolledText(onglet_tei, height=15, undo=True, maxundo=-1)
zone_resultat_tei.pack(fill=tk.BOTH, expand=True)
notebook.add(onglet_tei, text="🧾 TEI")

# ekdosis
onglet_ekdosis = tk.Frame(notebook, bg="white")
zone_resultat_ekdosis = scrolledtext.ScrolledText(onglet_ekdosis, height=15, undo=True, maxundo=-1)
zone_resultat_ekdosis.pack(fill=tk.BOTH, expand=True)
notebook.add(onglet_ekdosis, text="📘 ekdosis")

# HTML
onglet_html = tk.Frame(notebook, bg="white")
zone_resultat_html = scrolledtext.ScrolledText(onglet_html, height=15, undo=True, maxundo=-1, bg="white", fg="#4a3c1a",
                                               font=("Georgia", 11))
zone_resultat_html.pack(fill=tk.BOTH, expand=True)
notebook.add(onglet_html, text="🌐 html")

# appliquer_style_light(fenetre)
appliquer_style_parchemin(fenetre)

# --- Raccourcis clavier globaux ---
# Sans doute à effacer tous
fenetre.bind_all("<Control-a>", lambda event: fenetre.focus_get().event_generate('<<SelectAll>>'))
fenetre.bind_all("<Control-x>", lambda event: fenetre.focus_get().event_generate('<<Cut>>'))
fenetre.bind_all("<Control-c>", lambda event: fenetre.focus_get().event_generate('<<Copy>>'))
# fenetre.bind_all("<Control-v>", lambda event: fenetre.focus_get().event_generate('<<Paste>>'))


fenetre.mainloop()
