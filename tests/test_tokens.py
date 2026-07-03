import json
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.utils import timezone

from djcrud_api.models import Token


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="tokenuser",
        email="token@example.com",
        password="secret",
    )


@pytest.fixture
def other_user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="otheruser",
        email="other@example.com",
        password="secret",
    )


@pytest.fixture
def token_perms(user):
    content_type = ContentType.objects.get_for_model(Token)
    for codename in ("view_token", "add_token", "delete_token"):
        perm = Permission.objects.get(
            content_type=content_type,
            codename=codename,
        )
        user.user_permissions.add(perm)
    return user


@pytest.fixture
def item_perms(user):
    from djcrud_example.routing_example.models import Item

    content_type = ContentType.objects.get_for_model(Item)
    for codename in ("view_item", "add_item", "change_item", "delete_item"):
        perm = Permission.objects.get(
            content_type=content_type,
            codename=codename,
        )
        user.user_permissions.add(perm)
    return user


@pytest.fixture
def product_perms(user):
    from djcrud_example.drf_example.models import Product

    content_type = ContentType.objects.get_for_model(Product)
    for codename in ("view_product", "add_product", "change_product", "delete_product"):
        perm = Permission.objects.get(
            content_type=content_type,
            codename=codename,
        )
        user.user_permissions.add(perm)
    return user


def bearer_headers(token):
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def csrf_headers(client, url="/api/token/create/"):
    response = client.get(url)
    return {"HTTP_X_CSRFTOKEN": response.cookies["csrftoken"].value}


@pytest.mark.django_db
def test_api_login(user):
    client = Client()
    response = client.post(
        "/api/login/",
        data=json.dumps({"username": "tokenuser", "password": "secret"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "expires" in data
    assert Token.objects.filter(user=user, name="API login").count() == 1


@pytest.mark.django_db
def test_api_login_invalid(user):
    client = Client()
    response = client.post(
        "/api/login/",
        data=json.dumps({"username": "tokenuser", "password": "wrong"}),
        content_type="application/json",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_expired_bearer_rejected(user, item_perms):
    token, raw_key = Token.generate(
        user=user,
        name="expired",
        expires=timezone.now() - timedelta(minutes=1),
    )
    assert token.pk

    client = Client()
    response = client.get("/item/", **bearer_headers(raw_key))
    assert response.status_code == 302


@pytest.mark.django_db
@pytest.mark.drf
def test_bearer_crud_without_csrf(user, product_perms, drf_settings):
    from djcrud.permissions import _lookup_perm
    from djcrud_example.drf_example.models import Product

    assert user.has_perm("drf_example.change_product")
    assert _lookup_perm(Product, "change", "drf_example.change_product") is None
    token, raw_key = Token.generate(user=user, name="crud")
    client = Client()

    response = client.post(
        "/api/product/",
        data=json.dumps({"name": "bearer product"}),
        content_type="application/json",
        **bearer_headers(raw_key),
    )
    assert response.status_code == 201

    response = client.get(
        "/api/product/",
        **bearer_headers(raw_key),
    )
    pk = response.json()[0]["id"]

    response = client.patch(
        f"/api/product/{pk}/",
        data=json.dumps({"name": "updated bearer product"}),
        content_type="application/json",
        **bearer_headers(raw_key),
    )
    assert response.status_code == 200, response.content

    response = client.delete(
        f"/api/product/{pk}/",
        **bearer_headers(raw_key),
    )
    assert response.status_code == 204


@pytest.mark.django_db
def test_html_token_create(client, user, token_perms):
    client.force_login(user)
    headers = csrf_headers(client)
    response = client.post(
        "/api/token/create/",
        data={"name": "CI deploy", "expires": ""},
        **headers,
    )
    assert response.status_code == 302
    assert Token.objects.filter(user=user, name="CI deploy").count() == 1

    follow = client.get("/api/token/")
    assert b"CI deploy" in follow.content


@pytest.mark.django_db
def test_token_scoping(user, other_user, token_perms):
    _, raw_a = Token.generate(user=user, name="mine")
    Token.generate(user=other_user, name="theirs")

    client = Client()
    response = client.get(
        "/api/token/",
        **bearer_headers(raw_a),
    )
    assert response.status_code == 200
    assert b"mine" in response.content
    assert b"theirs" not in response.content


@pytest.mark.django_db
def test_bearer_delete_token(user, token_perms):
    token, raw_key = Token.generate(user=user, name="revoke-me")
    client = Client()

    response = client.post(
        f"/api/token/{token.pk}/delete/",
        **bearer_headers(raw_key),
    )
    assert response.status_code == 302
    assert not Token.objects.filter(pk=token.pk).exists()