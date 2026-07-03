class ActionMixin:
    """Per-object permission checks after the view-level permission passes.

    Override :meth:`has_permission_object` to deny access to individual rows
    (for example when the row is outside a scoped queryset).
    """

    def has_permission(self):
        """Check view permission, then :meth:`has_permission_object` when bound."""
        if super().has_permission():
            if getattr(self, "object", None) is not None:
                return self.has_permission_object()
            return True
        return False

    def has_permission_object(self):
        """Return whether the current user may act on :attr:`~djcrud.views.object.ObjectMixin.object`."""
        return True
