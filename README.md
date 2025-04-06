# 🧾 Ekdosis-Tei Studio

**Ekdosis-Tei Studio** est un outil d'encodage **TEI XML** et **LaTeX (avec le paquet ekdosis)** des variantes dans le théâtre classique, avec gestion des actes, scènes, personnages, locuteurs, vers et variantes textuelles ligne à ligne. Développé avec Python et Tkinter, il s'adresse aux chercheurs et éditeurs critiques travaillant sur les textes dramatiques anciens. L'interface est inspirée du **markdown**. Système de prévisualisation html via une feuille xslt dynamique intégrée au script Python. **Aucune connaissance de la TEI ni d'un système de balisage quelconque n'est requis, l'encodage est entièrement automatique.**

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![TEI](https://img.shields.io/badge/Format-TEI%20XML-ffcc00)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-En%20cours%20de%20développement-orange)

---

## ✨ Fonctionnalités principales

- 🏛 Saisie encodée structurée en style markdown : actes, scènes, personnages, locuteurs, tirades, didascalies (interface graphique complète possible)
- 🔀 Comparaison automatique de variantes ligne à ligne (difflib)
- 🔎 Génération parallèle des résultats en :
  - **TEI XML** avec balises `<app>`, `<lem>`, `<rdg>`, `<stage>`, etc.
  - **LaTeX** compatible avec le package `ekdosis` et template adapté fourni (template par T. Gheeraert et F. Siraguso)
- 🎭 Gestion des didascalies : format `**texte**` reconnu et encodé en `<stage>` / `\didas{}`
- 🔤 Échappement automatique des caractères spéciaux (`&`, etc.)
- 🧑‍🎓 Interface conviviale en Tkinter avec onglets TEI / LaTeX
- 🧪 Validation de structure intégrée (actes, scènes, locuteurs)
- 🎨 Style visuel "parchemin" pour une expérience élégante
- 🌐 Prévisualisation en html

---

## 🖋️ Exemple de saisie

```
####1####
###1###
##Antiochus## ##Arsace##
#Antiochus#

**Antiochus entre.**

Arrestons un moment. La pompe de ces lieux
Arrestons un moment. La pompe de ces lieux
Arrestons un moment. La pompe de ces lieux
Arrestons un moment. La pompe de ces lieux

Je le vois bien, Arsace, est nouvelle à tes yeux
Je le voy bien, Arsace, est nouvelle à tes yeux
Je le vois bien, Arsace, est nouvelle à tes yeux
Je le voy bien, Arsace, est nouvelle à tes yeux

Souvent ce Cabinet***
Souvent ce Cabinet***
Souvent ce Cabinet***
Souvent ce Cabinet***

#Arsace#
***superbe & solitaire,
***superbe & solitaire,
***superbe & solitaire,
***superbe & solitaire,

Des secrets de Titus est le dépositaire.
Des secrets de Titus est le dépositaire.
Des secrets de Titus est le dépositaire.
Des secrets de Titus est le dépositaire.

C'est icy quelquefois qu'il se cache à sa Cour,
C'est icy quelquefois qu'il se cache à sa Cour,
C'est ici quelquefois qu'il se cache à sa Cour,
C'est ici quelquefois qu'il se cache à sa Cour, 
```

---

## 🚀 Lancer l'application

Assurez-vous d'avoir Python 3.9+ installé. Un exécutable est également disponible (Ubuntu et Windows)

```bash
python TEILaTeXStudio.py
```

---

## 📦 Dépendances

- Python standard (`tkinter`, `difflib`, `re`, etc.)
- template LaTeX préconfiguré avec ekdosis pour l'affichage direct du code LaTeX généré
- feuille de transformation XSL à adapter pour la sortie TEI
---

## 🧪 En projet

- Prise en compte des variantes de didascalies
- Encodage de scènes muettes
- Résolution des cas particuliers
- portage en ligne via serveur Flask

---

## 🤝 Contribuer

Suggestions, pull requests ou retours bienvenus !  
Créez une [issue](https://github.com/ton-nom-utilisateur/TEILaTeXStudio/issues) ou proposez une amélioration.

---

## 📝 Licence

Ce projet est distribué sous la licence **MIT**. Voir `LICENSE` pour plus de détails.

---

## ✍️ Auteur

Développé par Tony Gheeraert dans le cadre de la **Chaire d’Excellence en Éditions Numériques**<br>
Université de Rouen – Centre d'étude et de recherche Editer-Interpréter (UR 3229)<br>
Presses de l'Université de Rouen et du Havre

Remerciements à Federico Siragusa et Roch Delannay pour leur contribution au template LaTeX


---

## 🌐 Capture d’écran

![image](https://github.com/user-attachments/assets/157acc17-1415-4ab4-ba84-5cecb93a3f2a)

