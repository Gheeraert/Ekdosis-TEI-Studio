**1. 🖊️ Syntaxe de saisie (Markdown inspiré)**
L’encodage se fait dans une zone de saisie structurée avec une syntaxe simple : les vers sont saisis ligne à ligne, avec ou sans variantes selon les témoins.

Soit une édition avec trois témoins, on écrira:

Etat du vers 1 selon le témoin 1<br>
Etat du vers 1 selon le témoin 2<br>
Etat du vers 1 selon le témoin 3<br>

Etat du vers 1 selon le témoin 1<br>
Etat du vers 1 selon le témoin 2<br>
Etat du vers 1 selon le témoin 3<br>

etc...

Les changements de locuteurs, d'actes, de scènes et de listes de personnages en tête des scènes sont notés ainsi:

####n####	Début d’un acte numéroté	####1####
###n###	Début d’une scène numérotée	###3###
##NOM##	Liste des personnages présents sur scène	##PHÈDRE, HIPPOLYTE##
#NOM#	Indique le locuteur d’une tirade	#PHÈDRE#
**didascalie**	Insère une didascalie	**Elle sort.**
***vers partagé***	Indique un vers réparti entre deux personnages	"Imaginations!***" / "***Eternelles clartés"!


**2. 💾 Enregistrement de la saisie brute**
Pour sauvegarder la saisie initiale, il suffit d’utiliser le menu Fichier > Enregistrer.
Cela enregistre le contenu brut de la zone de saisie dans un fichier .txt lisible, avec la syntaxe décrite ci-dessus.

Une fois enregistré (nom prédéfini), ce fichier peut être rouvert pour édition ou réutilisé comme base de traitement TEI/LaTeX.

**3. ⚙️ Paramétrage des sorties TEI et LaTeX**
Avant d’exporter une édition en TEI ou en LaTeX (ekdosis), une boîte de dialogue vous demandera d'entrer pour chaque témoin
- une abréviation (sigle court, par exemple A, B, C, etc.)
- une année de publication
- une description du témoin ("édition princeps", "dernière édition du vivant de l'auteur", etc.)

Ces métadonnées sont ensuite automatiquement intégrées dans l'environnement de l'édition critique (TEI ou LaTeX-ekdosis)
Le fichier LaTeX généré est compatible avec le package ekdosis, prêt à être compilé, ou visualisé en html statique via traitement XSLT dynamique intégré au logiciel.

N.B. Attention, ekdosis exige la compilation par LuaLaTeX.
N.B. La sortie ekdosis qui apparaît à la volée dans l'onglet du bas doit être intégrée au template (fourni sur le dépôt) pour être opérationnelle, tandis que la sortie "exporter ekdosis" est complète et compilable telle quelle en LaTeX.
