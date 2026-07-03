"""Tests for McpProfile classes and site.register()."""

from __future__ import annotations

from djcrud_mcp import McpProfile, site
from djcrud_mcp.profiles import RegistryProfile


class ArticlesMcp(McpProfile):
    key = "articles"
    server_name = "test-articles"
    instructions = "Article CRUD."
    info_tool_name = "article_registry_info"
    api_prefixes = ("/api/article/",)


def setup_function():
    site.clear()


def teardown_function():
    site.clear()


def test_site_register_builds_profile():
    site.register(ArticlesMcp)
    profile = site.get_profile("articles", resolve_viewsets=False)
    assert profile.server_name == "test-articles"
    assert profile.api_prefixes == ("/api/article/",)


def test_registry_profile_round_trip():
    profile = RegistryProfile(
        key="demo",
        server_name="demo",
        instructions="demo",
        info_tool_name="demo_info",
        api_prefixes=("/api/demo/",),
        meta={"role": "demo"},
    )
    restored = RegistryProfile.from_dict(profile.to_dict())
    assert restored == profile


def test_default_profile_listed():
    keys = site.list_keys(resolve_viewsets=False)
    assert "default" in keys