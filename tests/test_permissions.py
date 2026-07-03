import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import resolve_url
from django.template.response import TemplateResponse

import djcrud
from djcrud.views.update import UpdateView
from djcrud_example.routing_example.models import Item


def grant_perm(user, app_label, codename):
    content_type = ContentType.objects.get(
        app_label=app_label, model=codename.split("_")[-1]
    )
    perm = Permission.objects.get(content_type=content_type, codename=codename)
    user.user_permissions.add(perm)


@pytest.mark.django_db
def test_list_permission_superuser_only_by_default(rf, admin_user):
    user = djcrud.site.routes["item"].routes["list"]
    request = rf.get("/item/")
    request.user = admin_user
    view = type(user)(request=request)
    assert view.permission_fullcode == "routing_example.view_item"
    assert view.has_permission() is True

    from djcrud_example.models import User

    regular = User.objects.create_user("regular", password="pass")
    request.user = regular
    view = type(user)(request=request)
    assert view.has_permission() is False


@pytest.mark.django_db
def test_crud_permissions_use_django_defaults(rf, admin_user):
    from djcrud_example.models import User

    regular = User.objects.create_user("editor", password="pass")
    grant_perm(regular, "routing_example", "change_item")

    item_router = djcrud.site.routes["item"]
    request = rf.get("/item/1/update/")
    request.user = regular
    item = Item.objects.create(name="A")
    view = type(item_router.routes["update"])(request=request, pk=item.pk)
    assert view.permission_fullcode == "routing_example.change_item"
    assert view.has_permission() is True


@pytest.mark.django_db
def test_has_permission_override_bypasses_router(rf):
    class PublicView(djcrud.View):
        def has_permission(self):
            return True

    request = rf.get("/")
    from django.contrib.auth.models import AnonymousUser

    request.user = AnonymousUser()
    view = PublicView(request=request)
    assert view.has_permission() is True


@pytest.mark.django_db
def test_dispatch_forbidden_for_authenticated_denied(rf, admin_user):
    from djcrud_example.models import User

    regular = User.objects.create_user("regular", password="pass")
    list_route = djcrud.site.routes["item"].routes["list"]
    request = rf.get("/item/")
    request.user = regular
    view = type(list_route)(request=request)
    response = view.dispatch(request)
    assert response.status_code == 403
    assert isinstance(response, TemplateResponse)

    from django.contrib.auth.models import AnonymousUser

    request.user = AnonymousUser()
    view = type(list_route)(request=request)
    response = view.dispatch(request)
    assert response.status_code == 302
    assert response.url == resolve_url("/auth/login/") + "?next=/item/"


@pytest.mark.django_db
def test_action_mixin_object_permission(rf, admin_user):
    item = Item.objects.create(name="mine")
    other = Item.objects.create(name="other")

    class RestrictedUpdate(UpdateView):
        def has_permission_object(self):
            return self.object.name == "mine"

    router = djcrud.ModelRouter.clone(model=Item, routes=[RestrictedUpdate])()
    router.build()
    request = rf.get("/")
    request.user = admin_user

    update_route = router.routes["restrictedupdate"]
    view = type(update_route)(request=request)
    view.setup(request, pk=item.pk)
    assert view.has_permission() is True

    view = type(update_route)(request=request)
    view.setup(request, pk=other.pk)
    assert view.has_permission() is False


@pytest.mark.django_db
def test_get_tagged_views_respects_permissions(rf, admin_user):
    from djcrud_example.models import User

    regular = User.objects.create_user("regular", password="pass")
    item_router = djcrud.site.routes["item"]
    request = rf.get("/item/")
    request.user = regular
    views = item_router.get_tagged_views("navigation", request=request)
    assert views == []

    request.user = admin_user
    views = item_router.get_tagged_views("navigation", request=request)
    assert len(views) == 1
    assert type(views[0]).__name__ == "ListView"


@pytest.mark.django_db
def test_registry_perm_grants_list_access(rf):
    from djcrud_example.models import User

    djcrud.permissions.add_perm(Item, "view", check=lambda user, **ctx: True)
    try:
        reader = User.objects.create_user("reader", password="pass")
        router = djcrud.ModelRouter.clone(model=Item)()
        router.build()
        request = rf.get("/item/")
        request.user = reader
        view = type(router.routes["list"])(request=request)
        view.router = router
        assert view.has_permission() is True
    finally:
        djcrud.permissions.remove_perm(Item, "view")


@pytest.mark.django_db
def test_registry_queryset_scopes_list(rf, admin_user):
    Item.objects.create(name="mine")
    Item.objects.create(name="theirs")
    djcrud.permissions.add_queryset(
        Item,
        scoper=lambda user, *, model, action, **ctx: model.objects.filter(name="mine"),
    )
    try:
        router = djcrud.ModelRouter.clone(model=Item)()
        router.build()
        request = rf.get("/item/")
        request.user = admin_user
        view = type(router.routes["list"])(request=request)
        view.router = router
        names = list(view.get_queryset().values_list("name", flat=True))
        assert names == ["mine"]
    finally:
        djcrud.permissions.remove_queryset(Item)


@pytest.mark.django_db
def test_list_with_view_permission_shortcode(rf):
    from djcrud_example.models import User

    reader = User.objects.create_user("reader", password="pass")
    grant_perm(reader, "routing_example", "view_item")

    router = djcrud.ModelRouter.clone(
        model=Item,
        routes=[djcrud.views.ListView.clone(permission_shortcode="view")],
    )()
    router.build()
    request = rf.get("/item/")
    request.user = reader
    view = type(router.routes["list"])(request=request)
    assert view.permission_fullcode == "routing_example.view_item"
    assert view.has_permission() is True
