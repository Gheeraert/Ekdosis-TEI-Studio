from __future__ import annotations

import html as std_html

ODD_RELPATH = "tei-profile/ets-racine.odd"


def describedby_link_html(relpath_prefix: str = "") -> str:
    """Build a <link rel="describedby"> pointing to the published TEI ODD schema.

    Relative by design (digital-humanities convention, not a search-engine
    signal): the ODD is already published at ``tei-profile/ets-racine.odd``
    by the site builder regardless of the SEO configuration, so this never
    depends on ``site_base_url``.
    """
    href = std_html.escape(f"{relpath_prefix}{ODD_RELPATH}", quote=True)
    return f'<link rel="describedby" href="{href}" type="application/xml">'
