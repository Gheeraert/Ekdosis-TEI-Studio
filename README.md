# 🧾 TEILaTeXStudio

**TEILaTeXStudio** est un outil d'encodage **TEI XML** et **LaTeX ekdosis** des variantes dans le théâtre classique, avec gestion des actes, scènes, personnages, locuteurs, vers et variantes textuelles ligne à ligne. Développé avec Python et Tkinter, il s'adresse aux chercheurs et éditeurs critiques travaillant sur les textes dramatiques anciens.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![TEI](https://img.shields.io/badge/Format-TEI%20XML-ffcc00)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-En%20cours%20de%20développement-orange)

---

## ✨ Fonctionnalités principales

- 🏛 Saisie encodée structurée : actes, scènes, personnages, locuteurs, tirades
- 🔀 Comparaison automatique de variantes ligne à ligne (difflib)
- 🔎 Génération parallèle des résultats en :
  - **TEI XML** avec balises `<app>`, `<lem>`, `<rdg>`, `<stage>`, etc.
  - **LaTeX** compatible avec le package `ekdosis`
- 🎭 Gestion des didascalies : format `<<texte>>` reconnu et encodé en `<stage>` / `\didas{}`
- 🔤 Échappement automatique des caractères spéciaux (`&`, etc.)
- 🧑‍🎓 Interface conviviale en Tkinter avec onglets TEI / LaTeX
- 🧪 Validation de structure intégrée (actes, scènes, locuteurs)
- 🎨 Style visuel "parchemin" pour une expérience élégante

---

## 🖋️ Exemple de saisie

```
[[[[1]]]]
[[[1]]]
[[Antiochus]] [[Arsace]]
[Antiochus]

<<Antiochus entre.>>

Arrestons un moment. La pompe de ces lieux
Arrestons un moment. La pompe de ces lieux
Arrestons un moment. La pompe de ces lieux
Arrestons un moment. La pompe de ces lieux

Je le vois bien, Arsace, est nouvelle à tes yeux
Je le voy bien, Arsace, est nouvelle à tes yeux
Je le vois bien, Arsace, est nouvelle à tes yeux
Je le voy bien, Arsace, est nouvelle à tes yeux
```

---

## 🚀 Lancer l'application

Assurez-vous d'avoir Python 3.9+ installé.

```bash
python TEILaTeXStudio.py
```

---

## 📦 Dépendances

- Python standard (`tkinter`, `difflib`, `re`, etc.)
- Aucune installation externe nécessaire

---

## 🧪 En projet

- Export HTML simple
- Prise en compte des variantes de didascalies
- Encodage de scènes muettes
- Génération directe en PDF via XeLaTeX (optionnel)

---

## 🤝 Contribuer

Suggestions, pull requests ou retours bienvenus !  
Créez une [issue](https://github.com/ton-nom-utilisateur/TEILaTeXStudio/issues) ou proposez une amélioration.

---

## 📝 Licence

Ce projet est distribué sous la licence **MIT**. Voir `LICENSE` pour plus de détails.

---

## ✍️ Auteur

Développé par Tony Gheeraert dans le cadre de la **Chaire d’Excellence en Éditions Numériques**  
Université de Rouen – Centre d'étude et de recherche Editer-Interpréter (UR 3229)
Presses de l'Université de Rouen et du Havre

---

## 🌐 Capture d’écran (à venir !)

*Interface avec didascalie reconnue et affichée dans les onglets TEI et LaTeX.*
