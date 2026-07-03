from __future__ import annotations

import os

from .profiles import get_profile


def _first_env(*keys: str) -> str:
    for key in keys:
        value = os.environ.get(key, "").strip()
        if value:
            return value
    return ""


def get_base_url() -> str:
    value = _first_env("DJCRUD_BASE_URL", "DJMVC_BASE_URL", "TILDETTE_BASE_URL")
    return (value or "http://127.0.0.1:8000").rstrip("/")


def get_token() -> str:
    return _first_env("DJCRUD_TOKEN", "DJMVC_TOKEN", "TILDETTE_TOKEN")


def get_registry_key(*, base_url: str | None = None) -> str:
    explicit = _first_env("DJCRUD_MCP_REGISTRY", "TILDETTE_MCP_REGISTRY")
    if explicit:
        return explicit.strip().lower()

    if base_url:
        from .api import resolve_registry_key

        return resolve_registry_key(base_url=base_url)

    return "default"


def get_profile_from_env():
    from .server import _load_profile

    base_url = get_base_url()
    return _load_profile(get_registry_key(base_url=base_url), base_url=base_url)