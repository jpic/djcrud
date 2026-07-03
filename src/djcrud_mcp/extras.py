from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExtraTool:
    """Non-CRUD MCP tool backed by a fixed HTTP route."""

    name: str
    method: str
    path: str
    description: str
    input_schema: dict[str, Any] = field(
        default_factory=lambda: {"type": "object", "properties": {}, "required": []}
    )

    def as_tool_definition(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "method": self.method.lower(),
            "path": self.path,
            "operation": {},
            "input_schema": self.input_schema,
        }