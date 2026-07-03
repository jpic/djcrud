"""Tests for auto-generated McpProfile defaults."""

from __future__ import annotations

from unittest.mock import patch

from djcrud_mcp import McpProfile


class ProductOnlyMcp(McpProfile):
    key = "products"
    api_prefixes = ("/api/product/",)


def test_auto_generates_server_name_instructions_and_info_tool():
    profile = ProductOnlyMcp().build(resolve_viewsets=False)
    assert profile.server_name == "products"
    assert profile.info_tool_name == "product_registry_info"
    assert profile.instructions == "CRUD for product via the JSON API."
    assert profile.meta["name"] == "products"


def test_host_slug_prefixes_server_name():
    with patch("djcrud_mcp.profiles._host_slug", return_value="myapp"):
        profile = ProductOnlyMcp().build(resolve_viewsets=False)
        assert profile.server_name == "myapp-products"