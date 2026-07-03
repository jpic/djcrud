"""Tests for djcrud-mcp without Django."""

from __future__ import annotations

import subprocess
import sys
from unittest.mock import patch

import pytest

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
                                "properties": {"name": {"type": "string"}},
                                "required": ["name"],
                            }
                        }
                    }
                },
            },
        },
    }
}


def test_imports_no_django():
    script = """
import sys
for name in list(sys.modules):
    if name.startswith("django"):
        del sys.modules[name]
import djcrud_mcp.server
assert not [name for name in sys.modules if name.startswith("django")]
"""
    subprocess.run([sys.executable, "-c", script], check=True)


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
    assert names == {"product_list", "product_create"}


def test_create_mcp_server_with_api_prefixes():
    from djcrud_mcp.extras import ExtraTool
    from djcrud_mcp.profiles import RegistryProfile
    from djcrud_mcp.server import create_mcp_server

    profile = RegistryProfile(
        key="custom",
        server_name="test-custom",
        instructions="Custom tools.",
        info_tool_name="custom_registry_info",
        api_prefixes=("/api/product/",),
        extra_tools=(
            ExtraTool(
                name="ping",
                method="get",
                path="/api/ping/",
                description="Health ping",
            ),
        ),
    )

    with patch("djcrud_mcp.server.fetch_schema", return_value=SAMPLE_SCHEMA):
        mcp = create_mcp_server(
            base_url="http://testserver",
            token="tok",
            profile=profile,
        )

    tool_names = set(mcp._tool_manager._tools.keys())
    assert "product_list" in tool_names
    assert "ping" in tool_names
    assert "custom_registry_info" in tool_names


def test_profile_meta_uses_api_prefixes():
    from djcrud_mcp.profiles import RegistryProfile, profile_meta

    profile = RegistryProfile(
        key="items",
        server_name="test",
        instructions="test",
        info_tool_name="info",
        api_prefixes=("/api/product/",),
    )
    meta = profile_meta(profile)
    assert meta["api_prefixes"] == ["/api/product/"]
    assert "viewsets" not in meta


def test_discover_viewsets_requires_django_stack():
    from djcrud_mcp.viewsets import discover_viewsets

    with pytest.raises(ImportError, match="djcrud\\[drf\\]"):
        discover_viewsets()