"""Django host integration for MCP profile registration."""

from .profiles import McpProfile, profile_meta, register_profile, resolve_profile_viewsets
from .site import site

__all__ = [
    "McpProfile",
    "profile_meta",
    "register_profile",
    "resolve_profile_viewsets",
    "site",
]