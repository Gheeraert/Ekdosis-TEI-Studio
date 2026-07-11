from __future__ import annotations


RELEDMAC_SUPPORT_PREAMBLE = r"""\usepackage[
  series={A},
  noend,
  noeledsec,
  noledgroup,
  nofamiliar
]{reledmac}

\Xarrangement[A]{paragraph}
\newcommand{\PURHApparatusSize}{%
  \fontsize{7.4}{8.4}\selectfont
}
\Xnotefontsize[A]{\PURHApparatusSize}
\AtBeginDocument{%
  \Xmaxhnotes[A]{0.8\textheight}%
}
\firstlinenum{100000}
\linenumincrement{100000}
\setstanzaindents{0,0}
\setcounter{stanzaindentsrepetition}{1}

\newcommand{\stage}[1]{\par\begin{center}\textsc{#1}\end{center}\par}
\newenvironment{speech}{\par}{\par}
\newcommand{\speaker}[1]{\vspace{1em}\large\centering\textsc{#1}\par}
\newcommand{\didas}[1]{\par\begin{center}\textit{#1}\end{center}\par}
\newcommand{\PURHAct}[1]{\stage{#1}}
\newcommand{\PURHScene}[1]{\stage{#1}}
\newcommand{\PURHSharedVerseIndentTwo}{\hspace*{5em}}
\newcommand{\PURHSharedVerseIndentThree}{\hspace*{7em}}
\ExplSyntaxOn
\seq_new:N \l_ets_reledmac_verse_number_parts_seq
\bool_new:N \l_ets_reledmac_print_verse_number_bool
\cs_new_protected:Npn \ets_reledmac_verse:nn #1#2
  {
    \group_begin:
      \seq_set_split:Nnn \l_ets_reledmac_verse_number_parts_seq {.} {#1}
      \tl_set:Nx \l_tmpa_tl { \seq_item:Nn \l_ets_reledmac_verse_number_parts_seq {1} }
      \tl_set:Nx \l_tmpb_tl { \seq_item:Nn \l_ets_reledmac_verse_number_parts_seq {2} }
      \bool_set_false:N \l_ets_reledmac_print_verse_number_bool
      \int_compare:nNnT { \l_tmpa_tl } > { 0 }
        {
          \int_compare:nNnT { \int_mod:nn { \l_tmpa_tl } { 5 } } = { 0 }
            {
              \bool_set_true:N \l_ets_reledmac_print_verse_number_bool
              \tl_if_blank:VF \l_tmpb_tl
                {
                  \str_if_eq:VnF \l_tmpb_tl {1}
                    { \bool_set_false:N \l_ets_reledmac_print_verse_number_bool }
                }
            }
        }
      \bool_if:NT \l_ets_reledmac_print_verse_number_bool
        { \makebox[0pt][r]{\scriptsize \l_tmpa_tl\quad} }
      \tl_if_blank:VF \l_tmpb_tl
        {
          \str_case:Vn \l_tmpb_tl
            {
              {2}{\PURHSharedVerseIndentTwo}
              {3}{\PURHSharedVerseIndentThree}
            }
        }
      #2
    \group_end:
  }
\cs_new_protected:Npn \PURHVerse #1#2
  {
    \ets_reledmac_verse:nn {#1} {#2}
  }
\ExplSyntaxOff
"""


def render_reledmac_support_preamble() -> str:
    return RELEDMAC_SUPPORT_PREAMBLE
