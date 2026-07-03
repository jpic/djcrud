"""Tests for McpProfile classes and site.register()."""

from __future__ import annotations

from djcrud_mcp import McpProfile, site


class ArticlesMcp(McpProfile):
    key = "articles"
    api_prefixes = ("/api/article/",)


def setup_function():
    site.clear()


def teardown_function():
    site.clear()


def test_site_register_builds_profile():
    site.register(ArticlesMcp)
    profile = site.get_profile("articles", resolve_viewsets=False)
    assert profile.server_name == "articles"
    assert profile.info_tool_name == "article_registry_info"
    assert profile.instructions == "CRUD for article via the JSON API."
    assert profile.api_prefixes == ("/api/article/",)


def test_auto_generated_fields_from_api_prefixes():
    site.register(ArticlesMcp)
    profile = site.get_profile("articles", resolve_viewsets=False)
    assert profile.meta["name"] == profile.server_name


def test_profile_to_dict_round_trip():
    profile = ArticlesMcp().build(resolve_viewsets=False)
    restored = McpProfile.from_dict(profile.to_dict())
    assert restored == profile


def test_default_profile_listed():
    keys = site.list_keys(resolve_viewsets=False)
    assert "default" in keys


def test_default_key_when_single_profile_registered():
    site.register(ArticlesMcp)
    assert site.default_key(resolve_viewsets=False) == "articles"
    assert site.list_keys(resolve_viewsets=False) == ["articles"]


def test_default_key_honors_explicit_default_flag():
    class AdminMcp(McpProfile):
        key = "admin"
        server_name = "admin"
        instructions = "admin"
        info_tool_name = "admin_info"
        api_prefixes = ("/api/admin/",)

    class ArticlesDefaultMcp(ArticlesMcp):
        key = "articles"
        default = True

    site.register(AdminMcp)
    site.register(ArticlesDefaultMcp)
    assert site.default_key(resolve_viewsets=False) == "articles"