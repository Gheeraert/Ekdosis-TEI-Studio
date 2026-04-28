# Export LaTeX / Ekdosis (greffe V2)

Ce module réintroduit l'export LaTeX/Ekdosis sans réintroduire la logique Tkinter legacy.

## Utilisation

- UI Tkinter: `Outils -> Export LaTeX-Ekdosis`
- Le service lit:
  - le texte de transcription courant;
  - la configuration des temoins active;
  - le temoin de reference courant.
- Le service produit:
  - `body`: corps Ekdosis seul;
  - `full_document`: document `.tex` autonome (preambule, `\DeclareWitness`, titlepage, corps, fin).
- L'onglet bas `Ekdosis` affiche le `body`.

## Service

Fichier: `src/ets/application/ekdosis_service.py`

API principale:

```python
generate_ekdosis_from_text(
    text: str,
    witnesses: list[WitnessLike],
    reference_witness: str | int | None = None,
    metadata: EkdosisMetadata | dict | None = None,
    start_line_number: int = 1,
) -> EkdosisResult
```

L'export disque est fourni par `export_ekdosis(...)`.

## Repris du legacy

- templates `template_ekdosis_preamble`, `template_ekdosis_debut_doc`, `template_ekdosis_fin_doc`;
- generation `\ekddiv`, `\speaker`, `\vnum`, `\app/\lem/\rdg`, `\DeclareWitness`;
- echappement LaTeX/Ekdosis (`& % $ # _ { }`) et gestion des series de `~`.

## Hors scope volontaire

- compilation PDF;
- installation TeX;
- refonte typographique;
- changement des moteurs TEI/HTML/site builder.
