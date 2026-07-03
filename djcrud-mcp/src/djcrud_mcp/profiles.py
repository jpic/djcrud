from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DEFAULT_PROFILE_KEY = "default"


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
    server_name: str = "djcrud"
    instructions: str = "CRUD tools for registered djcrud API ViewSets."
    info_tool_name: str = "registry_info"
    viewsets: tuple = ()
    models: tuple = ()
    api_prefixes: tuple[str, ...] = ()
    meta: dict[str, Any] = {}

    @classmethod
    def build_registry_profile(
        cls, *, resolve_viewsets: bool = True
    ) -> RegistryProfile:
        api_prefixes = tuple(cls.api_prefixes)
        if not api_prefixes and resolve_viewsets and (cls.viewsets or cls.models):
            api_prefixes = _api_prefixes_for_viewsets(cls)
        elif (
            not api_prefixes
            and resolve_viewsets
            and cls.key == DEFAULT_PROFILE_KEY
            and not cls.viewsets
            and not cls.models
        ):
            api_prefixes = _api_prefixes_for_all_viewsets()

        return RegistryProfile(
            key=cls.key,
            server_name=cls.server_name,
            instructions=cls.instructions,
            info_tool_name=cls.info_tool_name,
            viewsets=tuple(cls.viewsets),
            models=tuple(cls.models),
            api_prefixes=api_prefixes,
            meta=dict(cls.meta),
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
    registry_key = (key or DEFAULT_PROFILE_KEY).strip().lower()
    if base_url:
        from .api import fetch_profile

        try:
            return fetch_profile(base_url=base_url, key=registry_key)
        except Exception:
            pass

    from .site import site

    return site.get_profile(registry_key, resolve_viewsets=resolve_viewsets)


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