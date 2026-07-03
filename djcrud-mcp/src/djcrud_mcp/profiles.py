from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DEFAULT_PROFILE_KEY = "default"


def _is_auto(value: str) -> bool:
    return not str(value).strip()


def _host_slug() -> str | None:
    try:
        from django.conf import settings

        if not settings.configured:
            return None
        root = settings.ROOT_URLCONF.rsplit(".", 1)[0]
        if root.endswith("_settings"):
            root = root[: -len("_settings")]
        return root.replace("_", "-")
    except Exception:
        return None


def _resource_names_from_api_prefixes(prefixes: tuple[str, ...]) -> list[str]:
    names: list[str] = []
    for prefix in prefixes:
        parts = prefix.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "api" and parts[1]:
            names.append(parts[1])
    return names


def _model_labels(*, viewsets: list, models: tuple) -> list[str]:
    labels: list[str] = []
    for viewset in viewsets:
        model = viewset.model
        labels.append(str(model._meta.verbose_name or model.__name__))
    for model in models:
        labels.append(str(model._meta.verbose_name or model.__name__))
    return labels


def _format_resource_list(labels: list[str]) -> str:
    if not labels:
        return "registered API resources"
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return ", ".join(labels[:-1]) + f", and {labels[-1]}"


def _primary_model_slug(
    profile_class: type[McpProfile], *, viewsets: list
) -> str | None:
    if profile_class.viewsets:
        from .viewsets import model_name_for

        return model_name_for(profile_class.viewsets[0])
    if viewsets:
        from .viewsets import model_name_for

        return model_name_for(viewsets[0])
    if profile_class.models:
        return str(profile_class.models[0]._meta.model_name)
    resource_names = _resource_names_from_api_prefixes(profile_class.api_prefixes)
    return resource_names[0] if resource_names else None


def _default_server_name(profile_class: type[McpProfile]) -> str:
    key_slug = profile_class.key.replace("_", "-")
    if profile_class.key == DEFAULT_PROFILE_KEY:
        return _host_slug() or "djcrud"
    host = _host_slug()
    if host:
        return f"{host}-{key_slug}"
    return key_slug


def _default_info_tool_name(
    profile_class: type[McpProfile], *, primary_model: str | None
) -> str:
    if profile_class.key == DEFAULT_PROFILE_KEY and not primary_model:
        return "registry_info"
    slug = primary_model or profile_class.key
    return f"{slug}_registry_info"


def _default_instructions(
    profile_class: type[McpProfile], *, model_labels: list[str]
) -> str:
    if profile_class.key == DEFAULT_PROFILE_KEY and not model_labels:
        return "CRUD tools for registered djcrud API ViewSets."
    return f"CRUD for {_format_resource_list(model_labels)} via the JSON API."


@dataclass(frozen=True)
class RegistryProfile:
    key: str
    server_name: str
    instructions: str
    info_tool_name: str
    viewsets: tuple = ()
    models: tuple = ()
    api_prefixes: tuple[str, ...] = ()
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "server_name": self.server_name,
            "instructions": self.instructions,
            "info_tool_name": self.info_tool_name,
            "api_prefixes": list(self.api_prefixes),
            "meta": dict(self.meta),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RegistryProfile:
        return cls(
            key=str(payload["key"]),
            server_name=str(payload["server_name"]),
            instructions=str(payload["instructions"]),
            info_tool_name=str(payload["info_tool_name"]),
            api_prefixes=tuple(payload.get("api_prefixes", ())),
            meta=dict(payload.get("meta", {})),
        )


class McpProfile:
    """Declare an MCP stdio server surface (register on :data:`djcrud_mcp.site`)."""

    key: str = DEFAULT_PROFILE_KEY
    default: bool = False
    server_name: str = ""
    instructions: str = ""
    info_tool_name: str = ""
    viewsets: tuple = ()
    models: tuple = ()
    api_prefixes: tuple[str, ...] = ()
    meta: dict[str, Any] = {}

    @classmethod
    def build_registry_profile(
        cls, *, resolve_viewsets: bool = True
    ) -> RegistryProfile:
        introspect = resolve_viewsets
        api_prefixes = tuple(cls.api_prefixes)
        if not api_prefixes and introspect and (cls.viewsets or cls.models):
            api_prefixes = _api_prefixes_for_viewsets(cls)
        elif (
            not api_prefixes
            and introspect
            and cls.key == DEFAULT_PROFILE_KEY
            and not cls.viewsets
            and not cls.models
        ):
            api_prefixes = _api_prefixes_for_all_viewsets()

        resolved_viewsets: list = []
        if introspect and (cls.viewsets or cls.models):
            try:
                resolved_viewsets = resolve_viewsets(
                    RegistryProfile(
                        key=cls.key,
                        server_name="",
                        instructions="",
                        info_tool_name="",
                        viewsets=tuple(cls.viewsets),
                        models=tuple(cls.models),
                    )
                )
            except Exception:
                resolved_viewsets = list(cls.viewsets)
        elif cls.viewsets:
            resolved_viewsets = list(cls.viewsets)

        model_labels = _model_labels(viewsets=resolved_viewsets, models=tuple(cls.models))
        if not model_labels and api_prefixes:
            model_labels = _resource_names_from_api_prefixes(api_prefixes)

        primary_model = _primary_model_slug(cls, viewsets=resolved_viewsets)
        server_name = (
            cls.server_name.strip()
            if not _is_auto(cls.server_name)
            else _default_server_name(cls)
        )
        instructions = (
            cls.instructions.strip()
            if not _is_auto(cls.instructions)
            else _default_instructions(cls, model_labels=model_labels)
        )
        info_tool_name = (
            cls.info_tool_name.strip()
            if not _is_auto(cls.info_tool_name)
            else _default_info_tool_name(cls, primary_model=primary_model)
        )

        meta = dict(cls.meta)
        meta.setdefault("name", server_name)

        return RegistryProfile(
            key=cls.key,
            server_name=server_name,
            instructions=instructions,
            info_tool_name=info_tool_name,
            viewsets=tuple(cls.viewsets),
            models=tuple(cls.models),
            api_prefixes=api_prefixes,
            meta=meta,
        )


class DefaultMcpProfile(McpProfile):
    key = DEFAULT_PROFILE_KEY
    server_name = "djcrud"
    instructions = "CRUD tools for registered djcrud API ViewSets."
    info_tool_name = "registry_info"


def _api_prefixes_for_viewsets(profile_class: type[McpProfile]) -> tuple[str, ...]:
    from .viewsets import api_path_for, discover_viewsets

    probe = RegistryProfile(
        key=profile_class.key,
        server_name=profile_class.server_name,
        instructions=profile_class.instructions,
        info_tool_name=profile_class.info_tool_name,
        viewsets=tuple(profile_class.viewsets),
        models=tuple(profile_class.models),
    )
    viewsets = resolve_viewsets(probe, all_viewsets=discover_viewsets())
    return tuple(api_path_for(viewset) for viewset in viewsets)


def _api_prefixes_for_all_viewsets() -> tuple[str, ...]:
    from .viewsets import api_path_for, discover_viewsets

    return tuple(api_path_for(viewset) for viewset in discover_viewsets())


def register_profile(profile: RegistryProfile) -> None:
    from .site import site

    site.register_profile(profile)


def get_profile(
    key: str | None = None,
    *,
    base_url: str | None = None,
    resolve_viewsets: bool = True,
) -> RegistryProfile:
    if base_url:
        from .api import fetch_profile, resolve_registry_key

        try:
            registry_key = resolve_registry_key(base_url=base_url, explicit=key)
            return fetch_profile(base_url=base_url, key=registry_key)
        except Exception:
            pass

    from .site import site

    return site.get_profile(key, resolve_viewsets=resolve_viewsets)


def resolve_viewsets(profile: RegistryProfile, *, all_viewsets=None) -> list:
    from .viewsets import discover_viewsets

    all_viewsets = list(all_viewsets if all_viewsets is not None else discover_viewsets())
    if profile.viewsets:
        allowed = set(profile.viewsets)
        return [viewset for viewset in all_viewsets if viewset in allowed]
    if profile.models:
        allowed = {model for model in profile.models}
        return [viewset for viewset in all_viewsets if viewset.model in allowed]
    return all_viewsets


def profile_meta(profile: RegistryProfile, *, viewsets: list | None = None) -> dict[str, Any]:
    meta = dict(profile.meta)
    meta.setdefault("name", profile.server_name)
    if viewsets:
        from .viewsets import model_name_for

        meta["viewsets"] = [model_name_for(viewset) for viewset in viewsets]
    elif profile.api_prefixes:
        meta["api_prefixes"] = list(profile.api_prefixes)
    return meta