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


def get_registry_key() -> str:
    return _first_env("DJCRUD_MCP_REGISTRY", "TILDETTE_MCP_REGISTRY") or "default"


def get_profile_from_env():
    return get_profile(get_registry_key())