from __future__ import annotations

from typing import Any

from .profile import McpProfile
from .tools import build_tool_definition, infer_action


def prefix_map_from_profile(profile: McpProfile) -> dict[str, str]:
    """Build ``{model_name: api_prefix}`` from host-published ``api_prefixes``."""
    result: dict[str, str] = {}
    for prefix in profile.api_prefixes:
        model_name = prefix.rstrip("/").split("/")[-1]
        normalized = prefix if prefix.endswith("/") else prefix + "/"
        result[model_name] = normalized
    return result


def build_tools_for_profile(
    schema: dict[str, Any],
    profile: McpProfile,
) -> list[dict[str, Any]]:
    return _build_tools_from_prefix_map(schema, prefix_map_from_profile(profile))


def all_tools_for_profile(
    schema: dict[str, Any],
    profile: McpProfile,
) -> list[dict[str, Any]]:
    return build_tools_for_profile(schema, profile)


def build_tools_from_schema(
    schema: dict[str, Any],
    *,
    prefixes: dict[str, str],
) -> list[dict[str, Any]]:
    return _build_tools_from_prefix_map(schema, prefixes)


def _build_tools_from_prefix_map(
    schema: dict[str, Any],
    prefixes: dict[str, str],
) -> list[dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    paths: dict[str, Any] = {}
    for path, operations in schema.get("paths", {}).items():
        normalized = path.rstrip("/")
        if any(
            normalized == pfx.rstrip("/") or normalized.startswith(pfx.rstrip("/") + "/")
            for pfx in prefixes.values()
        ):
            paths[path] = operations

    for path, operations in paths.items():
        for method, operation in operations.items():
            if method.startswith("x-"):
                continue
            model_name = _model_for_path(path, prefixes)
            if model_name is None:
                continue
            action = infer_action(
                path=path,
                method=method,
                api_prefix=prefixes[model_name],
                model_name=model_name,
                operation=operation,
            )
            if not action:
                continue
            tool = build_tool_definition(
                path=path,
                method=method,
                operation=operation,
                model_name=model_name,
                action=action,
            )
            existing = by_name.get(tool["name"])
            if existing is None or method == "patch":
                by_name[tool["name"]] = tool
    return list(by_name.values())


def _model_for_path(path: str, prefixes: dict[str, str]) -> str | None:
    normalized = path.rstrip("/") + "/"
    matches = [
        model_name
        for model_name, prefix in prefixes.items()
        if normalized.startswith(prefix.rstrip("/") + "/") or normalized == prefix
    ]
    if not matches:
        return None
    return min(matches, key=len)