import djcrud
import pytest
from django.contrib.auth.models import AnonymousUser

from djcrud.router import Router
from djcrud.views import generic
from djcrud_example.routing_example.models import Item


def _make_request(rf, user):
    request = rf.get("/")
    request.user = user
    return request


@pytest.mark.django_db
def test_find_route_on_immediate_router(rf, admin_user):
    item_router = djcrud.site.routes["item"]
    create_route = item_router.routes["create"]
    request = _make_request(rf, admin_user)
    view = type(create_route)(request=request)
    assert view.router.find_route("list") is item_router.routes["list"]


@pytest.mark.django_db
def test_find_route_walks_up_to_parent_router(rf, admin_user):
    outer = djcrud.ModelRouter.clone(
        model=Item,
        routes=[
            generic.ListView,
            djcrud.Router.clone(
                codename="nested",
                routes=[
                    djcrud.ModelRouter.clone(
                        model=Item,
                        routes=[generic.CreateView],
                    ),
                ],
            ),
        ],
    )
    site = Router.clone(codename="site", routes=[outer])()
    site.build()
    inner_mc = site.routes["item"].routes["nested"].routes["item"]
    create_route = inner_mc.routes["create"]
    request = _make_request(rf, admin_user)
    view = type(create_route)(request=request)
    assert view.router.find_route("list") is site.routes["item"].routes["list"]


@pytest.mark.django_db
def test_list_view_breadcrumbs_empty(rf, admin_user):
    item_router = djcrud.site.routes["item"]
    list_route = item_router.routes["list"]
    request = _make_request(rf, admin_user)
    view = type(list_route)(request=request)
    assert view.breadcrumbs() == []


@pytest.mark.django_db
def test_create_view_breadcrumbs(rf, admin_user):
    item_router = djcrud.site.routes["item"]
    create_route = item_router.routes["create"]
    request = _make_request(rf, admin_user)
    view = type(create_route)(request=request)
    crumbs = view.breadcrumbs()
    assert len(crumbs) == 2
    assert type(crumbs[0]).__name__ == "ListView"
    assert crumbs[1] is view


@pytest.mark.django_db
def test_create_view_breadcrumbs_omits_list_without_permission(rf):
    item_router = djcrud.site.routes["item"]
    create_route = item_router.routes["create"]
    request = _make_request(rf, AnonymousUser())
    view = type(create_route)(request=request)
    crumbs = view.breadcrumbs()
    assert len(crumbs) == 1
    assert crumbs[0] is view


@pytest.mark.django_db
def test_update_view_breadcrumbs(rf, admin_user):
    obj = Item.objects.create(name="Alice")
    item_router = djcrud.site.routes["item"]
    update_route = item_router.routes["update"]
    request = _make_request(rf, admin_user)
    view = type(update_route)(request=request, object=obj, pk=obj.pk)
    crumbs = view.breadcrumbs()
    assert len(crumbs) == 3
    assert type(crumbs[0]).__name__ == "ListView"
    assert type(crumbs[1]).__name__ == "DetailView"
    assert crumbs[1].object == obj
    assert crumbs[2] is view


@pytest.mark.django_db
def test_detail_view_breadcrumbs_without_self(rf, admin_user):
    obj = Item.objects.create(name="Alice")
    item_router = djcrud.site.routes["item"]
    detail_route = item_router.routes["detail"]
    request = _make_request(rf, admin_user)
    view = type(detail_route)(request=request, object=obj, pk=obj.pk)
    crumbs = view.breadcrumbs()
    assert len(crumbs) == 2
    assert type(crumbs[0]).__name__ == "ListView"
    assert type(crumbs[1]).__name__ == "DetailView"
    assert crumbs[1].object == obj
    assert view not in crumbs


@pytest.mark.django_db
def test_update_view_breadcrumb_titles(rf, admin_user):
    obj = Item.objects.create(name="Alice")
    item_router = djcrud.site.routes["item"]
    update_route = item_router.routes["update"]
    request = _make_request(rf, admin_user)
    view = type(update_route)(request=request, object=obj, pk=obj.pk)
    crumbs = view.breadcrumbs()
    assert [crumb.breadcrumb_title for crumb in crumbs] == [
        item_router.routes["list"].title,
        str(obj),
        "Change Item",
    ]


@pytest.mark.django_db
def test_detail_view_titles(rf, admin_user):
    obj = Item.objects.create(name="Alice")
    item_router = djcrud.site.routes["item"]
    detail_route = item_router.routes["detail"]
    request = _make_request(rf, admin_user)
    view = type(detail_route)(request=request, object=obj, pk=obj.pk)
    assert view.title == "Detail"
    crumbs = view.breadcrumbs()
    assert [crumb.breadcrumb_title for crumb in crumbs] == [
        item_router.routes["list"].title,
        str(obj),
    ]


@pytest.mark.django_db
def test_history_view_titles(rf, admin_user):
    obj = Item.objects.create(name="Alice")
    item_router = djcrud.site.routes["item"]
    history_route = item_router.routes["history"]
    request = _make_request(rf, admin_user)
    view = type(history_route)(request=request, object=obj, pk=obj.pk)
    assert view.title == "History"
    assert view.breadcrumb_title == "History"
    crumbs = view.breadcrumbs()
    assert [crumb.breadcrumb_title for crumb in crumbs] == [
        item_router.routes["list"].title,
        str(obj),
        "History",
    ]


@pytest.mark.django_db
def test_object_menu_titles(rf, admin_user):
    obj = Item.objects.create(name="Alice")
    item_router = djcrud.site.routes["item"]
    history_route = item_router.routes["history"]
    request = _make_request(rf, admin_user)
    view = type(history_route)(request=request, object=obj, pk=obj.pk)
    menu = view.router.model_router.get_tagged_views(
        "object",
        request=request,
        object=obj,
    )
    assert {item.title for item in menu} == {
        "Detail",
        "Change Item",
        "Delete",
        "History",
    }
