import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

import djcrud
from djcrud_debug.models import Router, URL
from djcrud_debug.routing_debug import RouteCollection, walk_site

User = get_user_model()


def test_walk_site_contains_known_routes():
    data = walk_site(djcrud.site)
    urlnames = {u.urlfullname for u in data["urls"]}
    assert "site:auth:login" in urlnames
    assert "site:item:list" in urlnames


def test_walk_site_contains_known_routers():
    data = walk_site(djcrud.site)
    pks = {c.pk for c in data["routers"]}
    assert "site.auth" in pks
    assert "routing_example.Item" in pks


def test_router_manager_returns_records():
    routers = Router.objects.all()
    assert len(routers) > 0
    assert all(isinstance(r, Router) for r in routers)


def test_url_manager_returns_records():
    urls = URL.objects.all()
    assert len(urls) > 0
    login = URL.objects.get(pk="site:auth:login")
    assert login.fullurlpath == "/auth/login/"
    assert login.view_class == "LoginView"


def test_route_collection_filter_icontains():
    qs = RouteCollection(
        [
            Router(pk="a", app="Auth", model="User", codename="user"),
            Router(pk="b", app="Blog", model="Post", codename="post"),
        ]
    )
    filtered = qs.filter(app__icontains="auth")
    assert len(filtered) == 1
    assert filtered[0].pk == "a"


def test_route_collection_get():
    qs = RouteCollection(
        [
            URL(pk="site:auth:login", urlfullname="site:auth:login"),
        ]
    )
    assert qs.get(pk="site:auth:login").pk == "site:auth:login"


@pytest.mark.django_db
def test_url_list_superuser(admin_client):
    response = admin_client.get("/debug/url/")
    assert response.status_code == 200
    assert b"site:auth:login" in response.content


@pytest.mark.django_db
def test_router_list_superuser(admin_client):
    response = admin_client.get("/debug/router/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_url_list_forbidden_for_regular_user(client, db):
    User.objects.create_user(username="user", password="pass")
    client.login(username="user", password="pass")
    response = client.get("/debug/url/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_url_list_forbidden_anonymous(client):
    response = client.get("/debug/url/")
    assert response.status_code == 302
    assert response["Location"].startswith("/auth/login/")


@pytest.mark.django_db
def test_url_detail_superuser(admin_client):
    url = reverse("site:debug:url:detail", args=["site:auth:login"])
    response = admin_client.get(url)
    assert response.status_code == 200
    assert b"/auth/login/" in response.content
