# 🧾 Ekdosis-Tei Studio

**Ekdosis-Tei Studio** est un outil d'encodage **TEI XML** et **LaTeX (avec le paquet ekdosis)** des variantes dans le théâtre classique, avec gestion des actes, scènes, personnages, locuteurs, vers et variantes textuelles ligne à ligne, ainsi que des italiques et des didascalies implicites.
Développé avec Python et Tkinter, avec recours à XML et LaTeX, il s'adresse aux chercheurs et éditeurs critiques travaillant sur les textes dramatiques anciens. L'interface de saisie est inspirée du **markdown**. Système de prévisualisation html via une feuille XSLT dynamique intégrée au script Python. **Aucune connaissance de la TEI ni d'un système de balisage quelconque n'est requis, l'encodage est entièrement automatique.**

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![TEI](https://img.shields.io/badge/Format-TEI%20XML-ffcc00)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-En%20cours%20de%20développement-orange)

---

## ✨ Fonctionnalités principales

- 🏛 Saisie encodée structurée en style markdown : actes, scènes, personnages, locuteurs, tirades, didascalies, didascalies implicites, italique (interface graphique complète possible)
- 🔀 Comparaison automatique de variantes ligne à ligne (difflib)
- 🔎 Génération parallèle des résultats en :
  - **TEI XML** avec balises `<app>`, `<lem>`, `<rdg>`, `<stage>`, etc.
  - **LaTeX** compatible avec le package `ekdosis` et template adapté fourni (template par T. Gheeraert et F. Siraguso)
- 🎭 Gestion des didascalies : format `**texte**` reconnu et encodé en `<stage>` / `\didas{}`
- 🔤 Échappement automatique des caractères spéciaux (`&`, etc.)
- 🧑‍🎓 Interface conviviale en Tkinter avec onglets TEI / LaTeX
- 🧪 Validation de structure intégrée (actes, scènes, locuteurs)
- 🎨 Style visuel "parchemin"
- 🌐 Prévisualisation en html

---

## 🖋️ Exemple de saisie

```
####Acte premier#### */acte
####Acte premier####
####Acte premier####
####Acte I####

###Scène I###
###Scène premiere###
###Scène premiere###
###Scène premiere###

##Antiochus## ##Arsace##
##Antiochus## ##Arsace##
##Antiochus## ##Arsace##
##Antiochus## ##Arsace##

#Antiochus#
#Antiochus#
#Antiochus#
#Antiochus#

**Antiochus entre.**
**Antiochus entre.**
**Antiochus entre.**
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

$$SET$$
C'est icy _quelquefois_ qu'il se cache à sa Cour,
C'est icy _quelquefois_ qu'il se cache à sa Cour,
C'est ici _quelquefois_ qu'il se cache à sa Cour,
C'est ici _quelquefois qu'il se cache à sa Cour, 
$$fin$$
```

---

## 🚀 Lancer l'application

Python : Assurez-vous d'avoir Python 3.9+ installé. Un exécutable est également disponible


```bash
python TEILaTeXStudio.py
```

Exécutable: Téléchargez et lancez simplement le fichier (.dmg pour Mac, .exe pour Windows)

---

## 📦 Dépendances

- Python standard (`tkinter`, `difflib`, `re`, etc.)
- template LaTeX préconfiguré avec ekdosis pour l'affichage direct du code LaTeX généré
- feuille de transformation XSL à adapter pour la sortie TEI
- nécessite lxml et bs4 (à installer via la console, par ex: pip install bs4 et pip install lxml)
---

## 🧪 En projet

- Amélioration/réparation des sorties ekdosis, actuellement instables
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



