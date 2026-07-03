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
        if obj is None:
            obj = getattr(self, "object", None)
        if obj is None:
            # For list-action views (which use object_list for targets), provide
            # a representative object for context if available. This ensures
            # object-dependent permission checks always receive an obj when
            # the view has a populated selection.
            try:
                ol = getattr(self, "object_list", None)
                if ol:
                    obj = next(iter(ol))
            except Exception:
                pass
        return dict(
            user=self.request.user,
            perm=self.permission_fullcode,
            model=self._permission_model(),
            action=self.permission_shortcode,
            obj=obj,
        )

    def get_permission_targets(self):
        """Return the object(s) this view acts upon for per-target permission checks.

        Default returns []. Dedicated mixins provide better targets:

        - :class:`~djcrud.views.action.ObjectPermissionMixin` for single ``self.object``
        - :class:`~djcrud.views.action.ObjectListPermissionMixin` for ``self.object_list``

        Empty list means only the general (view-level) permission applies.
        """
        return []
