import os
import re
from tkinter import Tk, filedialog, messagebox

def merge_tei_by_regex():
    # Masquer la fenêtre principale
    root = Tk()
    root.withdraw()

    # 1. Choix des fichiers et tri alphabétique
    files = filedialog.askopenfilenames(
        title="Sélectionnez vos TEI à fusionner",
        filetypes=[("TEI XML", "*.xml"), ("Tous fichiers", "*.*")]
    )
    if not files:
        return
    files = sorted(files, key=lambda p: os.path.basename(p).lower())

    # 2. Lire tous les fichiers en mémoire
    docs = []
    for path in files:
        try:
            with open(path, encoding="utf-8") as f:
                docs.append(f.read())
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire {path} :\n{e}")
            return

    # 3. Préparer nos patterns
    body_open_re  = re.compile(r'^(.*?<body[^>]*>)', re.DOTALL|re.IGNORECASE)
    body_close_re = re.compile(r'(</body>.*)$', re.DOTALL|re.IGNORECASE)
    body_content_re = re.compile(r'<body[^>]*>(.*?)</body>', re.DOTALL|re.IGNORECASE)

    # 4. Extraire header, footer et contenu du premier
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

    # 5. Pour chaque fichier suivant, extraire juste ce qui est entre <body> et </body>
    for idx, doc in enumerate(docs[1:], start=2):
        m = body_content_re.search(doc)
        if not m:
            messagebox.showerror("Erreur", f"Fichier n°{idx} : pas de <body>…</body> trouvé.")
            return
        bodies.append(m.group(1))

    # 6. Concaténer et proposer d'enregistrer
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

    messagebox.showinfo("Succès", f"TEI fusionné enregistré sous :\n{save_path}")

if __name__ == "__main__":
    merge_tei_by_regex()
