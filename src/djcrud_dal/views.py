from dal_alight.views import AlightQuerySetView

from djcrud.model import ModelMixin
from djcrud.view import ViewMixin


class AutocompleteView(ModelMixin, ViewMixin, AlightQuerySetView):
    """DAL Alight autocomplete endpoint for a model router's rows.

    Row scope comes from the detail-route ``view`` permission registry,
    not the list queryset.
    """

    permission_shortcode = "view"
    tags = []

    def get_search_fields(self):
        list_route = self.router.find_route("list")
        if list_route is not None:
            return type(list_route)().search_fields
        return super().get_search_fields()

    def get_queryset(self):
        mc = self.router.model_router
        model = self.model
        ctx = self.permission_context()
        return mc.get_queryset(
            user=ctx["user"],
            model=model,
            action="view",
            perm=f"{model._meta.app_label}.view_{model._meta.model_name}",
            obj=None,
        )