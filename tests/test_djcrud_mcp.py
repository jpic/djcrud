"""Tests for djcrud_mcp — host MCP profiles and ViewSet discovery."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

pytestmark = [pytest.mark.drf]

SAMPLE_SCHEMA = {
    "paths": {
        "/api/product/": {
            "get": {
                "operationId": "product_list",
                "summary": "List products",
                "parameters": [],
            },
            "post": {
                "operationId": "product_create",
                "summary": "Create product",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                },
                                "required": ["name"],
                            }
                        }
                    }
                },
            },
        },
        "/api/product/{id}/": {
            "get": {
                "operationId": "product_retrieve",
                "summary": "Retrieve product",
                "parameters": [{"name": "id", "in": "path", "required": True}],
            },
            "patch": {
                "operationId": "product_partial_update",
                "summary": "Partial update product",
                "parameters": [{"name": "id", "in": "path", "required": True}],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {"name": {"type": "string"}},
                            }
                        }
                    }
                },
            },
            "delete": {
                "operationId": "product_destroy",
                "summary": "Delete product",
                "parameters": [{"name": "id", "in": "path", "required": True}],
            },
        },
        "/api/article/{id}/publish/": {
            "post": {
                "operationId": "article_publish",
                "summary": "Publish article",
                "parameters": [{"name": "id", "in": "path", "required": True}],
            },
        },
        "/api/login/": {
            "post": {"operationId": "login_create", "summary": "Login"},
        },
    }
}


def test_tool_name():
    from djcrud_client.tools import tool_name

    assert tool_name("Product", "list") == "product_list"
    assert tool_name("Article", "partial_update") == "article_partial_update"


def test_api_path_for_viewset():
    from djcrud_example.drf_example.djcrud import ProductViewSet
    from djcrud_mcp.viewsets import api_path_for

    assert api_path_for(ProductViewSet) == "/api/product/"


def test_discover_viewsets_includes_product(drf_settings):
    from djcrud_example.drf_example.djcrud import ProductViewSet
    from djcrud_mcp.viewsets import discover_viewsets

    viewsets = discover_viewsets()
    assert ProductViewSet in viewsets


def test_build_tools_from_api_prefixes():
    from djcrud_client import McpProfile
    from djcrud_client.schema import build_tools_for_profile

    profile = McpProfile.from_dict(
        {
            "key": "items",
            "server_name": "test",
            "instructions": "test",
            "info_tool_name": "info",
            "api_prefixes": ["/api/product/"],
            "meta": {},
        }
    )
    tools = build_tools_for_profile(SAMPLE_SCHEMA, profile)
    names = {tool["name"] for tool in tools}
    assert "product_list" in names
    assert "product_create" in names


def test_build_tools_from_schema_prefix_map():
    from djcrud_client.schema import build_tools_from_schema

    tools = build_tools_from_schema(
        SAMPLE_SCHEMA,
        prefixes={
            "product": "/api/product/",
            "article": "/api/article/",
        },
    )
    names = {tool["name"] for tool in tools}
    assert names == {
        "product_list",
        "product_create",
        "product_retrieve",
        "product_partial_update",
        "product_destroy",
        "article_publish",
    }
    create_tool = next(tool for tool in tools if tool["name"] == "product_create")
    assert "name" in create_tool["input_schema"]["properties"]
    assert "name" in create_tool["input_schema"]["required"]


def test_registry_profile_filters_viewsets():
    from djcrud_example.drf_example.djcrud import ProductViewSet
    from djcrud_example.drf_example.article_viewset import ArticleViewSet
    from djcrud_mcp import McpProfile
    from djcrud_mcp.profiles import resolve_profile_viewsets

    class ProductsOnlyMcp(McpProfile):
        key = "products"
        viewsets = (ProductViewSet,)

    profile = ProductsOnlyMcp()
    resolved = resolve_profile_viewsets(
        profile, all_viewsets=[ProductViewSet, ArticleViewSet]
    )
    assert resolved == [ProductViewSet]


def test_split_arguments_openapi3():
    from djcrud_client.tools import render_path, split_arguments

    operation = SAMPLE_SCHEMA["paths"]["/api/product/{id}/"]["patch"]
    path_args, body = split_arguments(
        "/api/product/{id}/",
        operation,
        {"id": 3, "name": "updated"},
    )
    assert path_args == {"id": 3}
    assert body == {"name": "updated"}
    assert render_path("/api/product/{id}/", path_args) == "/api/product/3/"


def test_site_register_builds_profile():
    from djcrud_mcp import McpProfile, site

    class ArticlesMcp(McpProfile):
        key = "articles"
        api_prefixes = ("/api/article/",)

    site.clear()
    try:
        site.register(ArticlesMcp)
        profile = site.get_profile("articles", do_resolve=False)
        assert profile.server_name.endswith("-articles")
        assert profile.info_tool_name == "article_registry_info"
        assert profile.instructions == "CRUD for article via the JSON API."
        assert profile.api_prefixes == ("/api/article/",)
    finally:
        site.clear()


def test_profile_to_dict_wire_format():
    from djcrud_mcp import McpProfile
    from djcrud_client import McpProfile as RemoteProfile

    class ArticlesMcp(McpProfile):
        key = "articles"
        api_prefixes = ("/api/article/",)

    with patch("djcrud_mcp.profiles._host_slug", return_value=None):
        profile = ArticlesMcp().build(do_resolve=False)
        wire = profile.to_dict()
        restored = RemoteProfile.from_dict(wire)
        assert restored.to_dict() == wire


def test_auto_generates_server_name():
    from djcrud_mcp import McpProfile

    class ProductOnlyMcp(McpProfile):
        key = "products"
        api_prefixes = ("/api/product/",)

    with patch("djcrud_mcp.profiles._host_slug", return_value=None):
        profile = ProductOnlyMcp().build(do_resolve=False)
        assert profile.server_name == "products"
    assert profile.info_tool_name == "product_registry_info"
    assert profile.instructions == "CRUD for product via the JSON API."

    with patch("djcrud_mcp.profiles._host_slug", return_value="myapp"):
        profile = ProductOnlyMcp().build(do_resolve=False)
        assert profile.server_name == "myapp-products"


@pytest.mark.django_db
def test_create_mcp_server_from_live_schema(api_client, drf_settings, django_user_model):
    from djcrud_api.models import Token
    from djcrud_client.server import create_mcp_server

    user = django_user_model.objects.get(username="apiuser")
    _, raw_key = Token.generate(user=user, name="mcp")

    response = api_client.get("/api/schema/", HTTP_ACCEPT="application/json")
    schema = response.json()

    with patch("djcrud_client.server.fetch_schema", return_value=schema):
        with patch(
            "djcrud_client.server.load_profile",
            return_value=__import__("djcrud_client", fromlist=["McpProfile"]).McpProfile.from_dict(
                {
                    "key": "default",
                    "server_name": "djcrud",
                    "instructions": "CRUD tools",
                    "info_tool_name": "registry_info",
                    "api_prefixes": ["/api/product/", "/api/article/"],
                    "meta": {},
                }
            ),
        ):
            mcp = create_mcp_server(base_url="http://testserver", token=raw_key)

    tool_names = set(mcp._tool_manager._tools.keys())
    assert "product_list" in tool_names
    assert "product_create" in tool_names
    assert "article_publish" in tool_names


@pytest.mark.django_db
def test_mcp_tool_calls_api(api_client, drf_settings, django_user_model):
    from djcrud_api.models import Token
    from djcrud_client import McpProfile
    from djcrud_client.server import create_mcp_server

    user = django_user_model.objects.get(username="apiuser")
    _, raw_key = Token.generate(user=user, name="mcp")

    response = api_client.get("/api/schema/", HTTP_ACCEPT="application/json")
    schema = response.json()
    profile = McpProfile.from_dict(
        {
            "key": "default",
            "server_name": "djcrud",
            "instructions": "CRUD tools",
            "info_tool_name": "registry_info",
            "api_prefixes": ["/api/product/"],
            "meta": {},
        }
    )

    with patch("djcrud_client.server.fetch_schema", return_value=schema):
        mcp = create_mcp_server(
            base_url="http://testserver",
            token=raw_key,
            profile=profile,
        )

    handler = mcp._tool_manager._tools["product_create"].fn
    with patch("djcrud_client.api.httpx.Client") as client_cls:
        response = client_cls.return_value.__enter__.return_value.request
        response.return_value.json.return_value = {"id": 1, "name": "widget"}
        response.return_value.status_code = 201
        result = handler(name="widget")
    payload = json.loads(result)
    assert payload["name"] == "widget"


@pytest.mark.django_db
def test_mcp_profiles_endpoint(api_client, drf_settings):
    from djcrud_mcp import McpProfile, site

    class ArticlesMcp(McpProfile):
        key = "articles"
        api_prefixes = ("/api/article/",)

    site.clear()
    try:
        site.register(ArticlesMcp)
        response = api_client.get("/api/mcp/profiles/")
        assert response.status_code == 200
        payload = response.json()
        assert "articles" in payload["profiles"]
        assert payload["default"] == "articles"

        detail = api_client.get("/api/mcp/profiles/articles/")
        assert detail.status_code == 200
        assert detail.json()["server_name"].endswith("-articles")
    finally:
        site.clear()