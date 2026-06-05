from __future__ import annotations

MINIMAL_PREAMBLE = r"""\documentclass{book}
\usepackage[main=french,spanish,latin]{babel}
\usepackage[T1]{fontenc}
\usepackage{fontspec}
\usepackage{csquotes}
\usepackage[teiexport, divs=ekdosis, poetry=verse]{ekdosis}

\newenvironment{speech}{\par}{\par}
\newcommand{\speaker}[1]{\vspace{1em}\large\centering\textsc{#1}\par}
\newcommand{\didas}[1]{\par\begin{center}\textit{#1}\end{center}\par}
\newcommand{\vnum}[2]{\linelabel{v#1}#2\par}
"""


def wrap_standalone(fragment: str) -> str:
    body = fragment.rstrip()
    return f"{MINIMAL_PREAMBLE}\n\\begin{{document}}\n\\begin{{ekdosis}}\n{body}\n\\end{{ekdosis}}\n\\end{{document}}\n"
