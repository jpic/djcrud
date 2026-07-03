from __future__ import annotations

import os

from .api import resolve_registry_key


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
    """Host default profile key from ``GET /api/mcp/profiles/`` (not an env var)."""
    return resolve_registry_key(base_url=(base_url or get_base_url()).rstrip("/"))


def get_profile_from_env():
    from .server import load_profile

    base_url = get_base_url()
    return load_profile(get_registry_key(base_url=base_url), base_url=base_url)