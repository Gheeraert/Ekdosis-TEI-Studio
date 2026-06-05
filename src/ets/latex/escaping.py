from __future__ import annotations

NBSP = "\u00a0"

_RESERVED_CHARS = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "\\": r"\textbackslash{}",
}


def escape_latex_text(text: str) -> str:
    """Escape ordinary text for LaTeX while preserving TEI non-breaking spaces."""
    output: list[str] = []
    for char in text:
        if char == NBSP:
            output.append("~")
        else:
            output.append(_RESERVED_CHARS.get(char, char))
    return "".join(output)
