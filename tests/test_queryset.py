import pytest
from django.http import Http404

import djcrud
from djcrud.views.delete import DeleteObjectsView
from djcrud_example.routing_example.models import Item


@pytest.mark.django_db
def test_router_get_queryset_scopes_list(rf, admin_user):
    owned = Item.objects.create(name="owned")
    Item.objects.create(name="other")

    class ItemRouter(djcrud.ModelRouter):
        model = Item

        def get_queryset(self, *, user, model, action, perm, obj=None):
            return self.model.objects.filter(name="owned")

    router = ItemRouter()
    router.build()
    request = rf.get("/item/")
    request.user = admin_user
    view = type(router.routes["list"])(request=request)
    view.setup(request)
    assert list(view.get_queryset().values_list("name", flat=True)) == ["owned"]


@pytest.mark.django_db
def test_get_object_404_outside_scoped_queryset(rf, admin_user):
    owned = Item.objects.create(name="owned")
    other = Item.objects.create(name="other")

    class ItemRouter(djcrud.ModelRouter):
        model = Item

        def get_queryset(self, *, user, model, action, perm, obj=None):
            return self.model.objects.filter(name="owned")

    router = ItemRouter()
    router.build()
    request = rf.get(f"/item/{other.pk}/detail/")
    request.user = admin_user
    view = type(router.routes["detail"])(request=request)
    with pytest.raises(Http404):
        view.setup(request, pk=other.pk)


@pytest.mark.django_db
def test_get_object_returns_scoped_object(rf, admin_user):
    owned = Item.objects.create(name="owned")

    class ItemRouter(djcrud.ModelRouter):
        model = Item

        def get_queryset(self, *, user, model, action, perm, obj=None):
            return self.model.objects.filter(name="owned")

    router = ItemRouter()
    router.build()
    request = rf.get(f"/item/{owned.pk}/detail/")
    request.user = admin_user
    view = type(router.routes["detail"])(request=request)
    view.setup(request, pk=owned.pk)
    assert view.object.pk == owned.pk


@pytest.mark.django_db
def test_list_action_intersects_scoped_queryset(rf, admin_user):
    a = Item.objects.create(name="owned")
    b = Item.objects.create(name="other")

    class ItemRouter(djcrud.ModelRouter):
        model = Item
        routes = djcrud.ModelRouter.routes

        def get_queryset(self, *, user, model, action, perm, obj=None):
            return self.model.objects.filter(name="owned")

    router = ItemRouter()
    router.build()
    request = rf.get(f"/item/deleteobjects/?pks={a.pk}&pks={b.pk}")
    request.user = admin_user
    view = type(router.routes["deleteobjects"])(request=request)
    assert list(view.object_list.values_list("pk", flat=True)) == [a.pk]
    assert view.invalid_pks == 1