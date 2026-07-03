from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .profiles import McpProfile


class McpSite:
    """Registry of :class:`~djcrud_mcp.McpProfile` classes (like :data:`djcrud_drf.site`)."""

    def __init__(self) -> None:
        self._profile_classes: list[type[McpProfile]] = []
        self._local_profiles: dict[str, McpProfile] = {}
        self._built: dict[str, McpProfile] | None = None

    def register(self, profile_class: type[McpProfile]) -> None:
        if profile_class not in self._profile_classes:
            self._profile_classes.append(profile_class)

    def register_profile(self, profile: McpProfile) -> None:
        """Attach a built profile (tests)."""
        if not profile._built:
            profile.build(resolve_viewsets=False)
        self._local_profiles[profile.key] = profile
        self._built = None

    def build(self, *, resolve_viewsets: bool = True) -> dict[str, McpProfile]:
        from .profiles import DEFAULT_PROFILE_KEY, DefaultMcpProfile

        if self._built is not None:
            return self._built

        profiles = dict(self._local_profiles)
        for profile_class in self._profile_classes:
            profile = profile_class().build(resolve_viewsets=resolve_viewsets)
            profiles[profile.key] = profile

        if not self._profile_classes and DEFAULT_PROFILE_KEY not in profiles:
            profiles[DEFAULT_PROFILE_KEY] = DefaultMcpProfile().build(
                resolve_viewsets=resolve_viewsets
            )

        self._built = profiles
        return profiles

    def list_keys(self, *, resolve_viewsets: bool = True) -> list[str]:
        return sorted(self.build(resolve_viewsets=resolve_viewsets))

    def default_key(self, *, resolve_viewsets: bool = True) -> str | None:
        from .profiles import DEFAULT_PROFILE_KEY

        profiles = self.build(resolve_viewsets=resolve_viewsets)
        if not profiles:
            return None

        flagged = [profile.key.strip().lower() for profile in profiles.values() if profile.default]
        if len(flagged) > 1:
            raise ValueError(
                "Multiple MCP profiles marked default: " + ", ".join(sorted(flagged))
            )
        if len(flagged) == 1:
            return flagged[0]

        if len(self._profile_classes) == 1:
            return self._profile_classes[0].key.strip().lower()

        if DEFAULT_PROFILE_KEY in profiles:
            return DEFAULT_PROFILE_KEY

        return None

    def get_profile(
        self, key: str | None = None, *, resolve_viewsets: bool = True
    ) -> McpProfile:
        if key is None or not str(key).strip():
            registry_key = self.default_key(resolve_viewsets=resolve_viewsets)
            if registry_key is None:
                raise ValueError("No MCP profile key given and host has no default profile")
        else:
            registry_key = str(key).strip().lower()
        profiles = self.build(resolve_viewsets=resolve_viewsets)
        try:
            return profiles[registry_key]
        except KeyError as exc:
            known = ", ".join(sorted(profiles))
            raise ValueError(
                f"Unknown MCP registry {registry_key!r}; expected one of: {known}"
            ) from exc

    def clear(self) -> None:
        self._profile_classes.clear()
        self._local_profiles.clear()
        self._built = None


site = McpSite()