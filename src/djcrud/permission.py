import inspect


def call_with_context(method, ctx):
    """Call *method* with keys from *ctx* that its signature accepts."""
    params = inspect.signature(method).parameters
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
        return method(**ctx)
    names = set(params) - {"self"}
    return method(**{key: value for key, value in ctx.items() if key in names})


class PermissionMixin:
    """Shared permission context and checks for views and ViewSets."""

    def permission_context(self, obj=None):
        router = getattr(self, "router", None) or getattr(self, "_built_router", None)
        router_codename = getattr(router, "codename", None) if router else None
        return dict(
            user=self.request.user,
            perm=self.permission_fullcode,
            model=self._permission_model(),
            action=self.permission_shortcode,
            obj=obj or getattr(self, "object", None),
            router=router,
            router_codename=router_codename,
        )