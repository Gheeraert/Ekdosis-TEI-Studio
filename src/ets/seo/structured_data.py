from __future__ import annotations

import json

# HTML parsing closes a <script> element on ANY case variant of "</script",
# regardless of the script's type attribute or the surrounding JSON syntax.
# Escaping every "<" (and, defensively, ">" and "&") as a JSON unicode escape
# neutralizes that terminator wherever it could appear in free editorial
# text (title, author, description), independently of case.
_SCRIPT_UNSAFE_ESCAPES = {
    "<": "\\u003c",
    ">": "\\u003e",
    "&": "\\u0026",
}


def _escape_for_script_context(payload: str) -> str:
    for unsafe, escaped in _SCRIPT_UNSAFE_ESCAPES.items():
        payload = payload.replace(unsafe, escaped)
    return payload


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
    safe_payload = _escape_for_script_context(payload)
    return f'<script type="application/ld+json">{safe_payload}</script>'
