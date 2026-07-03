from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .viewsets import discover_viewsets, model_name_for


@dataclass(frozen=True)
class RegistryProfile:
    key: str
    server_name: str
    instructions: str
    info_tool_name: str
    viewsets: tuple = ()
    models: tuple = ()
    api_prefixes: tuple[str, ...] = ()
    extra_tools: tuple = ()
    meta: dict[str, Any] = field(default_factory=dict)


DEFAULT_PROFILE = RegistryProfile(
    key="default",
    server_name="djcrud",
    instructions="CRUD tools for registered djcrud API ViewSets.",
    info_tool_name="registry_info",
)

_PROFILES: dict[str, RegistryProfile] = {DEFAULT_PROFILE.key: DEFAULT_PROFILE}


def register_profile(profile: RegistryProfile) -> None:
    _PROFILES[profile.key] = profile


def get_profile(key: str | None = None) -> RegistryProfile:
    registry_key = (key or DEFAULT_PROFILE.key).strip().lower()
    try:
        return _PROFILES[registry_key]
    except KeyError as exc:
        known = ", ".join(sorted(_PROFILES))
        raise ValueError(
            f"Unknown MCP registry {registry_key!r}; expected one of: {known}"
        ) from exc


def resolve_viewsets(profile: RegistryProfile, *, all_viewsets=None) -> list:
    all_viewsets = list(all_viewsets or discover_viewsets())
    if profile.viewsets:
        allowed = set(profile.viewsets)
        return [viewset for viewset in all_viewsets if viewset in allowed]
    if profile.models:
        allowed = {model for model in profile.models}
        return [viewset for viewset in all_viewsets if viewset.model in allowed]
    return all_viewsets


def profile_meta(profile: RegistryProfile, *, viewsets) -> dict[str, Any]:
    meta = dict(profile.meta)
    meta.setdefault("name", profile.server_name)
    meta["viewsets"] = [model_name_for(viewset) for viewset in viewsets]
    return meta