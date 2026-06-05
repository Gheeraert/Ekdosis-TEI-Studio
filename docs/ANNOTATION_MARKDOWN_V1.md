# Syntaxe légère des annotations

Dernière mise à jour documentaire : 5 juin 2026.

## 1. Objet

Les annotations peuvent être saisies avec une syntaxe Markdown limitée pour faciliter l’écriture par les éditeurs.

Cette syntaxe n’est pas la source canonique.
Elle doit être convertie vers TEI lorsqu’une note est injectée dans le document.

## 2. Constructions autorisées

Support minimal recommandé :

- paragraphes ;
- italiques ;
- emphase simple ;
- listes simples ;
- références ou citations simples si le module de références les prend en charge.

## 3. Non-objectifs

Ne pas viser un Markdown complet.
Ne pas introduire de HTML arbitraire.
Ne pas permettre une syntaxe susceptible de casser la TEI.

## 4. Sortie TEI

Le contenu d’une annotation doit produire des éléments TEI simples et prévisibles, par exemple :

```xml
<note>
  <p>Texte de la note avec <hi rend="italic">italique</hi>.</p>
</note>
```

## 5. Rendu

Les rendus HTML et LaTeX doivent consommer la TEI enrichie, non la chaîne Markdown brute.
