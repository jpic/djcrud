from __future__ import annotations

from typing import Any

from .tools import build_tool_definition, infer_action, tool_name
from .viewsets import api_path_for, model_name_for


def filter_paths_by_viewsets(
    schema: dict[str, Any],
    *,
    viewsets,
) -> dict[str, Any]:
    prefixes = [api_path_for(viewset).rstrip("/") for viewset in viewsets]
    paths: dict[str, Any] = {}
    for path, operations in schema.get("paths", {}).items():
        normalized = path.rstrip("/")
        if any(
            normalized == prefix or normalized.startswith(prefix + "/")
            for prefix in prefixes
        ):
            paths[path] = operations
    return paths


def build_tools_from_schema(
    schema: dict[str, Any],
    *,
    viewsets,
) -> list[dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    prefixes = {model_name_for(viewset): api_path_for(viewset) for viewset in viewsets}

    for path, operations in filter_paths_by_viewsets(schema, viewsets=viewsets).items():
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


def prefix_map_from_profile(profile) -> dict[str, str]:
    """Build ``{model_name: api_prefix}`` without importing Django ViewSets."""
    from .profiles import RegistryProfile
    from .viewsets import api_path_for, model_name_for

    if isinstance(profile, RegistryProfile) and profile.api_prefixes:
        result = {}
        for prefix in profile.api_prefixes:
            model_name = prefix.rstrip("/").split("/")[-1]
            normalized = prefix if prefix.endswith("/") else prefix + "/"
            result[model_name] = normalized
        return result

    prefixes: dict[str, str] = {}
    viewsets = []
    if isinstance(profile, RegistryProfile):
        from .profiles import resolve_viewsets

        viewsets = resolve_viewsets(profile)
    elif profile:
        viewsets = list(profile)

    for viewset in viewsets:
        prefixes[model_name_for(viewset)] = api_path_for(viewset)
    return prefixes


def build_tools_for_profile(
    schema: dict[str, Any],
    profile,
    *,
    viewsets=None,
) -> list[dict[str, Any]]:
    prefix_map = prefix_map_from_profile(profile)
    if not prefix_map and viewsets:
        prefix_map = {model_name_for(vs): api_path_for(vs) for vs in viewsets}
    return _build_tools_from_prefix_map(schema, prefix_map)


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