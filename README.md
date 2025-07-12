# 🧾 Ekdosis-Tei Studio

**Ekdosis-Tei Studio** est un outil d'encodage **TEI XML** et **LaTeX (avec le paquet ekdosis)** des variantes dans le théâtre classique, avec gestion des actes, scènes, personnages, locuteurs, vers et variantes textuelles ligne à ligne. Développé avec Python et Tkinter, il s'adresse aux chercheurs et éditeurs critiques travaillant sur les textes dramatiques anciens. L'interface est inspirée du **markdown**. Système de prévisualisation html via une feuille xslt dynamique intégrée au script Python. **Aucune connaissance de la TEI ni d'un système de balisage quelconque n'est requis, l'encodage est entièrement automatique.**

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![TEI](https://img.shields.io/badge/Format-TEI%20XML-ffcc00)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-En%20cours%20de%20développement-orange)

---

## ✨ Fonctionnalités principales

- 🏛 Saisie scène par scène, encodée structurée en style markdown : actes, scènes, personnages, locuteurs, tirades, didascalies
- interface graphique complète possible)
- 🔀 Comparaison automatique de variantes ligne à ligne (difflib)
- 🔎 Génération parallèle des résultats en :
  - **TEI XML** avec balises `<app>`, `<lem>`, `<rdg>`, `<stage>`, etc.
  - **LaTeX** compatible avec le package `ekdosis` et template adapté fourni (template par T. Gheeraert et F. Siraguso)
- 🎭 Gestion des didascalies : format `**texte**` reconnu et encodé en `<stage>` / `\didas{}`
- - 🎭 Gestion des vers remaniés complètement à gérer globalement : format `#####texte#####` reconnu et traité par une seule balise <app>
- 🔤 Échappement automatique des caractères spéciaux (`&`, etc.)
- 🧑‍🎓 Interface conviviale en Tkinter avec onglets TEI / LaTeX
- 🧪 Validation de structure intégrée (actes, scènes, locuteurs)
- 🎨 Style visuel "parchemin"
- 🌐 Prévisualisation en html

---

## 🖋️ Exemple de saisie

```
####Acte Premier####
####Acte Premier####
####Acte Premier####
####Acte I####

###Scène 1###
###Scène 1###
###Scène 1###
###Scène Première###

##Antiochus## ##Arsace##
##Antiochus## ##Arsace##
##Antiochus## ##Arsace##
##Antiochus## ##Arsac##

#Antiochus#
#Antiochus#
#Antiochus#
#Antiocus#

**Antiochus entre.**
**Antiochus entre.**
**Antiochus entre.**
**Antiochus entre.**
_(2 étoiles pour les didascalies)_

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
_(3 étoiles en fin de vers
pour la première moitié des vers partagés)_

#Arsace#
#Arsace#
#Arsace#
#Arsace#

***superbe & solitaire,
***superbe & solitaire,
***superbe & solitaire,
***superbe & solitaire,
_(3 étoiles en début de vers
pour la seconde moitié des vers partagés)_

Des secrets de Titus est le dépositaire.
Des secrets de Titus est le dépositaire.
Des secrets de Titus est le dépositaire.
Des secrets de Titus est le dépositaire.

C'est icy quelquefois qu'il se cache à sa Cour,
C'est icy quelquefois qu'il se cache à sa Cour,
C'est ici quelquefois qu'il se cache à sa Cour,
C'est ici quelquefois qu'il se cache à sa Cour,

#####Il deuoit bien plutost les fermer pour jamais,
#####Il devoit bien plûtost les fermer pour jamais,
#####Il devoit bien plûtost les fermer pour jamais,
#####Puisse plûtost la mort les fermer pour jamais,
#####Il devoit bien plutost les fermer pour jamais,
_(5 dièses pour neutraliser le traitement des variantes mot par mot
et traiter le vers en entier avec une seule balise <app>)_
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

- Python standard (`tkinter`, `re`, etc.)
- template LaTeX préconfiguré avec ekdosis pour l'affichage direct du code LaTeX généré
- feuille de transformation XSL à adapter pour la sortie TEI (librairie `lxml`)
- Module [lxml](https://lxml.de/) (pour le traitement XML)
- Module [tkinter](https://docs.python.org/fr/3/library/tkinter.html) (pour l’interface graphique, inclus dans Python officiel)

---

## 🧪 En projet

- Encodage des didascalies internes (implicites)
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

