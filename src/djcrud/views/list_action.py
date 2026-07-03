import functools

from django.forms import Form

from ..model import ModelMixin
from .. import tags
from .action import ActionMixin, ObjectListPermissionMixin
from .form import FormMixin, FormView


class ListActionMixin(ModelMixin, FormMixin, ObjectListPermissionMixin):
    """Bulk actions from the list action bar (selected row PKs in ``pks``).

    Brings in :class:`~djcrud.views.action.ObjectListPermissionMixin` so that
    when combined with :class:`~djcrud.views.action.ActionMixin` (as
    :class:`ListActionView` does), per-target permission checks (general
    shortcode + :meth:`~djcrud.views.action.ActionMixin.has_permission_object`
    per row) are performed against each row in ``self.object_list``.

    The bar itself lists *configured* LIST_ACTION routes (see
    :attr:`~djcrud.views.list.ListMixin.list_actions`, which walks tagged
    routes directly with no permission check). Per-object allowance (always
    checked with a concrete object) is propagated via ``data-list-actions``
    on checkboxes and filtered client-side.

    Attributes:
        tags (list[str]): Must include ``djcrud.tags.LIST_ACTION`` for discovery.
        title (str): Action label in the list action bar.
        icon (str): Bootstrap Icons name.
        color (str): Bulma button colour modifier.
        message (str): Confirmation text in the action modal.
        form_class (type): Form class for the action. Default empty ``Form``.
    """

    tags = [tags.LIST_ACTION]  # see djcrud.tags.LIST_ACTION

    def get_queryset(self):
        """Scoped queryset from the enclosing router."""
        return super().get_queryset()

    @functools.cached_property
    def pks(self):
        """Selected primary keys from GET or POST."""
        return self.request.GET.getlist("pks") or self.request.POST.getlist("pks")

    @functools.cached_property
    def object_list(self):
        """Intersection of :attr:`pks` with the scoped queryset."""
        return self.get_queryset().filter(pk__in=self.pks)

    @functools.cached_property
    def invalid_pks(self):
        """Count of PKs outside the scoped queryset."""
        return len(self.pks) - self.object_list.count()

    def get_success_url(self):
        """Redirect back to the list view after the action."""
        list_route = self.router.find_route("list")
        return type(list_route)(request=self.request).url

    def get_form_class(self):
        """Return :attr:`form_class` or Django's base :class:`~django.forms.Form`."""
        return getattr(self, "form_class", None) or Form

    @property
    def form_attributes(self):
        """Form tag attributes including list-action selection cleanup."""
        attrs = dict(FormMixin.form_attributes)
        attrs["up-on-finished"] = "djcrudClearListActionSelections()"
        return attrs

    def unpoly_attributes(self, context=""):
        attrs = super().unpoly_attributes(context)
        if context == "list_action_bar":
            attrs["data-list-action"] = "urlupdate"
            attrs["up-on-accepted"] = (
                "djcrudClearListActionSelections(); up.visit(response.url)"
            )
        return attrs


class ListActionView(ListActionMixin, ActionMixin, FormView):
    """Bulk action form opened from the list action bar.

    Includes :class:`~djcrud.views.action.ActionMixin` + :class:`~djcrud.views.action.ObjectListPermissionMixin`
    (via the mixin) so per-target permission checks are performed uniformly.
    Override :meth:`~djcrud.views.action.ActionMixin.has_permission_object` for
    extra per-row rules after the registry check.
    """

    pass
