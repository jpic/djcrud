"""Tests for host-published default MCP registry resolution."""

from __future__ import annotations

from unittest.mock import patch

from djcrud_client.api import resolve_registry_key


def test_resolve_registry_key_prefers_explicit():
    key = resolve_registry_key(
        base_url="http://example.test",
        explicit="custom",
    )
    assert key == "custom"


def test_resolve_registry_key_uses_host_default():
    with patch(
        "djcrud_client.api.fetch_profile_catalog",
        return_value=(["tasks", "mcp"], "tasks"),
    ):
        key = resolve_registry_key(base_url="http://example.test")
    assert key == "tasks"


def test_resolve_registry_key_uses_single_profile():
    with patch(
        "djcrud_client.api.fetch_profile_catalog",
        return_value=(["articles"], None),
    ):
        key = resolve_registry_key(base_url="http://example.test")
    assert key == "articles"


def test_resolve_registry_key_falls_back_to_default():
    with patch(
        "djcrud_client.api.fetch_profile_catalog",
        side_effect=OSError("offline"),
    ):
        key = resolve_registry_key(base_url="http://example.test")
    assert key == "default"