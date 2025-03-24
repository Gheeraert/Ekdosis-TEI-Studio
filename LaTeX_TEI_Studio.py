# ==============================================================================
# TEILaTeXStudio
# Un outil d'encodage TEI et LaTeX des variantes dans le théâtre classique
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
import difflib
from collections import defaultdict
import re
import unicodedata

def afficher_nagscreen():
    nag = tk.Toplevel(fenetre)
    nag.title("Bienvenue dans TEILaTeXStudio")
    nag.configure(bg="#f5f0e6")

    largeur_nag = 500
    hauteur_nag = 400
    fenetre.update_idletasks()
    x_main = fenetre.winfo_rootx()
    y_main = fenetre.winfo_rooty()
    w_main = fenetre.winfo_width()
    h_main = fenetre.winfo_height()
    x = x_main + (w_main - largeur_nag) // 2
    y = y_main + (h_main - hauteur_nag) // 2
    nag.geometry(f"{largeur_nag}x{hauteur_nag}+{x}+{y}")
    nag.grab_set()

    # Titre
    titre = tk.Label(nag, text="TEILaTeXStudio", font=("Georgia", 18, "bold"), bg="#f5f0e6")
    titre.pack(pady=10)

    # Logo
    try:
        logo = tk.PhotoImage(file="favicon.png")
        nag.logo_img = logo  # éviter garbage collector
        logo_label = tk.Label(nag, image=logo, bg="#f5f0e6")
        logo_label.pack(pady=(0, 10))
    except Exception as e:
        print("⚠️ Fichier favicon.png non trouvé, le logo ne sera pas affiché.")
        logo_label = tk.Label(nag, text="🧾", font=("Helvetica", 32), bg="#f5f0e6")
        logo_label.pack(pady=(0, 10))

    # Auteur
    auteur = tk.Label(nag, text="Développé par la Chaire d'Excellence en Editions numériques", font=("Georgia", 10), bg="#f5f0e6")
    auteur.pack(pady=5)

    # Texte explicatif
    intro = tk.Label(
        nag,
        text=(
            "Un outil d'encodage TEI et LaTeX des variantes dans le théâtre classique.\n\n"
            "- [[[[n]]]] pour un acte\n"
            "- [[[n]]] pour une scène\n"
            "- [[Nom]] pour les personnages présents\n"
            "- [Nom] pour indiquer un locuteur\n"
        ),
        font=("Georgia", 10), bg="#f5f0e6", justify="center"
    )
    intro.pack(pady=15)

    bouton = tk.Button(nag, text="Commencer", font=("Georgia", 11, "bold"), width=15,
                       command=nag.destroy)
    bouton.pack(pady=10)

def valider_structure_amelioree():
    texte = zone_saisie.get("1.0", tk.END).strip()
    lignes = texte.splitlines()

    erreurs = []
    ligne_actuelle = 0

    a_scene = False
    a_acte = False
    locuteur_attendu = False
    locuteur_en_cours = None

    for i, ligne in enumerate(lignes):
        ligne_actuelle = i + 1
        ligne = ligne.strip()

        # Crochets non fermés ou suspects
        if ligne.count("[") != ligne.count("]"):
            erreurs.append(f"Ligne {ligne_actuelle} : crochets non appariés.")

        # Acte
        if re.match(r"\[\[\[\[\d+\]\]\]\]", ligne):
            a_acte = True
            a_scene = False  # on attend une scène ensuite
            locuteur_attendu = False
            continue

        # Scène
        if re.match(r"\[\[\[\d+\]\]\]", ligne):
            if not a_acte:
                erreurs.append(f"Ligne {ligne_actuelle} : scène définie avant tout acte.")
            a_scene = True
            locuteur_attendu = False
            continue

        # Personnages présents
        if re.match(r"\[\[[^\[\]]+\]\]", ligne):
            if not a_scene:
                erreurs.append(f"Ligne {ligne_actuelle} : personnages présents en dehors d'une scène.")
            continue

        # Locuteur
        if ligne.startswith("[") and ligne.endswith("]") and not ligne.startswith("[["):
            if not a_scene:
                erreurs.append(f"Ligne {ligne_actuelle} : locuteur défini hors scène.")
            if locuteur_en_cours:
                erreurs.append(f"Ligne {ligne_actuelle} : locuteur '{locuteur_en_cours}' sans contenu avant nouveau locuteur.")
            locuteur_en_cours = ligne[1:-1].strip()
            locuteur_attendu = True
            continue

        # Contenu d'une tirade
        if ligne and locuteur_attendu:
            locuteur_attendu = False
            locuteur_en_cours = None

        # Ligne vide
        if not ligne:
            continue

        # Lignes ambiguës ?
        if "[" in ligne or "]" in ligne:
            if not (re.fullmatch(r"\[\[\[?\w[\w\s,-]*\]?\]\]?\]?", ligne)):
                erreurs.append(f"Ligne {ligne_actuelle} : crochets suspects ou mal fermés.")

    if not any(re.match(r"\[\[\[\[\d+\]\]\]\]", l.strip()) for l in lignes):
        erreurs.append("Aucun acte ([[[[n]]]]) n’est défini.")
    if not any(re.match(r"\[\[\[\d+\]\]\]", l.strip()) for l in lignes):
        erreurs.append("Aucune scène ([[[n]]]) n’est définie.")
    if not any(l.strip().startswith("[") and l.strip().endswith("]") and not l.startswith("[[") for l in lignes):
        erreurs.append("Aucun locuteur ([Nom]) n’est défini.")

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

nettoyer_identifiant("Bérénice (Reine)")

def echapper_caracteres_latex(texte):
    """Échappe les caractères spéciaux LaTeX comme l’esperluette."""
    return texte.replace("&", r"\&")

def encoder_caracteres_tei(texte):
    """Encode les caractères spéciaux XML/TEI comme l’esperluette."""
    return texte.replace("&", "&amp;")

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
    COULEUR_FOND = "#fdf6e3"         # Ivoire / parchemin
    COULEUR_ENCADRE = "#f5ebc4"      # Jaune parchemin pâle
    COULEUR_TEXTE = "#4a3c1a"        # Brun profond
    POLICE_SERIF = "Georgia"

    # Appliquer à la fenêtre principale
    fenetre.configure(bg=COULEUR_FOND)

    # Polices
    police_label = font.Font(family=POLICE_SERIF, size=11, weight="bold")
    police_zone = font.Font(family="Courier New", size=11)  # pour l'alignement des zones de texte
    police_bouton = font.Font(family=POLICE_SERIF, size=12, weight="bold")

    # Zones spécifiques à configurer si elles existent
    for widget in fenetre.winfo_children():
        if isinstance(widget, (tk.Label, tk.LabelFrame)):
            widget.configure(font=police_label, bg=COULEUR_ENCADRE, fg=COULEUR_TEXTE)
        elif isinstance(widget, tk.Frame):
            widget.configure(bg=COULEUR_FOND)

    try:
        zone_saisie.configure(bg="white", font=police_zone)
        zone_resultat_tei.configure(bg="white", font=police_zone)
        zone_resultat_latex.configure(bg="white", font=police_zone)
    except:
        pass

    try:
        for frame in [frame_bas]:
            for bouton in frame.winfo_children():
                if isinstance(bouton, tk.Button):
                    bouton.configure(
                        font=police_bouton,
                        bg=COULEUR_ENCADRE,
                        fg=COULEUR_TEXTE,
                        activebackground=COULEUR_TEXTE,
                        activeforeground="white",
                        relief="raised",
                        bd=2
                    )
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
        title="Enregistrer le fichier LaTeX"
    )
    if fichier:
        with open(fichier, "w", encoding="utf-8") as f:
            f.write(contenu)
        messagebox.showinfo("Succès", f"Fichier LaTeX enregistré :\n{fichier}")

def enregistrer_saisie():
    contenu = zone_saisie.get("1.0", tk.END).strip()
    if not contenu:
        messagebox.showwarning("Avertissement", "Aucune saisie à enregistrer.")
        return
    fichier = fd.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Fichiers texte", "*.txt")],
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

def comparer_etats():
    texte = zone_saisie.get("1.0", tk.END).strip()
    lignes = texte.splitlines()

    dialogues = []
    current_acte = None
    current_scene = None
    current_personnages = []
    current_speaker = None
    current_bloc = []

    for ligne in lignes:
        ligne = ligne.strip()

        if re.match(r"\[\[\[\[\d+\]\]\]\]", ligne):  # Acte
            if current_bloc and current_speaker:
                dialogues.append((current_acte, current_scene, current_personnages, current_speaker, "\n".join(current_bloc)))
                current_bloc = []
            current_acte = re.findall(r"\d+", ligne)[0]
            current_scene = None
            current_personnages = []

        elif re.match(r"\[\[\[\d+\]\]\]", ligne):  # Scène
            if current_bloc and current_speaker:
                dialogues.append((current_acte, current_scene, current_personnages, current_speaker, "\n".join(current_bloc)))
                current_bloc = []
            current_scene = re.findall(r"\d+", ligne)[0]
            current_personnages = []

        elif re.match(r"\[\[[^\[\]]+\]\]", ligne):  # Personnages
            personnages = re.findall(r"\[\[([^\[\]]+)\]\]", ligne)
            current_personnages.extend(personnages)

        elif ligne.startswith("[") and ligne.endswith("]"):  # Locuteur
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

    resultat_tei = []
    resultat_latex = []

    vers_courant = numero_depart
    current_acte_out = None
    current_scene_out = None

    for acte, scene, personnages, speaker, bloc in dialogues:
        if acte != current_acte_out:
            if current_acte_out is not None:
                resultat_tei.append("  </div>")
                resultat_tei.append("</div>")
                resultat_latex.append("  \\closescene{}\n\\end{scene}")
                resultat_latex.append("\\closeact{}\n\\end{act}")
            current_acte_out = acte
            num, titre = extraire_numero_et_titre(acte)
            resultat_tei.append(f'<div type="act" n="{num}">')
            resultat_latex.append(f'\\begin{{act}}\n  \\numact{{{num}}}\n  \\acthead{{Acte {titre}}}')

            current_scene_out = None

        if scene != current_scene_out:
            if current_scene_out is not None:
                resultat_tei.append("  </div>")
                resultat_latex.append("  \\closescene{}\n\\end{scene}")
            current_scene_out = scene
            resultat_tei.append(f'  <div type="scene" n="{scene}">\n    <head>Scène {scene}</head>')
            resultat_latex.append(f'  \\begin{{scene}}\n    \\numscene{{{scene}}}\n    \\scenehead{{Scène {scene}}}')
            if personnages:
                pers_tei = formatter_persname_tei(personnages)
                pers_latex = formatter_persname_latex(personnages)
                resultat_tei.append(f'    <stage>{pers_tei}.</stage>')
                resultat_latex.append(f'    \\stage{{{pers_latex}}}')

        sous_blocs = bloc.split("\n\n")
        resultat_tei.append(f'    <sp>\n      <speaker>{speaker}</speaker>')
        resultat_latex.append("    \\begin{speech}\n      \\speaker{" + speaker + "}\n      \\begin{vers}")

        for sous_bloc in sous_blocs:
            lignes = [l.strip() for l in sous_bloc.strip().splitlines() if l.strip()]

            # Si c'est une didascalie seule
            if len(lignes) == 1 and lignes[0].startswith("<<") and lignes[0].endswith(">>"):
                didascalie = lignes[0][2:-2].strip()
                resultat_tei.append(f'      <stage>{didascalie}</stage>')
                resultat_latex.append(f'        \\didas{{{didascalie}}}')
                continue

            # Sinon, ignorer les lignes uniques non didascaliques
            if len(lignes) < 2:
                continue

            temoins = [chr(65 + i) for i in range(len(lignes))]
            # Si c'est une didascalie isolée
            if len(lignes) == 1 and lignes[0].startswith("<<") and lignes[0].endswith(">>"):
                didascalie = lignes[0][2:-2].strip()
                resultat_tei.append(f'      <stage>{encoder_caracteres_tei(didascalie)}</stage>')
                resultat_latex.append(f'        \\didas{{{echapper_caracteres_latex(didascalie)}}}')
                continue  # ne pas traiter comme vers
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
            resultat_latex.append(f"        \\vnum{{{vers_courant}}}{{\n{vers_formate}\n        }}")
            vers_courant += 1

        resultat_tei.append("    </sp>")
        resultat_latex.append("      \\end{vers}\n    \\end{speech}")

    if current_scene_out:
        resultat_tei.append("  </div>")
        resultat_latex.append("  \\closescene{}\n\\end{scene}")
    if current_acte_out:
        resultat_tei.append("</div>")
        resultat_latex.append("\\closeact{}\n\\end{act}")

    zone_resultat_tei.delete("1.0", tk.END)
    zone_resultat_tei.insert(tk.END, "\n".join(resultat_tei) + "\n")

    zone_resultat_latex.delete("1.0", tk.END)
    zone_resultat_latex.insert(tk.END, "\n".join(resultat_latex) + "\n")

def mettre_a_jour_menu(*args):
    texte = zone_saisie.get("1.0", tk.END).strip()
    lignes = [l.strip() for l in texte.splitlines() if l.strip() and not l.startswith("[")]
    menu_ref["values"] = [chr(65 + i) for i in range(len(lignes))]
    if lignes:
        liste_ref.current(0)

def convertir_tei_en_html(tei_text):
    html = []
    for ligne in tei_text.splitlines():
        ligne = ligne.strip()

        # Acte
        match_acte = re.match(r'<div type="act" n="(\d+)">', ligne)
        if match_acte:
            html.append(f'<h2>Acte {match_acte.group(1)}</h2>')
            continue

        # Scène
        match_scene = re.match(r'<div type="scene" n="(\d+)">', ligne)
        if match_scene:
            html.append(f'<h3>Scène {match_scene.group(1)}</h3>')
            continue

        # Titre de scène
        if ligne.startswith("<head>"):
            html.append(f"<h4>{re.sub(r'</?head>', '', ligne).strip()}</h4>")
            continue

        # Didascalie
        if "<stage>" in ligne:
            texte = re.sub(r'</?stage>', '', ligne).strip()
            html.append(f"<p><em>{texte}</em></p>")
            continue

        # Locuteur
        if "<speaker>" in ligne:
            locuteur = re.sub(r'</?speaker>', '', ligne).strip()
            html.append(f"<p><strong>{locuteur} :</strong>")
            continue

        # Vers
        match_vers = re.match(r'<l n="(\d+)">(.+?)</l>', ligne)
        if match_vers:
            vers = re.sub(r'<[^>]+>', '', match_vers.group(2)).strip()
            html.append(f"{vers}<br>")
            continue

        # Par défaut : on ignore les autres balises
    html.append("</p>")  # fermer la dernière tirade
    return "\n".join(html)


def afficher_aide():
    exemple = r"""
Structure attendue :

[[[[1]]]]             → Acte I
[[[1]]]              → Scène 1
[[Titus]] [[Bérénice]] → Personnages présents
[Titus]             → Locuteur (début de tirade)
Texte du vers 1
Texte du vers 2

[Bérénice]
Texte du vers 1
Texte du vers 2

Les états (témoins A, B, C…) doivent être saisis ligne à ligne à chaque vers.
Laissez une ligne vide pour séparer les variantes d’un nouveau vers.

Exemple:

[[[[1]]]]
[[[1]]]
[[Antiochus]] [[Arsace]]
[Antiochus]
Arrestons un moment. La pompe de ces lieux
Arrestons un moment. La pompe de ces lieux
Arrestons un moment. La pompe de ces lieux
Arrestons un moment. La pompe de ces lieux

Je le voy bien, Arsace, est nouvelle à tes yeux
Je le voy bien, Arsace, est nouvelle à tes yeux
Je le vois bien, Arsace, est nouvelle à tes yeux
Je le vois bien, Arsace, est nouvelle à tes yeux

"""
    messagebox.showinfo("Aide à la transcription", exemple)

# Interface tkinter
fenetre = tk.Tk()
#fenetre.iconbitmap("favicon.ico")
fenetre.title("Comparateur avec scènes, personnages et locuteurs")
fenetre.update_idletasks()
fenetre.minsize(1000, fenetre.winfo_reqheight())
fenetre.bind_all("<Control-s>", lambda event: enregistrer_saisie())

afficher_nagscreen()

frame_saisie = tk.LabelFrame(fenetre, text="Saisie des variantes", padx=10, pady=5, bg="#f4f4f4")
frame_saisie.pack(fill=tk.BOTH, padx=10, pady=10)

label_texte = tk.Label(frame_saisie, text="Utilisez [[[[a]]]] pour un acte, [[[n]]] pour une scène, [[Nom]] pour les personnages, et [Nom] pour le locuteur :", bg="#f4f4f4")
label_texte.pack()

zone_saisie = scrolledtext.ScrolledText(frame_saisie, height=15, undo=True, maxundo=-1)
zone_saisie.pack(fill=tk.BOTH, expand=True)
zone_saisie.bind("<KeyRelease>", mettre_a_jour_menu)

frame_params = tk.LabelFrame(fenetre, text="Paramètres", padx=10, pady=5, bg="#f4f4f4")
frame_params.pack(fill=tk.X, padx=10, pady=10)

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
#onglet_html = tk.Frame(notebook, bg="white")
#zone_resultat_html = scrolledtext.ScrolledText(onglet_html, height=15, undo=True, maxundo=-1)
#zone_resultat_html.pack(fill=tk.BOTH, expand=True)
#notebook.add(onglet_html, text="🌐 HTML")


frame_bas = tk.Frame(fenetre)
frame_bas.pack(pady=10)

btn_comparer = tk.Button(frame_bas, text="Comparer et générer", command=comparer_etats)
btn_comparer.pack(side=tk.LEFT, padx=10)

btn_export_tei = tk.Button(frame_bas, text="💾 Exporter TEI", command=exporter_tei)
btn_export_tei.pack(side=tk.LEFT, padx=10)

btn_export_latex = tk.Button(frame_bas, text="💾 Exporter LaTeX", command=exporter_latex)
btn_export_latex.pack(side=tk.LEFT, padx=10)

btn_sauver_saisie = tk.Button(frame_bas, text="💾 Enregistrer la saisie", command=enregistrer_saisie)
btn_sauver_saisie.pack(side=tk.LEFT, padx=10)

btn_quitter = tk.Button(frame_bas, text="Quitter", command=confirmer_quitter)
ajouter_bouton_validation(frame_bas)
btn_aide = tk.Button(frame_bas, text="❔ Aide", command=afficher_aide)
btn_aide.pack(side=tk.LEFT, padx=10)
btn_quitter.pack(side=tk.RIGHT, padx=10)

#appliquer_style_light(fenetre)
appliquer_style_parchemin(fenetre)
fenetre.mainloop()
