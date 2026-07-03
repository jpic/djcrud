import json

import pytest
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model

from djcrud.views.log import ADDITION, CHANGE, DELETION

pytestmark = pytest.mark.drf


@pytest.mark.django_db
def test_drf_create_logs_addition(api_client):
    from djcrud_example.drf_example.models import Product

    before = LogEntry.objects.count()
    response = api_client.post(
        "/api/product/",
        data=json.dumps({"name": "logged product"}),
        content_type="application/json",
    )
    assert response.status_code == 201
    obj = Product.objects.get(name="logged product")

    assert LogEntry.objects.count() == before + 1
    entry = LogEntry.objects.filter(object_id=str(obj.pk)).get()
    assert entry.action_flag == ADDITION
    data = json.loads(entry.change_message)
    assert data["extra"]["path"] == "/api/product/"
    assert data["extra"]["view"] == "ProductViewSet"


@pytest.mark.django_db
def test_drf_update_logs_changed_fields(api_client):
    from djcrud_example.drf_example.models import Product

    product = Product.objects.create(name="before")
    response = api_client.patch(
        f"/api/product/{product.pk}/",
        data=json.dumps({"name": "after"}),
        content_type="application/json",
    )
    assert response.status_code == 200

    entry = LogEntry.objects.filter(object_id=str(product.pk)).get()
    assert entry.action_flag == CHANGE
    data = json.loads(entry.change_message)
    assert data["changes"] == [{"changed": {"fields": ["Name"]}}]


@pytest.mark.django_db
def test_drf_delete_logs_deletion(api_client):
    from djcrud_example.drf_example.models import Product

    product = Product.objects.create(name="gone")
    pk = product.pk
    response = api_client.delete(f"/api/product/{pk}/")
    assert response.status_code == 204

    entry = LogEntry.objects.filter(object_id=str(pk)).get()
    assert entry.action_flag == DELETION


@pytest.mark.django_db
def test_drf_no_log_when_anonymous(client, drf_settings, db):
    before = LogEntry.objects.count()
    client.post(
        "/api/product/",
        data=json.dumps({"name": "ghost"}),
        content_type="application/json",
    )
    assert LogEntry.objects.count() == before


@pytest.mark.django_db
def test_drf_no_log_when_disabled(api_client, monkeypatch):
    from djcrud_example.drf_example.djcrud import ProductViewSet

    monkeypatch.setattr(ProductViewSet, "log_actions", False)
    before = LogEntry.objects.count()
    response = api_client.post(
        "/api/product/",
        data=json.dumps({"name": "silent"}),
        content_type="application/json",
    )
    assert response.status_code == 201
    assert LogEntry.objects.count() == before


@pytest.mark.django_db
def test_drf_create_list_detail_update_delete(api_client):
    response = api_client.post(
        "/api/product/",
        data=json.dumps({"name": "test product"}),
        content_type="application/json",
    )
    assert response.status_code == 201
    assert response.json()["name"] == "test product"

    response = api_client.get("/api/product/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test product"
    pk = data[0]["id"]

    response = api_client.get(f"/api/product/{pk}/")
    assert response.json()["name"] == "test product"

    response = api_client.patch(
        f"/api/product/{pk}/",
        data=json.dumps({"name": "updated product"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["name"] == "updated product"

    response = api_client.delete(f"/api/product/{pk}/")
    assert response.status_code == 204


@pytest.mark.django_db
def test_drf_schema_lists_product_routes(api_client):
    response = api_client.get(
        "/api/schema/",
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 200
    schema = response.json()
    paths = schema.get("paths", {})
    assert any("product" in path for path in paths)


@pytest.mark.django_db
def test_drf_api_login(client, drf_settings, db):
    User = get_user_model()
    User.objects.create_user(username="apiuser", password="test")

    response = client.post(
        "/api/login/",
        data=json.dumps({"username": "apiuser", "password": "test"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "expires" in data
    assert "prefix" in data


@pytest.mark.django_db
def test_drf_schema_includes_login_and_bearer_auth(api_client):
    response = api_client.get(
        "/api/schema/",
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 200
    schema = response.json()
    paths = schema.get("paths", {})
    assert any(path.rstrip("/").endswith("/login") for path in paths)
    login_path = next(
        path for path in paths if path.rstrip("/").endswith("/login")
    )
    assert "post" in paths[login_path]

    security_schemes = schema.get("components", {}).get("securitySchemes", {})
    assert "BearerAuth" in security_schemes
    assert security_schemes["BearerAuth"]["scheme"] == "bearer"


@pytest.mark.django_db
def test_drf_custom_action_uses_method_name_as_permission_shortcode(
    client, drf_settings, django_user_model
):
    from djcrud_api.models import Token
    from djcrud_drf.viewsets import action_shortcode
    from djcrud_example.views_example.models import Article

    assert action_shortcode("publish") == "publish"

    owner = django_user_model.objects.create_user(username="owner", password="x")
    stranger = django_user_model.objects.create_user(username="stranger", password="x")
    article = Article.objects.create(
        title="Draft",
        published=False,
        owner=owner,
    )
    _, stranger_token = Token.generate(user=stranger, name="api")
    _, owner_token = Token.generate(user=owner, name="api")

    denied = client.post(
        f"/api/article/{article.pk}/publish/",
        HTTP_AUTHORIZATION=f"Bearer {stranger_token}",
    )
    assert denied.status_code == 403

    allowed = client.post(
        f"/api/article/{article.pk}/publish/",
        HTTP_AUTHORIZATION=f"Bearer {owner_token}",
    )
    assert allowed.status_code == 200
    article.refresh_from_db()
    assert article.published is True