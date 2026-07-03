"""Tests for djcrud_client.config."""

from __future__ import annotations

from unittest.mock import patch

from djcrud_client.config import get_registry_key


def test_get_registry_key_ignores_registry_env_var(monkeypatch):
    monkeypatch.setenv("DJCRUD_MCP_REGISTRY", "ignored")
    monkeypatch.setenv("TILDETTE_MCP_REGISTRY", "also-ignored")
    with patch(
        "djcrud_client.api.fetch_profile_catalog",
        return_value=(["tasks", "mcp"], "tasks"),
    ):
        assert get_registry_key(base_url="http://example.test") == "tasks"