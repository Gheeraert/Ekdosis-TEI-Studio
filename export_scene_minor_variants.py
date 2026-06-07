from __future__ import annotations

import argparse
from pathlib import Path

from ets.core import run_pipeline_from_text
from ets.domain import EditionConfig, Witness
from ets.latex.ekdosis_from_tei import tei_to_ekdosis


def witness_labels(count: int) -> list[str]:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return list(alphabet[:count])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, default=Path("_minor_variants_real_scene"))
    parser.add_argument("--witnesses", type=int, default=5)
    parser.add_argument("--title", default="Test variantes mineures")
    args = parser.parse_args()

    text = args.input.read_text(encoding="utf-8-sig")
    labels = witness_labels(args.witnesses)

    config = EditionConfig(
        title=args.title,
        author="Jean Racine",
        editor="Tony",
        witnesses=[
            Witness(siglum=label, year="", description=label)
            for label in labels
        ],
        reference_witness=0,
    )

    xml = run_pipeline_from_text(text, config)

    args.out.mkdir(parents=True, exist_ok=True)

    stem = args.input.stem
    xml_path = args.out / f"{stem}.xml"
    full_path = args.out / f"{stem}_full.tex"
    hide_path = args.out / f"{stem}_hide_minor.tex"

    xml_path.write_text(xml, encoding="utf-8")
    full_path.write_text(tei_to_ekdosis(xml), encoding="utf-8")
    hide_path.write_text(
        tei_to_ekdosis(xml, apparatus_policy="hide_minor"),
        encoding="utf-8",
    )

    print("Fichiers générés :")
    print(xml_path)
    print(full_path)
    print(hide_path)
    print()
    print('Nombre de <app type="minor"> :', xml.count('type="minor"'))


if __name__ == "__main__":
    main()