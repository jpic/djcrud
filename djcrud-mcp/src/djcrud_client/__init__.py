"""Stdio MCP bridge for djcrud JSON APIs (no Django required)."""

from .api import CrudApi, login
from .config import get_base_url, get_registry_key, get_token
from .profile import McpProfile, profile_meta
from .schema import all_tools_for_profile, build_tools_for_profile, build_tools_from_schema
from .server import create_mcp_server, fetch_schema, run_stdio

__all__ = [
    "CrudApi",
    "McpProfile",
    "all_tools_for_profile",
    "build_tools_for_profile",
    "build_tools_from_schema",
    "create_mcp_server",
    "fetch_schema",
    "get_base_url",
    "get_registry_key",
    "get_token",
    "login",
    "profile_meta",
    "run_stdio",
]