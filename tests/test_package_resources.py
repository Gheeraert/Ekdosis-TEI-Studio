from __future__ import annotations

from importlib import resources


def test_tei_profile_resources_are_packaged() -> None:
    root = resources.files("ets.resources")
    for relative_path in (
        "odd/ets-racine.odd",
        "schemas/ets-racine.rnc",
        "schemas/ets-racine.sch",
    ):
        resource = root.joinpath(*relative_path.split("/"))
        assert resource.is_file()
        assert resource.read_text(encoding="utf-8").strip()
