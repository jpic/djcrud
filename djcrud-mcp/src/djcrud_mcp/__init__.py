"""Stdio MCP bridge for djcrud DRF APIs."""

from .api import CrudApi, login
from .config import get_base_url, get_registry_key, get_token
from .extras import ExtraTool
from .profiles import RegistryProfile, get_profile, profile_meta, register_profile
from .schema import all_tools_for_profile, build_tools_for_profile, build_tools_from_schema
from .server import create_mcp_server, fetch_schema, run_stdio

__all__ = [
    "CrudApi",
    "ExtraTool",
    "RegistryProfile",
    "all_tools_for_profile",
    "build_tools_for_profile",
    "build_tools_from_schema",
    "create_mcp_server",
    "fetch_schema",
    "get_base_url",
    "get_profile",
    "get_registry_key",
    "get_token",
    "login",
    "profile_meta",
    "register_profile",
    "run_stdio",
]


def discover_viewsets():
    """Optional: requires ``djcrud[drf]`` (Django host)."""
    from .viewsets import discover_viewsets as _discover_viewsets

    return _discover_viewsets()


def api_path_for(viewset_class):
    from .viewsets import api_path_for as _api_path_for

    return _api_path_for(viewset_class)