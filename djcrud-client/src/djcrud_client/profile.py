from __future__ import annotations

from typing import Any


class McpProfile:
    """Wire-format MCP profile fetched from ``GET /api/mcp/profiles/{key}/``."""

    key: str
    server_name: str
    instructions: str
    info_tool_name: str
    api_prefixes: tuple[str, ...]
    meta: dict[str, Any]

    def __init__(self) -> None:
        self.key = ""
        self.server_name = ""
        self.instructions = ""
        self.info_tool_name = ""
        self.api_prefixes = ()
        self.meta = {}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> McpProfile:
        profile = cls()
        profile.key = str(payload["key"])
        profile.server_name = str(payload["server_name"])
        profile.instructions = str(payload["instructions"])
        profile.info_tool_name = str(payload["info_tool_name"])
        profile.api_prefixes = tuple(payload.get("api_prefixes", ()))
        profile.meta = dict(payload.get("meta", {}))
        return profile

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "server_name": self.server_name,
            "instructions": self.instructions,
            "info_tool_name": self.info_tool_name,
            "api_prefixes": list(self.api_prefixes),
            "meta": dict(self.meta),
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, McpProfile):
            return NotImplemented
        return self.to_dict() == other.to_dict()


def profile_meta(profile: McpProfile) -> dict[str, Any]:
    meta = dict(profile.meta)
    if profile.api_prefixes:
        meta.setdefault("api_prefixes", list(profile.api_prefixes))
    return meta