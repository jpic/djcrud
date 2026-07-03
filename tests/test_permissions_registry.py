import pytest

import djcrud
from djcrud.permissions import _lookup_perm, _lookup_scoper
from djcrud_example.routing_example.models import Item
from djcrud_example.security_example.models import Document


@pytest.mark.django_db
def test_add_perm_grants_without_django_perm(rf):
    from djcrud_example.models import User

    djcrud.add_perm(Item, "view", check=lambda user, **ctx: True)
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
        djcrud.remove_perm(Item, "view")


@pytest.mark.django_db
def test_add_queryset_scopes_rows(rf, admin_user):
    Item.objects.create(name="mine")
    Item.objects.create(name="theirs")

    djcrud.add_queryset(
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
        djcrud.remove_queryset(Item)


@pytest.mark.django_db
def test_perm_string_registration(rf):
    from djcrud_example.models import User

    djcrud.add_perm(
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
        djcrud.remove_perm("routing_example.view_item")


@pytest.mark.django_db
def test_add_perm_comma_separated_actions(rf):
    from djcrud_example.models import User

    djcrud.add_perm(Item, "view,add", check=lambda user, **ctx: True)
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
        djcrud.remove_perm(Item, "view")
        djcrud.remove_perm(Item, "add")


def test_lookup_prefers_specific_action_over_model_wide():
    djcrud.add_perm(Item, check=lambda user, **ctx: False)
    djcrud.add_perm(Item, "view", check=lambda user, **ctx: True)
    try:
        check = _lookup_perm(Item, "view", "routing_example.view_item")
        assert check is not None
        assert check(
            user=None, model=Item, action="view", perm="", obj=None
        )
    finally:
        djcrud.remove_perm(Item, "view")
        djcrud.remove_perm(Item)


@pytest.mark.django_db
def test_is_owner_predicate(django_user_model):
    from djcrud_example.views_example.models import Article

    owner = django_user_model.objects.create_user(username="owner", password="x")
    stranger = django_user_model.objects.create_user(username="stranger", password="x")
    article = Article.objects.create(title="Draft", owner=owner)

    assert djcrud.is_owner(owner, obj=article) is True
    assert djcrud.is_owner(stranger, obj=article) is False
    assert djcrud.is_owner(owner, obj=None) is False
    assert djcrud.owner is djcrud.is_owner


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
    from djcrud.permissions import is_search_enabled

    djcrud.remove_search(Item)
    try:
        assert is_search_enabled(Item) is False
        djcrud.add_search(Item)
        assert is_search_enabled(Item) is True
    finally:
        djcrud.add_search(Item)
