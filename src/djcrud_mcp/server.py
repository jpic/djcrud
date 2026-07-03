from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from .api import CrudApi
from .config import get_base_url, get_profile_from_env, get_registry_key, get_token
from .extras import ExtraTool
from .profiles import RegistryProfile, get_profile, profile_meta, resolve_viewsets
from .schema import build_tools_for_profile, build_tools_from_schema
from .tools import render_path, split_arguments
from .viewsets import discover_viewsets


def fetch_schema(*, base_url: str) -> dict[str, Any]:
    return CrudApi(base_url=base_url, token="").fetch_schema()


def create_mcp_server(
    *,
    base_url: str | None = None,
    token: str | None = None,
    profile: RegistryProfile | str | None = None,
    registry: str | None = None,
) -> FastMCP:
    if isinstance(profile, str):
        profile = get_profile(profile)
    elif profile is None:
        profile = get_profile(registry or get_registry_key())
    base_url = (base_url or get_base_url()).rstrip("/")
    token = token if token is not None else get_token()
    viewsets = []
    try:
        all_viewsets = discover_viewsets()
        viewsets = resolve_viewsets(profile, all_viewsets=all_viewsets)
    except Exception:
        viewsets = []
    schema = fetch_schema(base_url=base_url)
    api = CrudApi(base_url=base_url, token=token)
    mcp = FastMCP(profile.server_name, instructions=profile.instructions)

    def registry_info() -> str:
        return json.dumps(profile_meta(profile, viewsets=viewsets), indent=2)

    registry_info.__name__ = profile.info_tool_name
    mcp.add_tool(
        registry_info,
        name=profile.info_tool_name,
        description=profile.instructions,
    )

    for tool in build_tools_for_profile(schema, profile, viewsets=viewsets or None):
        _register_tool(mcp, api, tool)

    for extra in profile.extra_tools:
        if isinstance(extra, ExtraTool):
            _register_tool(mcp, api, extra.as_tool_definition())

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