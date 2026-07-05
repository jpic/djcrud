import pytest

import djcrud
from djcrud.permissions import _lookup_perm, _lookup_scoper, is_owner
from djcrud_example.routing_example.models import Item
from djcrud_example.security_example.models import Document


@pytest.mark.django_db
def test_add_perm_grants_without_django_perm(rf):
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
def test_add_queryset_scopes_rows(rf, admin_user):
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
def test_perm_string_registration(rf):
    from djcrud_example.models import User

    djcrud.permissions.add_perm(
        "routing_example.view_item",
        check=lambda user, **ctx: True,
    )
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
        djcrud.permissions.remove_perm("routing_example.view_item")


@pytest.mark.django_db
def test_add_perm_comma_separated_actions(rf):
    from djcrud_example.models import User

    djcrud.permissions.add_perm(Item, "view,add", check=lambda user, **ctx: True)
    try:
        reader = User.objects.create_user("reader", password="pass")
        router = djcrud.ModelRouter.clone(model=Item)()
        router.build()
        request = rf.get("/item/")
        request.user = reader
        for route_name in ("list", "create"):
            view = type(router.routes[route_name])(request=request)
            view.router = router
            assert view.has_permission() is True
    finally:
        djcrud.permissions.remove_perm(Item, "view")
        djcrud.permissions.remove_perm(Item, "add")


def test_lookup_prefers_specific_action_over_model_wide():
    djcrud.permissions.add_perm(Item, check=lambda user, **ctx: False)
    djcrud.permissions.add_perm(Item, "view", check=lambda user, **ctx: True)
    try:
        check = _lookup_perm(Item, "view", "routing_example.view_item")
        assert check is not None
        assert check(user=None, model=Item, action="view", perm="", obj=None)
    finally:
        djcrud.permissions.remove_perm(Item, "view")
        djcrud.permissions.remove_perm(Item)


@pytest.mark.django_db
def test_is_owner_predicate(django_user_model):
    from djcrud_example.views_example.models import Article

    owner = django_user_model.objects.create_user(username="owner", password="x")
    stranger = django_user_model.objects.create_user(username="stranger", password="x")
    article = Article.objects.create(title="Draft", owner=owner)

    assert is_owner(owner, obj=article) is True
    assert is_owner(stranger, obj=article) is False
    assert is_owner(owner, obj=None) is False
    assert djcrud.permissions.owner is djcrud.permissions.is_owner


def test_secured_document_rules_registered_from_djcrud_autodiscover():
    check = _lookup_perm(
        Document,
        "view",
        "security_example.view_document",
    )
    scoper = _lookup_scoper(Document, "view")
    assert check is not None
    assert scoper is not None


def test_add_search_opt_in():
    from djcrud.search import is_search_enabled

    djcrud.search.remove_search(Item)
    try:
        assert is_search_enabled(Item) is False
        djcrud.search.add_search(Item)
        assert is_search_enabled(Item) is True
    finally:
        djcrud.search.add_search(Item)


@pytest.mark.django_db
def test_get_queryset_raises_clear_error_for_model_none(rf, admin_user):
    """Plain Router + ListView without model or explicit model= should fail fast."""
    from django.core.exceptions import ImproperlyConfigured
    from django.views import generic

    from djcrud.model import ModelMixin
    from djcrud.views.list import ListMixin
    from djcrud.views.template import TemplateViewMixin

    class BareList(ListMixin, TemplateViewMixin, ModelMixin, generic.ListView):
        pass

    class SectionRouter(djcrud.Router):
        routes = [BareList]

    router = SectionRouter()
    router.build()

    request = rf.get("/section/barelist/")
    request.user = admin_user

    bare_route = router.routes[0]
    view = type(bare_route)(request=request)
    view.router = bare_route.router
    view.setup(request)

    with pytest.raises(ImproperlyConfigured) as exc:
        view.get_queryset()

    assert "model=None" in str(exc.value) or "ModelRouter" in str(exc.value)


@pytest.mark.django_db
def test_explicit_model_on_view_under_plain_router_uses_correct_scoper(rf, admin_user):
    """Workspace sharing pattern: list a different model under a plain section Router."""

    Item.objects.create(name="mine")
    Item.objects.create(name="other")

    djcrud.permissions.add_queryset(
        Item,
        scoper=lambda user, *, model, **ctx: model.objects.filter(name="mine"),
    )
    try:

        class ItemListUnderSection(djcrud.views.ListView):
            # Explicit model allows using under plain Router for custom URL structures
            # (e.g. workspace sections, invitations tabs, etc.)
            model = Item

        class WorkspaceSectionRouter(djcrud.Router):
            codename = "workspacesection"
            routes = [ItemListUnderSection]

        router = WorkspaceSectionRouter()
        router.build()

        request = rf.get("/workspacesection/itemlistundersection/")
        request.user = admin_user

        list_route = router.routes["itemlistundersection"]
        view = type(list_route)(request=request)
        view.setup(request)
        # get_queryset should go through router delegation but use view.model for scoping
        qs = view.get_queryset()
        names = list(qs.values_list("name", flat=True))
        assert names == ["mine"]
    finally:
        djcrud.permissions.remove_queryset(Item)
