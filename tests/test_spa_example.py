from pathlib import Path

import pytest
from django.urls import reverse

pytestmark = pytest.mark.tutorial


@pytest.mark.django_db
def test_spa_renders_server_navigation(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("site:spa"))
    assert response.status_code == 200
    content = response.content.decode()
    assert 'id="sidebar"' in content
    assert "is-hidden" in content
    assert "menu-list" in content
    assert 'href="/item/"' in content
    assert 'up-follow="false"' in content
    assert "hamburger-menu" not in content
    assert "spa_example/js/app.js" in content
    app_js = (
        Path(__file__).resolve().parents[1]
        / "src/djcrud_example/spa_example/static/spa_example/js/app.js"
    ).read_text()
    assert "hamburger-menu" in app_js
    assert "navbar-brand" in app_js


@pytest.mark.django_db
def test_spa_requires_login(client):
    response = client.get(reverse("site:spa"))
    assert response.status_code == 302
    assert "/auth/login/" in response["Location"]


@pytest.mark.django_db
def test_spa_renders_default_mount_node(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("site:spa"))
    assert response.status_code == 200
    assert '<div id="app"></div>' in response.content.decode()


@pytest.mark.django_db
def test_spa_standard_list_still_uses_navbar(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("site:item:list"))
    assert response.status_code == 200
    assert b'<nav class="navbar"' in response.content