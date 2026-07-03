"""Optional stdio MCP bridge for djcrud DRF ViewSets."""

from .api import CrudApi, login
from .config import get_base_url, get_registry_key, get_token
from .extras import ExtraTool
from .profiles import RegistryProfile, get_profile, register_profile
from .schema import build_tools_from_schema
from .server import create_mcp_server, fetch_schema, run_stdio
from .viewsets import api_path_for, discover_viewsets

__all__ = [
    "CrudApi",
    "ExtraTool",
    "RegistryProfile",
    "api_path_for",
    "build_tools_from_schema",
    "create_mcp_server",
    "discover_viewsets",
    "fetch_schema",
    "get_base_url",
    "get_profile",
    "get_registry_key",
    "get_token",
    "login",
    "register_profile",
    "run_stdio",
]