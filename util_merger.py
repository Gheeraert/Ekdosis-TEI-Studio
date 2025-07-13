import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from datetime import date
import locale

def roman_to_int(roman):
    roman = roman.strip().upper().replace("ACTE", "").strip()
    roman_dict = {
        'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
        'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10
    }
    if roman.isdigit():
        return roman
    return str(roman_dict.get(roman, roman))

def merge_acte_html():
    root = tk.Tk()
    root.withdraw()

    html_files = filedialog.askopenfilenames(
        title="Sélectionnez les fichiers HTML à fusionner",
        filetypes=[("Fichiers HTML", "*.html *.htm")]
    )
    if not html_files:
        return

    html_files = sorted(html_files, key=lambda x: os.path.basename(x).lower())

    titre = simpledialog.askstring("Titre de la pièce", "Entrez le titre de la pièce (ex : La Thébaïde ou les Frères ennemis):")
    if not titre:
        return
    acte = simpledialog.askstring("Numéro d'acte", "Entrez l’acte (ex : Acte I):")
    if not acte:
        return

    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    except:
        locale.setlocale(locale.LC_TIME, "")

    today_str = date.today().strftime("%d %B %Y")
    bloc_credit_perso = f'''
<div class="bloc-credit">

<div class="credit-line">Jean Racine – <span class="italic">{titre}</span>, acte {acte}</div>
<div class="credit-line">Édition critique par Claire Fourquet-Gracieux</div>
<div class="credit-line">Document généré le {today_str} depuis Ekdosis-TEI Studio</div>
</div>
'''

    num_acte = re.sub(r"Acte\s*", "", acte, flags=re.IGNORECASE).strip()
    num_acte = roman_to_int(num_acte)
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

        # Supprime TOUS les <style>...</style> PARTOUT AVANT TOUT TRAITEMENT
        content = re.sub(r'<style.*?>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        # Enlève balises fermantes partout
        content = re.sub(r'</body>\s*</html>\s*$', '', content, flags=re.IGNORECASE)

        if idx == 0:
            # Isole le pré-body pour le premier fichier
            parts = re.split(r'(<body[^>]*>)', content, maxsplit=1, flags=re.IGNORECASE | re.DOTALL)
            if len(parts) < 3:
                messagebox.showerror("Erreur", "Impossible de repérer le <body> dans le premier fichier.")
                return
            pre_body = parts[0] + parts[1]

            # Ajoute le lien Google Fonts tout en haut du <head>
            google_fonts_line = '<link href="https://fonts.googleapis.com/css2?family=Old+Standard+TT:wght@400;700&display=swap" rel="stylesheet">\n'
            pre_body = re.sub(r'(<head[^>]*>)', r'\1\n' + google_fonts_line, pre_body, count=1, flags=re.IGNORECASE)

            merged.append(pre_body)
            body_inside = parts[2]
            # Ajoute le <link> vers css après suppression du style
            body_inside = re.sub(
                r'<link rel="stylesheet" href="../../../css/edition.css">',
                '', body_inside, flags=re.IGNORECASE
            )
            body_inside = '<link rel="stylesheet" href="../../../css/edition.css">\n' + body_inside

            # Supprime toutes les lignes avec les classes à virer
            lines = body_inside.splitlines()
            filtered_lines = [line for line in lines if not (
                'bloc-credit' in line or 'logo-credit' in line or 'credit-line' in line
            )]
            # Ajoute le bloc crédit en tête
            merged.append(bloc_credit_perso + "\n" + "\n".join(filtered_lines))
        else:
            # Supprime toutes les lignes avec les classes à virer dans les autres fichiers
            content = re.sub(r'<\/?body[^>]*>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'<\/?html[^>]*>', '', content, flags=re.IGNORECASE)
            lines = content.splitlines()
            filtered_lines = [line for line in lines if not (
                'bloc-credit' in line or 'logo-credit' in line or 'credit-line' in line
            )]
            merged.append("\n".join(filtered_lines))

    merged.append("\n</body>\n</html>")

    with open(save_path, 'w', encoding='utf-8') as f:
        f.write("".join(merged))

    messagebox.showinfo("Succès", f"Acte fusionné enregistré sous :\n{save_path}")

if __name__ == "__main__":
    merge_acte_html()
