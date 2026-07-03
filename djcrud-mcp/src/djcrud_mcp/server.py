from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from .api import CrudApi
from .config import get_base_url, get_profile_from_env, get_registry_key, get_token
from .profiles import RegistryProfile, get_profile, profile_meta
from .schema import all_tools_for_profile, build_tools_for_profile
from .tools import render_path, split_arguments


def fetch_schema(*, base_url: str) -> dict[str, Any]:
    return CrudApi(base_url=base_url, token="").fetch_schema()


def _load_profile(key: str, *, base_url: str):
    from .api import fetch_profile

    try:
        return fetch_profile(base_url=base_url, key=key)
    except Exception:
        return get_profile(key)


def _resolve_viewsets(profile: RegistryProfile) -> list:
    if profile.api_prefixes:
        return []
    return []


def create_mcp_server(
    *,
    base_url: str | None = None,
    token: str | None = None,
    profile: RegistryProfile | str | None = None,
    registry: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> FastMCP:
    base_url = (base_url or get_base_url()).rstrip("/")
    registry_key = (
        profile
        if isinstance(profile, str)
        else (registry or get_registry_key(base_url=base_url))
    )
    if isinstance(profile, str) or profile is None:
        profile = _load_profile(registry_key, base_url=base_url)
    token = token if token is not None else get_token()
    viewsets = _resolve_viewsets(profile)
    schema = fetch_schema(base_url=base_url)
    api = CrudApi(base_url=base_url, token=token, extra_headers=extra_headers)
    mcp = FastMCP(profile.server_name, instructions=profile.instructions)

    def registry_info() -> str:
        return json.dumps(profile_meta(profile, viewsets=viewsets or None), indent=2)

    registry_info.__name__ = profile.info_tool_name
    mcp.add_tool(
        registry_info,
        name=profile.info_tool_name,
        description=profile.instructions,
    )

    for tool in build_tools_for_profile(schema, profile, viewsets=viewsets or None):
        _register_tool(mcp, api, tool)

    return mcp


def _register_tool(mcp: FastMCP, api: CrudApi, tool: dict[str, Any]) -> None:
    path = tool["path"]
    method = tool["method"]
    operation = tool.get("operation", {})

    def handler(**arguments: Any) -> str:
        if set(arguments.keys()) == {"arguments"} and isinstance(
            arguments["arguments"], dict
        ):
            arguments = arguments["arguments"]
        path_args, body = split_arguments(path, operation, arguments)
        rendered = render_path(path, path_args)
        if "?" not in rendered and not rendered.endswith("/"):
            rendered = f"{rendered}/"
        response = api.request(method, rendered, json_body=body)
        try:
            payload: Any = response.json()
        except Exception:
            payload = {"status_code": response.status_code, "text": response.text}
        return json.dumps(payload, indent=2)

    handler.__name__ = tool["name"]
    handler.__doc__ = tool["description"]
    mcp.add_tool(
        handler,
        name=tool["name"],
        description=tool["description"],
    )


def run_stdio(*, registry: str | None = None) -> None:
    create_mcp_server(registry=registry).run(transport="stdio")