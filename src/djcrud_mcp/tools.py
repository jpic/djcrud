from __future__ import annotations

from typing import Any

STANDARD_ACTIONS = (
    "partial_update",
    "destroy",
    "retrieve",
    "update",
    "create",
    "list",
)

METHOD_DEFAULT_ACTION = {
    "get": "list",
    "post": "create",
    "put": "update",
    "patch": "partial_update",
    "delete": "destroy",
}


def tool_name(model_name: str, action: str) -> str:
    return f"{model_name.lower()}_{action}"


_METHOD_SUFFIXES = (
    "_partial_update",
    "_destroy",
    "_retrieve",
    "_update",
    "_create",
    "_list",
)


def parse_operation_id(operation_id: str, *, model_name: str) -> str | None:
    prefix = f"{model_name}_"
    if not operation_id.startswith(prefix):
        return None
    suffix = operation_id[len(prefix) :]
    if suffix in STANDARD_ACTIONS:
        return suffix
    for method_suffix in _METHOD_SUFFIXES:
        if suffix.endswith(method_suffix):
            action = suffix[: -len(method_suffix)]
            if action:
                return action
    return suffix


def infer_action(
    *,
    path: str,
    method: str,
    api_prefix: str,
    model_name: str,
    operation: dict[str, Any],
) -> str | None:
    operation_id = operation.get("operationId") or ""
    parsed = parse_operation_id(operation_id, model_name=model_name)
    if parsed:
        return parsed

    normalized_path = path.rstrip("/") + "/"
    normalized_prefix = api_prefix.rstrip("/") + "/"
    if not normalized_path.startswith(normalized_prefix):
        return None

    relative = normalized_path[len(normalized_prefix) :]
    method = method.lower()

    if not relative:
        return METHOD_DEFAULT_ACTION.get(method)

    segments = [segment for segment in relative.split("/") if segment]
    if not segments:
        return METHOD_DEFAULT_ACTION.get(method)

    if segments[0].startswith("{"):
        if len(segments) == 1:
            return METHOD_DEFAULT_ACTION.get(method)
        return segments[1].rstrip("/")

    return segments[0].rstrip("/")


def render_path(path: str, arguments: dict[str, Any]) -> str:
    rendered = path
    for key, value in arguments.items():
        rendered = rendered.replace("{" + key + "}", str(value))
    return rendered


def _path_parameters(operation: dict[str, Any]) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    for parameter in operation.get("parameters", []):
        if parameter.get("in") == "path":
            schema = parameter.get("schema", {})
            properties[parameter["name"]] = {
                "type": schema.get("type", "string"),
            }
    return properties


def _body_properties(operation: dict[str, Any]) -> dict[str, Any]:
    for parameter in operation.get("parameters", []):
        if parameter.get("in") == "body":
            schema = parameter.get("schema", {})
            return schema.get("properties", {})

    request_body = operation.get("requestBody") or {}
    for media in (request_body.get("content") or {}).values():
        schema = media.get("schema") or {}
        return schema.get("properties", {})
    return {}


def _body_required(operation: dict[str, Any]) -> list[str]:
    for parameter in operation.get("parameters", []):
        if parameter.get("in") == "body":
            schema = parameter.get("schema", {})
            return list(schema.get("required", []))

    request_body = operation.get("requestBody") or {}
    for media in (request_body.get("content") or {}).values():
        schema = media.get("schema") or {}
        return list(schema.get("required", []))
    return []


def split_arguments(
    path: str,
    operation: dict[str, Any],
    arguments: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    path_args = {
        key: value for key, value in arguments.items() if "{" + key + "}" in path
    }
    body_keys = set(_body_properties(operation))
    body = {key: value for key, value in arguments.items() if key in body_keys}
    return path_args, body or None


def build_tool_definition(
    *,
    path: str,
    method: str,
    operation: dict[str, Any],
    model_name: str,
    action: str,
) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    properties.update(_path_parameters(operation))
    properties.update(_body_properties(operation))
    required = [name for name in properties if "{" + name + "}" in path]
    required.extend(
        name for name in _body_required(operation) if name not in required
    )
    return {
        "name": tool_name(model_name, action),
        "description": operation.get("summary") or f"{method.upper()} {path}",
        "method": method.lower(),
        "path": path,
        "operation": operation,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }