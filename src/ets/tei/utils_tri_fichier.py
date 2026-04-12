import tkinter as tk
from tkinter import filedialog
import os


def fusionner_fichiers():
    # Initialiser Tkinter et masquer la fenêtre principale
    root = tk.Tk()
    root.withdraw()

    # 1. Ouvrir la boîte de dialogue pour sélectionner les fichiers
    fichiers_selectionnes = filedialog.askopenfilenames(
        title="Sélectionnez les fichiers .txt ou .md à fusionner",
        filetypes=[("Fichiers Texte et Markdown", "*.txt *.md"), ("Tous les fichiers", "*.*")]
    )

    # Vérifier si l'utilisateur a annulé la sélection
    if not fichiers_selectionnes:
        print("Opération annulée : aucun fichier sélectionné.")
        return

    # 2. Trier les fichiers dans l'ordre alphabétique de leurs noms
    # os.path.basename permet de trier sur le nom du fichier ("b.txt") et non sur le chemin complet ("C:/dossier/b.txt")
    fichiers_tries = sorted(fichiers_selectionnes, key=lambda chemin: os.path.basename(chemin).lower())

    # 3. Demander où sauvegarder le fichier final
    fichier_sortie = filedialog.asksaveasfilename(
        title="Enregistrer le fichier fusionné sous...",
        defaultextension=".txt",
        filetypes=[("Fichier Texte", "*.txt"), ("Fichier Markdown", "*.md"), ("Tous les fichiers", "*.*")]
    )

    if not fichier_sortie:
        print("Opération annulée : aucune destination choisie.")
        return

    # 4. Fusionner les contenus
    try:
        with open(fichier_sortie, 'w', encoding='utf-8') as outfile:
            for chemin_fichier in fichiers_tries:
                nom_fichier = os.path.basename(chemin_fichier)

                # Optionnel : Ajouter un séparateur visuel avec le nom du fichier
                # outfile.write(f"\n\n{'=' * 40}\n")
                # outfile.write(f"--- Contenu de : {nom_fichier} ---\n")
                # outfile.write(f"{'=' * 40}\n\n")

                #Lire le contenu du fichier courant et l'écrire dans le fichier de sortie
                with open(chemin_fichier, 'r', encoding='utf-8') as infile:
                    contenu = infile.read()
                    outfile.write(contenu)

        print(f"✅ Fusion terminée avec succès !")
        print(f"Le fichier a été sauvegardé ici : {fichier_sortie}")

    except Exception as e:
        print(f"❌ Une erreur s'est produite lors de la fusion : {e}")


if __name__ == "__main__":
    fusionner_fichiers()