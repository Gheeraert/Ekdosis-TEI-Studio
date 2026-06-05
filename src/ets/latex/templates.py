from __future__ import annotations

MINIMAL_PREAMBLE = r"""\documentclass{book}
\usepackage[main=french,spanish,latin]{babel}
\usepackage[T1]{fontenc}
\usepackage{fontspec}
\usepackage{csquotes}
\usepackage[teiexport, divs=ekdosis, poetry=verse]{ekdosis}

\SetLineation{
  lineation=none,
  modulo,
  vmodulo=0
}

\newcommand{\stage}[1]{\par\begin{center}\textsc{#1}\end{center}\par}
\newenvironment{speech}{\par}{\par}
\newcommand{\speaker}[1]{\vspace{1em}\large\centering\textsc{#1}\par}
\newcommand{\didas}[1]{\par\begin{center}\textit{#1}\end{center}\par}
\ExplSyntaxOn
\seq_new:N \l_ets_verse_number_parts_seq
\bool_new:N \l_ets_print_verse_number_bool
\cs_new_protected:Npn \ets_vnum:nn #1#2
  {
    \group_begin:
      \seq_set_split:Nnn \l_ets_verse_number_parts_seq {.} {#1}
      \tl_set:Nx \l_tmpa_tl { \seq_item:Nn \l_ets_verse_number_parts_seq {1} }
      \tl_set:Nx \l_tmpb_tl { \seq_item:Nn \l_ets_verse_number_parts_seq {2} }
      \bool_set_false:N \l_ets_print_verse_number_bool
      \int_compare:nNnT { \l_tmpa_tl } > { 0 }
        {
          \int_compare:nNnT { \int_mod:nn { \l_tmpa_tl } { 5 } } = { 0 }
            {
              \bool_set_true:N \l_ets_print_verse_number_bool
              \tl_if_blank:VF \l_tmpb_tl
                {
                  \str_if_eq:VnF \l_tmpb_tl {1}
                    { \bool_set_false:N \l_ets_print_verse_number_bool }
                }
            }
        }
      \bool_if:NT \l_ets_print_verse_number_bool
        { \makebox[0pt][r]{\scriptsize \l_tmpa_tl\quad} }
      #2\par
    \group_end:
  }
\cs_new_protected:Npn \vnum #1#2
  {
    \ets_vnum:nn {#1} {#2}
  }
\ExplSyntaxOff
"""


def wrap_standalone(fragment: str) -> str:
    body = fragment.rstrip()
    return f"{MINIMAL_PREAMBLE}\n\\begin{{document}}\n\\begin{{ekdosis}}\n{body}\n\\end{{ekdosis}}\n\\end{{document}}\n"
