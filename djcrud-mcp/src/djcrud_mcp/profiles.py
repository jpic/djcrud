from __future__ import annotations

from typing import Any, Self

DEFAULT_PROFILE_KEY = "default"


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


class McpProfile:
    """Declare an MCP stdio server surface; register the class on :data:`djcrud_mcp.site`."""

    key: str = DEFAULT_PROFILE_KEY
    default: bool = False
    viewsets: tuple = ()
    models: tuple = ()
    api_prefixes: tuple[str, ...] | None = None
    server_name: str | None = None
    instructions: str | None = None
    info_tool_name: str | None = None
    meta: dict[str, Any] | None = None

    def __init__(self) -> None:
        self._built = False
        self._remote = False
        self._resolved_viewsets: list = []
        self._cached_api_prefixes: tuple[str, ...] = ()

    def build(self, *, resolve_viewsets: bool = True) -> Self:
        if self._built:
            return self

        declared_prefixes = type(self).__dict__.get("api_prefixes")
        if declared_prefixes is not None:
            self._cached_api_prefixes = tuple(declared_prefixes)
            self._resolved_viewsets = list(self.viewsets)
        elif resolve_viewsets and (self.viewsets or self.models):
            try:
                self._resolved_viewsets = resolve_viewsets(self)
                from .viewsets import api_path_for

                self._cached_api_prefixes = tuple(
                    api_path_for(viewset) for viewset in self._resolved_viewsets
                )
            except Exception:
                self._resolved_viewsets = list(self.viewsets)
                self._cached_api_prefixes = ()
        elif (
            resolve_viewsets
            and self.key == DEFAULT_PROFILE_KEY
            and not self.viewsets
            and not self.models
        ):
            try:
                from .viewsets import api_path_for, discover_viewsets

                self._resolved_viewsets = discover_viewsets()
                self._cached_api_prefixes = tuple(
                    api_path_for(viewset) for viewset in self._resolved_viewsets
                )
            except Exception:
                self._resolved_viewsets = []
                self._cached_api_prefixes = ()
        else:
            self._resolved_viewsets = list(self.viewsets)
            self._cached_api_prefixes = ()

        self._built = True
        return self

    def _class_override(self, name: str) -> Any:
        if name in self.__dict__:
            return self.__dict__[name]
        return type(self).__dict__.get(name)

    @property
    def resolved_viewsets(self) -> list:
        return list(self._resolved_viewsets)

    @property
    def api_prefixes(self) -> tuple[str, ...]:
        return self._cached_api_prefixes

    @property
    def server_name(self) -> str:
        if self._remote:
            return self._server_name_value
        override = self._class_override("server_name")
        if override is not None and str(override).strip():
            return str(override).strip()
        key_slug = self.key.replace("_", "-")
        if self.key == DEFAULT_PROFILE_KEY:
            return _host_slug() or "djcrud"
        host = _host_slug()
        if host:
            return f"{host}-{key_slug}"
        return key_slug

    @property
    def instructions(self) -> str:
        if self._remote:
            return self._instructions_value
        override = self._class_override("instructions")
        if override is not None and str(override).strip():
            return str(override).strip()
        labels = _model_labels(
            viewsets=self._resolved_viewsets,
            models=tuple(self.models),
        )
        if not labels and self._cached_api_prefixes:
            labels = _resource_names_from_api_prefixes(self._cached_api_prefixes)
        if self.key == DEFAULT_PROFILE_KEY and not labels:
            return "CRUD tools for registered djcrud API ViewSets."
        return f"CRUD for {_format_resource_list(labels)} via the JSON API."

    @property
    def info_tool_name(self) -> str:
        if self._remote:
            return self._info_tool_name_value
        override = self._class_override("info_tool_name")
        if override is not None and str(override).strip():
            return str(override).strip()
        primary = _primary_model_slug(self)
        if self.key == DEFAULT_PROFILE_KEY and not primary:
            return "registry_info"
        slug = primary or self.key
        return f"{slug}_registry_info"

    @property
    def meta(self) -> dict[str, Any]:
        if self._remote:
            return dict(self._meta_value)
        declared = self._class_override("meta")
        result = dict(declared) if isinstance(declared, dict) else {}
        result.setdefault("name", self.server_name)
        return result

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
    def from_dict(cls, payload: dict[str, Any]) -> McpProfile:
        profile = object.__new__(cls)
        profile._built = True
        profile._remote = True
        profile.key = str(payload["key"])
        profile.default = False
        profile.viewsets = ()
        profile.models = ()
        profile._resolved_viewsets = []
        profile._server_name_value = str(payload["server_name"])
        profile._instructions_value = str(payload["instructions"])
        profile._info_tool_name_value = str(payload["info_tool_name"])
        profile._cached_api_prefixes = tuple(payload.get("api_prefixes", ()))
        profile._meta_value = dict(payload.get("meta", {}))
        return profile

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, McpProfile):
            return NotImplemented
        return self.to_dict() == other.to_dict()


def _primary_model_slug(profile: McpProfile) -> str | None:
    if profile.viewsets:
        from .viewsets import model_name_for

        return model_name_for(profile.viewsets[0])
    if profile._resolved_viewsets:
        from .viewsets import model_name_for

        return model_name_for(profile._resolved_viewsets[0])
    if profile.models:
        return str(profile.models[0]._meta.model_name)
    resource_names = _resource_names_from_api_prefixes(profile._cached_api_prefixes)
    return resource_names[0] if resource_names else None


class DefaultMcpProfile(McpProfile):
    key = DEFAULT_PROFILE_KEY
    server_name = "djcrud"
    instructions = "CRUD tools for registered djcrud API ViewSets."
    info_tool_name = "registry_info"


def register_profile(profile: McpProfile) -> None:
    from .site import site

    site.register_profile(profile)


def get_profile(
    key: str | None = None,
    *,
    base_url: str | None = None,
    resolve_viewsets: bool = True,
) -> McpProfile:
    if base_url:
        from .api import fetch_profile, resolve_registry_key

        try:
            registry_key = resolve_registry_key(base_url=base_url, explicit=key)
            return fetch_profile(base_url=base_url, key=registry_key)
        except Exception:
            pass

    from .site import site

    return site.get_profile(key, resolve_viewsets=resolve_viewsets)


def resolve_viewsets(profile: McpProfile, *, all_viewsets=None) -> list:
    if profile._built and profile._resolved_viewsets:
        return list(profile._resolved_viewsets)

    from .viewsets import discover_viewsets

    all_viewsets = list(all_viewsets if all_viewsets is not None else discover_viewsets())
    if profile.viewsets:
        allowed = set(profile.viewsets)
        return [viewset for viewset in all_viewsets if viewset in allowed]
    if profile.models:
        allowed = {model for model in profile.models}
        return [viewset for viewset in all_viewsets if viewset.model in allowed]
    return all_viewsets


def profile_meta(profile: McpProfile, *, viewsets: list | None = None) -> dict[str, Any]:
    meta = dict(profile.meta)
    if viewsets:
        from .viewsets import model_name_for

        meta["viewsets"] = [model_name_for(viewset) for viewset in viewsets]
    elif profile._cached_api_prefixes:
        meta["api_prefixes"] = list(profile._cached_api_prefixes)
    return meta