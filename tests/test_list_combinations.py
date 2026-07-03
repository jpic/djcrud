"""Test all composable list mixin combinations."""

import pytest
from django.views import generic

from djcrud.views.filter import FilterMixin
from djcrud.views.list import ListMixin
from djcrud.views.search import SearchMixin
from djcrud.views.pagination import PaginationMixin
from djcrud.views.tables2 import Tables2Mixin
from djcrud.views.template import TemplateViewMixin
from djcrud.model import ModelMixin
from djcrud_example.routing_example.models import Item


class _MockRouter:
    model = Item
    codename = "item"
    router = None
    routes = []

    @property
    def model_router(self):
        return self

    def get_queryset(self, *, user, model, action, perm, obj=None):
        return model._default_manager.all()

    def find_route(self, codename):
        return None


MISSING = object()


def build_list_view(*mixins, paginate_by=MISSING, **attrs):
    bases = (
        ListMixin,
        *mixins,
        TemplateViewMixin,
        ModelMixin,
        generic.ListView,
    )
    if paginate_by is not MISSING:
        attrs["paginate_by"] = paginate_by
    if SearchMixin in mixins or FilterMixin in mixins:

        def get_queryset(self):
            qs = ModelMixin.get_queryset(self)
            if self.filter_fields and self.filterset is not None:
                qs = self.filterset.qs
            if hasattr(self, "search_filter"):
                qs = self.search_filter(qs)
            return qs

        attrs["get_queryset"] = get_queryset
    return type("TestListView", bases, attrs)


@pytest.fixture
def routing_items(db):
    return [Item.objects.create(name=f"item{i:02d}") for i in range(30)]


@pytest.fixture
def mock_router():
    return _MockRouter()


def _dispatch(view_cls, request, router):
    view = view_cls()
    view.router = router
    view.setup(request)
    view.object_list = view.get_queryset()
    paginate_by = view.get_paginate_by(view.object_list)
    if paginate_by:
        paginator, page, object_list, is_paginated = view.paginate_queryset(
            view.object_list,
            paginate_by,
        )
        view.object_list = object_list
        view.page_obj = page
        view._paginator = paginator
        view.is_paginated = is_paginated
    return view


@pytest.mark.django_db
def test_bare_list(rf, admin_user, routing_items, mock_router):
    view_cls = build_list_view()
    request = rf.get("/")
    request.user = admin_user
    view = _dispatch(view_cls, request, mock_router)

    assert len(view.object_list) == 30
    assert getattr(view, "page_obj", None) is None
    assert "table" not in type(view).__dict__


@pytest.mark.django_db
def test_filter_only(rf, admin_user, routing_items, mock_router):
    view_cls = build_list_view(
        SearchMixin,
        FilterMixin,
        paginate_by=None,
    )
    request = rf.get("/?search=item1")
    request.user = admin_user
    view = _dispatch(view_cls, request, mock_router)

    assert all("item1" in obj.name for obj in view.object_list)
    assert len(view.object_list) >= 10
    assert getattr(view, "page_obj", None) is None


@pytest.mark.django_db
def test_paginate_only(rf, admin_user, routing_items, mock_router):
    view_cls = build_list_view(
        PaginationMixin,
    )
    request = rf.get("/?per_page=10&page=2")
    request.user = admin_user
    view = _dispatch(view_cls, request, mock_router)

    assert len(view.object_list) == 10
    assert view.page.number == 2
    assert view.paginator.per_page == 10


@pytest.mark.django_db
def test_table_only(rf, admin_user, routing_items, mock_router):
    view_cls = build_list_view(
        Tables2Mixin,
        paginate_by=None,
    )
    request = rf.get("/")
    request.user = admin_user
    view = _dispatch(view_cls, request, mock_router)

    assert len(view.table.rows) == 30
    assert getattr(view, "page_obj", None) is None


@pytest.mark.django_db
def test_filter_and_paginate(rf, admin_user, routing_items, mock_router):
    view_cls = build_list_view(
        SearchMixin,
        FilterMixin,
        PaginationMixin,
    )
    request = rf.get("/?search=item&per_page=5&page=2")
    request.user = admin_user
    view = _dispatch(view_cls, request, mock_router)

    assert len(view.object_list) == 5
    assert view.page.number == 2
    assert all("item" in obj.name for obj in view.object_list)


@pytest.mark.django_db
def test_filter_and_table(rf, admin_user, routing_items, mock_router):
    view_cls = build_list_view(
        SearchMixin,
        FilterMixin,
        Tables2Mixin,
        paginate_by=None,
    )
    request = rf.get("/?search=item2")
    request.user = admin_user
    view = _dispatch(view_cls, request, mock_router)

    assert getattr(view, "page_obj", None) is None
    assert len(view.table.rows) == 10
    assert all("item2" in row.record.name for row in view.table.rows)


@pytest.mark.django_db
def test_paginate_and_table(rf, admin_user, routing_items, mock_router):
    view_cls = build_list_view(
        PaginationMixin,
        Tables2Mixin,
    )
    request = rf.get("/?per_page=10")
    request.user = admin_user
    view = _dispatch(view_cls, request, mock_router)

    assert len(view.object_list) == 10
    assert len(view.table.rows) == 10
    assert view.paginator.per_page == 10


@pytest.mark.django_db
def test_full_list_view(rf, admin_user, routing_items, mock_router):
    from djcrud.views.list import ListView

    view_cls = type("FullListView", (ListView,), {})
    request = rf.get("/?search=item&per_page=5&page=2")
    request.user = admin_user
    view = _dispatch(view_cls, request, mock_router)

    assert len(view.object_list) == 5
    assert view.page.number == 2
    assert len(view.table.rows) == 5


@pytest.mark.django_db
def test_invalid_per_page_falls_back(rf, admin_user, routing_items, mock_router):
    view_cls = build_list_view(PaginationMixin)
    request = rf.get("/?per_page=999")
    request.user = admin_user
    view = _dispatch(view_cls, request, mock_router)

    assert view.paginator.per_page == 25
