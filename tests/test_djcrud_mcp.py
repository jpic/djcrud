"""Tests for djcrud_mcp — ViewSet-based MCP tool discovery."""

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
    from djcrud_mcp.tools import tool_name

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


def test_filter_paths_by_registered_viewsets():
    from djcrud_example.drf_example.djcrud import ProductViewSet
    from djcrud_example.drf_example.article_viewset import ArticleViewSet
    from djcrud_mcp.schema import filter_paths_by_viewsets

    paths = filter_paths_by_viewsets(
        SAMPLE_SCHEMA,
        viewsets=[ProductViewSet, ArticleViewSet],
    )
    assert "/api/product/" in paths
    assert "/api/product/{id}/" in paths
    assert "/api/article/{id}/publish/" in paths
    assert "/api/login/" not in paths


def test_build_tools_from_schema():
    from djcrud_example.drf_example.djcrud import ProductViewSet
    from djcrud_example.drf_example.article_viewset import ArticleViewSet
    from djcrud_mcp.schema import build_tools_from_schema

    tools = build_tools_from_schema(
        SAMPLE_SCHEMA,
        viewsets=[ProductViewSet, ArticleViewSet],
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


def test_build_tools_from_api_prefixes():
    from djcrud_mcp.profiles import RegistryProfile
    from djcrud_mcp.schema import build_tools_for_profile

    profile = RegistryProfile(
        key="items",
        server_name="test",
        instructions="test",
        info_tool_name="info",
        api_prefixes=("/api/product/",),
    )
    tools = build_tools_for_profile(SAMPLE_SCHEMA, profile)
    names = {tool["name"] for tool in tools}
    assert "product_list" in names
    assert "product_create" in names


def test_registry_profile_filters_viewsets():
    from djcrud_example.drf_example.djcrud import ProductViewSet
    from djcrud_example.drf_example.article_viewset import ArticleViewSet
    from djcrud_mcp.profiles import RegistryProfile, resolve_viewsets

    profile = RegistryProfile(
        key="products",
        server_name="test-products",
        viewsets=(ProductViewSet,),
        instructions="Products only.",
        info_tool_name="product_registry_info",
    )
    resolved = resolve_viewsets(profile, all_viewsets=[ProductViewSet, ArticleViewSet])
    assert resolved == [ProductViewSet]


def test_split_arguments_openapi3():
    from djcrud_mcp.tools import render_path, split_arguments

    operation = SAMPLE_SCHEMA["paths"]["/api/product/{id}/"]["patch"]
    path_args, body = split_arguments(
        "/api/product/{id}/",
        operation,
        {"id": 3, "name": "updated"},
    )
    assert path_args == {"id": 3}
    assert body == {"name": "updated"}
    assert render_path("/api/product/{id}/", path_args) == "/api/product/3/"


@pytest.mark.django_db
def test_create_mcp_server_from_live_schema(api_client, drf_settings, django_user_model):
    from djcrud_api.models import Token
    from djcrud_mcp.server import create_mcp_server

    user = django_user_model.objects.get(username="apiuser")
    _, raw_key = Token.generate(user=user, name="mcp")

    response = api_client.get("/api/schema/", HTTP_ACCEPT="application/json")
    schema = response.json()

    with patch("djcrud_mcp.server.fetch_schema", return_value=schema):
        mcp = create_mcp_server(base_url="http://testserver", token=raw_key)

    tool_names = set(mcp._tool_manager._tools.keys())
    assert "product_list" in tool_names
    assert "product_create" in tool_names
    assert "article_publish" in tool_names


@pytest.mark.django_db
def test_mcp_tool_calls_api(api_client, drf_settings, django_user_model):
    from djcrud_api.models import Token
    from djcrud_mcp.server import create_mcp_server

    user = django_user_model.objects.get(username="apiuser")
    _, raw_key = Token.generate(user=user, name="mcp")

    response = api_client.get("/api/schema/", HTTP_ACCEPT="application/json")
    schema = response.json()

    with patch("djcrud_mcp.server.fetch_schema", return_value=schema):
        mcp = create_mcp_server(base_url="http://testserver", token=raw_key)

    handler = mcp._tool_manager._tools["product_create"].fn
    with patch("djcrud_mcp.api.httpx.Client") as client_cls:
        response = client_cls.return_value.__enter__.return_value.request
        response.return_value.json.return_value = {"id": 1, "name": "widget"}
        response.return_value.status_code = 201
        result = handler(name="widget")
    payload = json.loads(result)
    assert payload["name"] == "widget"


def test_custom_action_from_schema():
    from djcrud_mcp.profiles import RegistryProfile
    from djcrud_mcp.server import create_mcp_server

    profile = RegistryProfile(
        key="custom",
        server_name="test-custom",
        instructions="Custom tools.",
        info_tool_name="custom_registry_info",
        api_prefixes=("/api/product/", "/api/article/"),
    )

    with patch("djcrud_mcp.server.fetch_schema", return_value=SAMPLE_SCHEMA):
        mcp = create_mcp_server(
            base_url="http://testserver",
            token="tok",
            profile=profile,
        )

    assert "article_publish" in mcp._tool_manager._tools
    assert "custom_registry_info" in mcp._tool_manager._tools