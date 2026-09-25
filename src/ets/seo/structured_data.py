from __future__ import annotations

import json


def book_json_ld_html(
    *,
    title: str,
    author: str | None,
    url: str | None,
    description: str = "",
    site_name: str = "",
    language: str = "fr",
) -> str:
    """Build a schema.org Book JSON-LD <script> tag for one play page.

    Returns an empty string when ``url`` is not available: like Open Graph,
    rich-result structured data is only meaningful with an absolute URL.
    """
    if not url:
        return ""

    data: dict[str, object] = {
        "@context": "https://schema.org",
        "@type": "Book",
        "name": title,
        "url": url,
        "inLanguage": language,
    }
    if author:
        data["author"] = {"@type": "Person", "name": author}
    if description:
        data["description"] = description
    if site_name:
        data["publisher"] = {"@type": "Organization", "name": site_name}

    payload = json.dumps(data, ensure_ascii=False, indent=2)
    # </script> can never appear in valid JSON-LD content, but escape it
    # defensively since the payload embeds free editorial text.
    safe_payload = payload.replace("</script", "<\\/script")
    return f'<script type="application/ld+json">{safe_payload}</script>'
