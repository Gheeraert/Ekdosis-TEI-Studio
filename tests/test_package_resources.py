from __future__ import annotations

from importlib import resources


def test_tei_profile_resources_are_packaged() -> None:
    root = resources.files("ets.resources")
    for relative_path in (
        "odd/ets-racine.odd",
        "schemas/ets-racine.rnc",
        "schemas/ets-racine.sch",
        "schemas/tei_all.rng",
        "xslt/tei-vers-html.xsl",
    ):
        resource = root.joinpath(*relative_path.split("/"))
        assert resource.is_file()
        assert resource.read_text(encoding="utf-8").strip()


def test_embedded_fonts_are_packaged() -> None:
    root = resources.files("ets.resources")
    for filename in (
        "eb-garamond-latin.woff2",
        "eb-garamond-latin-ext.woff2",
        "im-fell-dw-pica-latin.woff2",
        "source-sans-pro-latin.woff2",
        "source-sans-pro-latin-ext.woff2",
    ):
        resource = root.joinpath("fonts", filename)
        assert resource.is_file()
        assert resource.read_bytes()[:4] == b"wOF2"
    assert root.joinpath("fonts", "LICENCES.md").is_file()
    ofl = root.joinpath("fonts", "OFL.txt")
    assert ofl.is_file()
    assert "SIL OPEN FONT LICENSE" in ofl.read_text(encoding="utf-8")
