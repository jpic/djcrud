from __future__ import annotations

import argparse
import json
import os
import sys

from djcrud_client.api import CrudApi, login
from djcrud_client.config import get_base_url, get_registry_key, get_token
from djcrud_client.schema import all_tools_for_profile
from djcrud_client.server import create_mcp_server, fetch_schema, load_profile
from djcrud_client.tools import render_path, split_arguments


def resolve_token(
    *,
    base_url: str,
    username: str | None,
    password: str | None,
) -> str:
    token = get_token()
    if token:
        return token
    user = username or os.environ.get("DJCRUD_USERNAME", "").strip()
    pwd = password or os.environ.get("DJCRUD_PASSWORD", "").strip()
    if not user or not pwd:
        raise SystemExit(
            "Authentication required: set DJCRUD_TOKEN "
            "or provide --user/--password (or DJCRUD_USERNAME/DJCRUD_PASSWORD)."
        )
    return login(base_url=base_url, username=user, password=pwd)


def call_tool(
    *,
    tool_name: str,
    arguments: dict,
    base_url: str,
    token: str,
    registry: str,
) -> None:
    profile = load_profile(registry, base_url=base_url)
    schema = fetch_schema(base_url=base_url)
    tools = all_tools_for_profile(schema, profile)
    tool = next((entry for entry in tools if entry["name"] == tool_name), None)
    if tool is None:
        raise SystemExit(f"Unknown tool: {tool_name}")

    api = CrudApi(base_url=base_url, token=token)
    path_args, body = split_arguments(
        tool["path"], tool.get("operation", {}), arguments
    )
    rendered = render_path(tool["path"], path_args)
    if "?" not in rendered and not rendered.endswith("/"):
        rendered = f"{rendered}/"
    response = api.request(tool["method"], rendered, json_body=body)
    print(response.text)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="djcrud-client")
    parser.add_argument("-mcp", action="store_true", help="Run stdio MCP server")
    parser.add_argument(
        "--registry",
        default=None,
        metavar="KEY",
        help="Profile key (default: host default from GET /api/mcp/profiles/)",
    )
    parser.add_argument("--call", metavar="TOOL", help="Call one tool and exit")
    parser.add_argument("--json", default="{}", help="Tool arguments as JSON object")
    parser.add_argument("--user", help="Username for /api/login/")
    parser.add_argument("--password", help="Password for /api/login/")
    args = parser.parse_args(argv)

    base_url = get_base_url()
    registry = args.registry or get_registry_key(base_url=base_url)

    if args.call:
        token = resolve_token(
            base_url=base_url,
            username=args.user,
            password=args.password,
        )
        arguments = json.loads(args.json)
        call_tool(
            tool_name=args.call,
            arguments=arguments,
            base_url=base_url,
            token=token,
            registry=registry,
        )
        return

    token = resolve_token(
        base_url=base_url,
        username=args.user,
        password=args.password,
    )
    create_mcp_server(
        base_url=base_url,
        token=token,
        registry=registry,
    ).run(transport="stdio")


if __name__ == "__main__":
    main(sys.argv[1:])