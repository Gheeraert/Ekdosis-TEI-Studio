from __future__ import annotations

from ets.seo import ODD_RELPATH, describedby_link_html


def test_describedby_link_uses_relative_path_by_default() -> None:
    html_fragment = describedby_link_html()

    assert html_fragment == (
        f'<link rel="describedby" href="{ODD_RELPATH}" type="application/xml">'
    )


def test_describedby_link_honors_relative_prefix() -> None:
    html_fragment = describedby_link_html("../")

    assert f'href="../{ODD_RELPATH}"' in html_fragment
    assert "https://" not in html_fragment
