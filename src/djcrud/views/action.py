class ActionMixin:
    """Per-object permission checks after the view-level permission passes.

    Override :meth:`has_permission_object` to deny access to individual rows
    (for example when the row is outside a scoped queryset).
    """

    def has_permission(self):
        """Check view permission, then :meth:`has_permission_object` when bound."""
        obj = getattr(self, "object", None)
        if obj is None:
            without_object = self._has_permission_without_object()
            if without_object is not None:
                return without_object
        if super().has_permission():
            if obj is not None:
                return self.has_permission_object()
            return True
        return False

    def _has_permission_without_object(self):
        """List-action bar and bulk dispatch without a single bound object."""
        if "list_action" not in getattr(type(self), "tags", []):
            return None

        from ..permissions import _invoke, _lookup_perm

        ctx = self.permission_context()
        model = ctx["model"]
        if model is None:
            return None

        check = _lookup_perm(model, ctx["action"], ctx["perm"])
        object_list = self._permission_object_list()
        if object_list is not None:
            if not object_list.exists():
                return False
            if check is None:
                return None
            for row in object_list:
                if not _invoke(
                    check,
                    ctx["user"],
                    model=model,
                    action=ctx["action"],
                    perm=ctx["perm"],
                    obj=row,
                ):
                    return False
            return True

        if check is None:
            return None

        qs = (
            self.get_queryset()
            if hasattr(self, "get_queryset")
            else model._default_manager.all()
        )
        for row in qs.iterator(chunk_size=50):
            if _invoke(
                check,
                ctx["user"],
                model=model,
                action=ctx["action"],
                perm=ctx["perm"],
                obj=row,
            ):
                return True
        return False

    def _permission_object_list(self):
        """Selected rows for a bulk list action, when PKs are in the request."""
        if not hasattr(self, "pks"):
            return None
        try:
            pks = self.pks
        except Exception:
            return None
        if not pks:
            return None
        return self.object_list

    def has_permission_object(self):
        """Return whether the current user may act on :attr:`~djcrud.views.object.ObjectMixin.object`."""
        return True
