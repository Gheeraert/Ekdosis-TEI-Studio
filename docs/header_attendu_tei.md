# En-tête TEI attendu pour la génération HTML

## 1. Distinguer deux choses

Il faut distinguer clairement deux niveaux.

### A. Le vrai en-tête TEI (`teiHeader`)
C'est lui qui appartient au document TEI canonique. Il doit être présent dans le XML produit.

### B. Le bloc de crédits de prévisualisation (`metadonnees`)
Ce bloc n'appartient pas au `teiHeader`. Il sert uniquement à l'affichage HTML dans la feuille XSLT actuelle.
Il peut rester **optionnel** pour ne pas compliquer inutilement la TEI de base.

---

## 2. Structure minimale attendue du document

```xml
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>...</title>
        <author>...</author>
        <editor>...</editor>
      </titleStmt>
      <publicationStmt>
        <publisher>Presses de l'Université de Rouen et du Havre</publisher>
        <pubPlace>Rouen</pubPlace>
        <date>...</date>
      </publicationStmt>
      <sourceDesc>
        <p>généré par Ekdosis-TEI Studio – Acte X, Scène Y</p>
      </sourceDesc>
    </fileDesc>
  </teiHeader>

  <!-- optionnel : seulement pour le rendu HTML -->
  <metadonnees>
    <credit>...</credit>
    <credit>...</credit>
  </metadonnees>

  <text>
    <body>
      ...
    </body>
  </text>
</TEI>
```

---

## 3. Contraintes à documenter explicitement

- La racine doit être `TEI` dans l'espace de noms TEI.
- `teiHeader` doit précéder `text`.
- `fileDesc` doit contenir au minimum `titleStmt`, `publicationStmt`, `sourceDesc`.
- `titleStmt` doit contenir au moins :
  - `title`
  - `author`
  - `editor`
- `publicationStmt` doit contenir au moins :
  - `publisher`
  - `pubPlace`
  - `date`
- `sourceDesc/p` doit indiquer au minimum le contexte de génération, par exemple acte et scène.
- `text/body` reste la zone canonique du texte édité.

---

## 4. Ce que la feuille XSLT attend en plus aujourd'hui

Pour le rendu HTML actuel, la feuille XSLT exploite surtout :

- `metadonnees/credit` pour le cartouche de crédits ;
- `text/body` pour le texte ;
- `stage[@type='DI']` pour les didascalies implicites ;
- `stage[@type='personnages']` ou `stage[@type='characters']` pour la liste des personnages ;
- `app/lem/rdg` pour les variantes.

Autrement dit :

- le **XML canonique** repose sur `teiHeader` ;
- le **rendu HTML actuel** repose aussi sur un bloc auxiliaire `metadonnees`.

---

## 5. Recommandation simple pour la suite

La solution la plus prudente est la suivante :

1. conserver le `teiHeader` comme structure canonique obligatoire ;
2. conserver `metadonnees` comme bloc optionnel de confort pour l'aperçu HTML ;
3. documenter noir sur blanc que `metadonnees` n'est pas le vrai en-tête TEI mais un bloc de présentation ;
4. à plus long terme, faire dériver ce cartouche HTML directement du `teiHeader` pour éviter la redondance.
