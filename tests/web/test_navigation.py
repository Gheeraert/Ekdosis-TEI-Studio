"""Tests de navigation : micro-passe ergonomique Constructeur de site."""

from __future__ import annotations

import pytest

from ets.web import create_app


@pytest.fixture()
def client():
    app = create_app(testing=True)
    with app.test_client() as c:
        yield c


def test_main_nav_present_on_index(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    assert "Établi de saisie" in html
    assert "Constructeur de site" in html
    assert "À propos d'ETS" in html


def test_builder_page_has_subnav_mode_normal_and_expert(client) -> None:
    rv = client.get("/publish/builder")
    html = rv.data.decode()
    assert "Mode normal" in html
    assert "Mode expert" in html


def test_static_page_has_subnav_mode_normal_and_expert(client) -> None:
    rv = client.get("/publish/static")
    html = rv.data.decode()
    assert "Mode normal" in html
    assert "Mode expert" in html


def test_main_nav_no_longer_contains_publication_zip(client) -> None:
    rv = client.get("/")
    assert "Publication ZIP" not in rv.data.decode()


def test_constructeur_link_points_to_builder(client) -> None:
    rv = client.get("/")
    html = rv.data.decode()
    assert 'href="/publish/builder"' in html


def test_publish_static_still_accessible(client) -> None:
    rv = client.get("/publish/static")
    assert rv.status_code == 200


def test_builder_mode_normal_is_active_on_builder_page(client) -> None:
    rv = client.get("/publish/builder")
    html = rv.data.decode()
    import re
    active_links = re.findall(r'<a[^>]+class="active"[^>]*>([^<]+)</a>', html)
    assert "Mode normal" in active_links


def test_static_mode_expert_is_active_on_static_page(client) -> None:
    rv = client.get("/publish/static")
    html = rv.data.decode()
    import re
    active_links = re.findall(r'<a[^>]+class="active"[^>]*>([^<]+)</a>', html)
    assert "Mode expert" in active_links
