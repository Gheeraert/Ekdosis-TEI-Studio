from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import BlockKind, InlineKind, InlineNode, ParsedBlock, ParsedDocument


def inline_text(nodes: tuple[InlineNode, ...]) -> str:
    parts: list[str] = []
    for node in nodes:
        if node.kind is InlineKind.TEXT:
            parts.append(node.text)
        elif node.kind is InlineKind.LINK:
            parts.append(inline_text(node.children))
        elif node.kind is InlineKind.NOTE:
            parts.append(inline_text(node.children))
        else:
            parts.append(inline_text(node.children))
    return "".join(parts)


def parse_pandoc_document(source_path: Path, payload: dict[str, Any]) -> ParsedDocument:
    raw_blocks = payload.get("blocks")
    if not isinstance(raw_blocks, list):
        raise ValueError("Invalid Pandoc payload: missing 'blocks' list.")
    parser = _PandocParser()
    for raw_block in raw_blocks:
        parser.parse_block(raw_block, inherited_style=None)
    return ParsedDocument(source_path=source_path.resolve(), blocks=tuple(parser.blocks))


@dataclass
class _PandocParser:
    blocks: list[ParsedBlock] = None  # type: ignore[assignment]
    _index: int = 0

    def __post_init__(self) -> None:
        self.blocks = []

    def _next_index(self) -> int:
        self._index += 1
        return self._index

    def parse_block(self, raw_block: Any, *, inherited_style: str | None) -> None:
        if not isinstance(raw_block, dict):
            self.blocks.append(
                ParsedBlock(
                    kind=BlockKind.UNSUPPORTED,
                    index=self._next_index(),
                    raw_type=type(raw_block).__name__,
                )
            )
            return

        block_type = str(raw_block.get("t") or "")
        content = raw_block.get("c")

        if block_type == "Div":
            style = _extract_style_from_attr(_extract_attr(content, index=0))
            nested = _extract_child_blocks_from_div(content)
            for child in nested:
                self.parse_block(child, inherited_style=style or inherited_style)
            return

        if block_type in {"Para", "Plain"}:
            self.blocks.append(
                ParsedBlock(
                    kind=BlockKind.PARAGRAPH,
                    index=self._next_index(),
                    style_name=inherited_style or "Normal",
                    inlines=_parse_inlines(content if isinstance(content, list) else []),
                    raw_type=block_type,
                )
            )
            return

        if block_type == "Header":
            level, attr, inlines = _extract_header_parts(content)
            header_style = _extract_style_from_attr(attr)
            self.blocks.append(
                ParsedBlock(
                    kind=BlockKind.HEADING,
                    index=self._next_index(),
                    style_name=header_style or inherited_style or f"Heading {level}",
                    heading_level=level,
                    inlines=_parse_inlines(inlines),
                    raw_type=block_type,
                )
            )
            return

        if block_type == "BlockQuote":
            quote_blocks = content if isinstance(content, list) else []
            for child in quote_blocks:
                if isinstance(child, dict) and child.get("t") in {"Para", "Plain"}:
                    self.blocks.append(
                        ParsedBlock(
                            kind=BlockKind.PARAGRAPH,
                            index=self._next_index(),
                            style_name="Citation",
                            inlines=_parse_inlines(child.get("c") if isinstance(child.get("c"), list) else []),
                            raw_type="BlockQuote",
                        )
                    )
                else:
                    self.parse_block(child, inherited_style="Citation")
            return

        if block_type in {"BulletList", "OrderedList"}:
            list_items = _extract_list_items(block_type, content)
            self.blocks.append(
                ParsedBlock(
                    kind=BlockKind.LIST,
                    index=self._next_index(),
                    list_items=tuple(list_items),
                    ordered_list=(block_type == "OrderedList"),
                    raw_type=block_type,
                )
            )
            return

        if block_type == "Table":
            rows, complex_reason = _extract_table_rows(content)
            self.blocks.append(
                ParsedBlock(
                    kind=BlockKind.TABLE,
                    index=self._next_index(),
                    table_rows=tuple(rows),
                    table_complex_reason=complex_reason,
                    raw_type=block_type,
                )
            )
            return

        if block_type == "HorizontalRule":
            return

        self.blocks.append(
            ParsedBlock(
                kind=BlockKind.UNSUPPORTED,
                index=self._next_index(),
                raw_type=block_type or "unknown",
            )
        )


def _extract_attr(node: Any, *, index: int) -> Any:
    if isinstance(node, list) and len(node) > index:
        return node[index]
    return None


def _extract_child_blocks_from_div(content: Any) -> list[Any]:
    if not isinstance(content, list) or len(content) < 2:
        return []
    child_blocks = content[1]
    if not isinstance(child_blocks, list):
        return []
    return list(child_blocks)


def _attr_to_dict(attr: Any) -> dict[str, str]:
    if not isinstance(attr, list) or len(attr) != 3:
        return {}
    kv_pairs = attr[2]
    result: dict[str, str] = {}
    if isinstance(kv_pairs, list):
        for pair in kv_pairs:
            if isinstance(pair, list) and len(pair) == 2:
                key = str(pair[0]).strip()
                value = str(pair[1]).strip()
                if key:
                    result[key] = value
    return result


def _extract_style_from_attr(attr: Any) -> str | None:
    values = _attr_to_dict(attr)
    style = values.get("custom-style")
    if style:
        return style.strip() or None
    return None


def _extract_header_parts(content: Any) -> tuple[int, Any, list[Any]]:
    if not isinstance(content, list) or len(content) != 3:
        return 1, None, []
    level = int(content[0]) if isinstance(content[0], int) else 1
    attr = content[1]
    inlines = content[2] if isinstance(content[2], list) else []
    return level, attr, inlines


def _parse_inlines(raw_inlines: list[Any]) -> tuple[InlineNode, ...]:
    output: list[InlineNode] = []
    for item in raw_inlines:
        if not isinstance(item, dict):
            continue
        inline_type = str(item.get("t") or "")
        content = item.get("c")

        if inline_type == "Str":
            output.append(InlineNode(kind=InlineKind.TEXT, text=str(content)))
            continue
        if inline_type in {"Space", "SoftBreak", "LineBreak"}:
            output.append(InlineNode(kind=InlineKind.TEXT, text=" "))
            continue
        if inline_type == "Emph":
            output.append(InlineNode(kind=InlineKind.ITALIC, children=_parse_inlines(content if isinstance(content, list) else [])))
            continue
        if inline_type == "Strong":
            output.append(InlineNode(kind=InlineKind.BOLD, children=_parse_inlines(content if isinstance(content, list) else [])))
            continue
        if inline_type == "Underline":
            output.append(
                InlineNode(
                    kind=InlineKind.UNDERLINE,
                    children=_parse_inlines(content if isinstance(content, list) else []),
                )
            )
            continue
        if inline_type == "SmallCaps":
            output.append(
                InlineNode(
                    kind=InlineKind.SMALLCAPS,
                    children=_parse_inlines(content if isinstance(content, list) else []),
                )
            )
            continue
        if inline_type == "Superscript":
            output.append(InlineNode(kind=InlineKind.SUP, children=_parse_inlines(content if isinstance(content, list) else [])))
            continue
        if inline_type == "Subscript":
            output.append(InlineNode(kind=InlineKind.SUB, children=_parse_inlines(content if isinstance(content, list) else [])))
            continue
        if inline_type == "Strikeout":
            output.append(
                InlineNode(
                    kind=InlineKind.STRIKETHROUGH,
                    children=_parse_inlines(content if isinstance(content, list) else []),
                )
            )
            continue
        if inline_type == "Link":
            if isinstance(content, list) and len(content) >= 3:
                child_inlines = content[1] if isinstance(content[1], list) else []
                target_spec = content[2]
                target = None
                if isinstance(target_spec, list) and target_spec:
                    target = str(target_spec[0])
                output.append(
                    InlineNode(
                        kind=InlineKind.LINK,
                        children=_parse_inlines(child_inlines),
                        target=target,
                    )
                )
            continue
        if inline_type == "Note":
            note_children = _parse_note_blocks(content if isinstance(content, list) else [])
            output.append(InlineNode(kind=InlineKind.NOTE, children=note_children))
            continue
        if inline_type == "Code":
            if isinstance(content, list) and len(content) == 2:
                output.append(InlineNode(kind=InlineKind.TEXT, text=str(content[1])))
            continue

        output.append(InlineNode(kind=InlineKind.TEXT, text=_stringify_inline(item)))
    return tuple(output)


def _parse_note_blocks(blocks: list[Any]) -> tuple[InlineNode, ...]:
    note_inlines: list[InlineNode] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_type = block.get("t")
        if block_type in {"Para", "Plain"}:
            note_inlines.extend(_parse_inlines(block.get("c") if isinstance(block.get("c"), list) else []))
            note_inlines.append(InlineNode(kind=InlineKind.TEXT, text=" "))
    while note_inlines and note_inlines[-1].kind is InlineKind.TEXT and not note_inlines[-1].text.strip():
        note_inlines.pop()
    return tuple(note_inlines)


def _stringify_inline(item: dict[str, Any]) -> str:
    inline_type = str(item.get("t") or "")
    content = item.get("c")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        nested: list[str] = []
        for part in content:
            if isinstance(part, dict):
                nested.append(_stringify_inline(part))
            elif isinstance(part, str):
                nested.append(part)
        collapsed = "".join(nested).strip()
        if collapsed:
            return collapsed
    return inline_type


def _extract_list_items(block_type: str, content: Any) -> list[tuple[InlineNode, ...]]:
    if block_type == "BulletList":
        raw_items = content if isinstance(content, list) else []
    else:
        raw_items = []
        if isinstance(content, list) and len(content) == 2 and isinstance(content[1], list):
            raw_items = content[1]

    rows: list[tuple[InlineNode, ...]] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, list):
            continue
        merged: list[InlineNode] = []
        for block in raw_item:
            if isinstance(block, dict) and block.get("t") in {"Para", "Plain"}:
                merged.extend(_parse_inlines(block.get("c") if isinstance(block.get("c"), list) else []))
                merged.append(InlineNode(kind=InlineKind.TEXT, text=" "))
        if merged and merged[-1].kind is InlineKind.TEXT and not merged[-1].text.strip():
            merged.pop()
        rows.append(tuple(merged))
    return rows


def _extract_table_rows(content: Any) -> tuple[tuple[tuple[InlineNode, ...], ...], str | None]:
    if not isinstance(content, list) or len(content) < 5:
        return (), "TABLE_UNSUPPORTED_SHAPE"

    header_rows_raw = _extract_rows_from_thead(content[3])
    body_rows_raw = _extract_rows_from_tbodies(content[4])
    footer_rows_raw = _extract_rows_from_tfoot(content[5] if len(content) > 5 else None)
    all_rows_raw = [*header_rows_raw, *body_rows_raw, *footer_rows_raw]
    if not all_rows_raw:
        return (), None

    rows: list[tuple[tuple[InlineNode, ...], ...]] = []
    expected_columns: int | None = None
    for row in all_rows_raw:
        cells_raw = _extract_cells_from_row(row)
        if cells_raw is None:
            return (), "TABLE_ROW_UNSUPPORTED_SHAPE"
        parsed_cells: list[tuple[InlineNode, ...]] = []
        for cell in cells_raw:
            parsed_cell, complex_reason = _parse_table_cell(cell)
            if complex_reason is not None:
                return (), complex_reason
            parsed_cells.append(parsed_cell)
        if expected_columns is None:
            expected_columns = len(parsed_cells)
        elif expected_columns != len(parsed_cells):
            return (), "TABLE_INCONSISTENT_COLUMNS"
        rows.append(tuple(parsed_cells))
    return tuple(rows), None


def _extract_cells_from_row(row: Any) -> list[Any] | None:
    if not isinstance(row, list) or len(row) < 2:
        return None
    cells = row[1]
    if not isinstance(cells, list):
        return None
    return cells


def _extract_rows_from_thead(node: Any) -> list[Any]:
    if not isinstance(node, list) or len(node) != 2:
        return []
    rows = node[1]
    return list(rows) if isinstance(rows, list) else []


def _extract_rows_from_tbodies(node: Any) -> list[Any]:
    if not isinstance(node, list):
        return []
    rows: list[Any] = []
    for tbody in node:
        if not isinstance(tbody, list) or len(tbody) < 4:
            continue
        head_rows = tbody[2]
        body_rows = tbody[3]
        if isinstance(head_rows, list):
            rows.extend(head_rows)
        if isinstance(body_rows, list):
            rows.extend(body_rows)
    return rows


def _extract_rows_from_tfoot(node: Any) -> list[Any]:
    if not isinstance(node, list) or len(node) != 2:
        return []
    rows = node[1]
    return list(rows) if isinstance(rows, list) else []


def _parse_table_cell(node: Any) -> tuple[tuple[InlineNode, ...], str | None]:
    if not isinstance(node, list) or len(node) < 5:
        return (), "TABLE_CELL_UNSUPPORTED_SHAPE"
    row_span = node[2]
    col_span = node[3]
    if (isinstance(row_span, int) and row_span > 1) or (isinstance(col_span, int) and col_span > 1):
        return (), "TABLE_COMPLEX_SPAN"

    blocks = node[4]
    if not isinstance(blocks, list):
        return (), "TABLE_CELL_UNSUPPORTED_CONTENT"

    merged: list[InlineNode] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_type = block.get("t")
        if block_type in {"Para", "Plain"}:
            merged.extend(_parse_inlines(block.get("c") if isinstance(block.get("c"), list) else []))
            merged.append(InlineNode(kind=InlineKind.TEXT, text=" "))
            continue
        return (), "TABLE_COMPLEX_CONTENT"
    if merged and merged[-1].kind is InlineKind.TEXT and not merged[-1].text.strip():
        merged.pop()
    return tuple(merged), None
