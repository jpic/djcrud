from ..permission import call_with_context


class ObjectPermissionMixin:
    """Target provider for actions that operate on a single object (``self.object``).

    Use together with :class:`~djcrud.views.object.ObjectMixin` (or a *View that
    includes it) + :class:`ActionMixin`.
    """

    def get_permission_targets(self):
        obj = getattr(self, "object", None)
        return [obj] if obj is not None else []


class ObjectListPermissionMixin:
    """Target provider for bulk/list actions that operate on ``self.object_list``.

    Use together with :class:`~djcrud.views.list_action.ListActionMixin` +
    :class:`ActionMixin`.
    """

    def get_permission_targets(self):
        try:
            ol = getattr(self, "object_list", None)
            return list(ol) if ol is not None else []
        except Exception:
            return []


class ActionMixin:
    """Per-target permission checks for actions (works for both single object
    and bulk/list actions).

    The general view-level permission (based on ``permission_shortcode``) is
    checked first via ``super()``. Then, for each target returned by
    ``get_permission_targets()``, ``has_permission_for_target(target)`` is called.

    Target resolution is provided by companion mixins (compose as needed):

    - :class:`ObjectPermissionMixin` — for views with ``self.object``
    - :class:`ObjectListPermissionMixin` — for views with ``self.object_list``

    This gives a uniform, straightforward path without special-casing "no object",
    private registry lookups, or bare (no-object) permission checks for
    object-scoped actions. Targets are always provided when relevant.

    Most users do nothing. Register rules with ``djcrud.permissions.add_perm``
    (or rely on Django permissions). Override :meth:`has_permission_object` only
    for view-specific extra logic on a concrete target.

    The old ``_has_permission_without_object`` branching and private access have
    been removed.
    """

    def has_permission(self):
        """General permission + per-target checks for the action's targets."""
        if not super().has_permission():
            return False
        for target in self.get_permission_targets():
            if not self.has_permission_for_target(target):
                return False
        return True

    def has_permission_for_target(self, target):
        """Whether the action is permitted on this specific *target*.

        Forces the registry check with a real obj=target (so add_perm checks,
        is_owner, etc. receive proper instances) then the hook.
        """
        ctx = self.permission_context(obj=target)
        router = getattr(self, "router", None)
        if router is not None:
            if not call_with_context(router.has_permission, ctx):
                return False
        return self.has_permission_object(target)

    def has_permission_object(self, obj):
        """Hook for additional per-object denial after registry checks pass.

        *obj* is always a concrete target (from get_permission_targets via
        has_permission_for_target). Return False to deny the action for this
        target.

        Example:
            def has_permission_object(self, obj):
                return obj.name == "mine"
        """
        return True
