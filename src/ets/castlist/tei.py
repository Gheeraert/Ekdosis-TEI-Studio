from __future__ import annotations

import xml.etree.ElementTree as ET

from ets.collation import collate_parallel_text
from ets.domain import DramatisPersonae, EditionConfig
from ets.tei.generator import _append_collated_text, _tei


def _append_readings(parent: ET.Element, readings: list[str], config: EditionConfig) -> None:
    collated = collate_parallel_text(
        readings=readings,
        witness_sigla=[witness.siglum for witness in config.witnesses],
        ref_index=config.reference_witness,
        strict_validation=False,
    )
    _append_collated_text(parent, collated)


def build_castlist_tei_element(dramatis_personae: DramatisPersonae, config: EditionConfig) -> ET.Element:
    root = ET.Element(_tei("div"), {"type": "dramatis-personae"})

    if dramatis_personae.head_readings:
        head = ET.SubElement(root, _tei("head"))
        _append_readings(head, dramatis_personae.head_readings, config)

    cast_list = ET.SubElement(root, _tei("castList"))
    for entry in dramatis_personae.entries:
        cast_item = ET.SubElement(cast_list, _tei("castItem"), {"xml:id": entry.id})
        ET.SubElement(cast_item, _tei("role")).text = entry.role
        if entry.desc:
            ET.SubElement(cast_item, _tei("roleDesc")).text = entry.desc
        note = ET.SubElement(cast_item, _tei("note"), {"type": "semi-diplomatic"})
        _append_readings(note, entry.readings, config)

    if dramatis_personae.setting_readings:
        setting = ET.SubElement(root, _tei("stage"), {"type": "setting"})
        _append_readings(setting, dramatis_personae.setting_readings, config)

    return root


def generate_castlist_tei(dramatis_personae: DramatisPersonae, config: EditionConfig) -> str:
    element = build_castlist_tei_element(dramatis_personae, config)
    ET.indent(element, "  ")
    return ET.tostring(element, encoding="unicode")
