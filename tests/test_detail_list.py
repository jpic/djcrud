import pytest

from djcrud.views.list import DetailListView
from djcrud_example.routing_example.models import Item


class _ItemRouter:
    model = Item
    codename = "item"
    router = None
    routes = []

    @property
    def model_router(self):
        return self

    def get_queryset(self, *, user, model, action, perm, obj=None):
        return model._default_manager.all()

    def _iter_tagged_routes(self, tag):
        return []


class ItemNamesView(DetailListView):
    list_model = Item

    def get_queryset(self):
        return Item.objects.all()


@pytest.mark.django_db
def test_detail_list_view_uses_list_model_for_tables():
    Item.objects.create(name="alpha")
    view = ItemNamesView()
    view.router = _ItemRouter()

    assert view.model is Item
