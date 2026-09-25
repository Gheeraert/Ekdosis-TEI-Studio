from __future__ import annotations

import html as std_html


def open_graph_head_html(
    *,
    title: str,
    description: str,
    url: str | None,
    site_name: str,
    image_url: str | None = None,
    locale: str = "fr_FR",
) -> str:
    """Build Open Graph / Twitter Card <meta> tags for one page.

    Returns an empty string when ``url`` is not available: Open Graph and
    Twitter Card both require an absolute URL, so there is no partial
    degradation here (unlike the canonical link, which is simply omitted).
    """
    if not url:
        return ""

    def esc(value: str) -> str:
        return std_html.escape(value, quote=True)

    tags = [
        '<meta property="og:type" content="website">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:url" content="{esc(url)}">',
        f'<meta property="og:site_name" content="{esc(site_name)}">',
        f'<meta property="og:locale" content="{esc(locale)}">',
    ]
    if description:
        tags.append(f'<meta property="og:description" content="{esc(description)}">')
    if image_url:
        tags.append(f'<meta property="og:image" content="{esc(image_url)}">')

    twitter_card = "summary_large_image" if image_url else "summary"
    tags.append(f'<meta name="twitter:card" content="{twitter_card}">')
    tags.append(f'<meta name="twitter:title" content="{esc(title)}">')
    if description:
        tags.append(f'<meta name="twitter:description" content="{esc(description)}">')
    if image_url:
        tags.append(f'<meta name="twitter:image" content="{esc(image_url)}">')

    return "".join(tags)
