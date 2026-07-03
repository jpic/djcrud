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
def test_router_scoped_perm_does_not_apply_to_other_router(rf):
    from djcrud_example.models import User

    djcrud.add_perm(
        Item,
        "view",
        check=lambda user, **ctx: True,
        router="scoped-item",
    )
    try:
        reader = User.objects.create_user("reader", password="pass")

        class OtherRouter(djcrud.ModelRouter):
            model = Item

            @property
            def codename(self):
                return "other-item"

        router = OtherRouter()
        router.build()
        request = rf.get("/other/")
        request.user = reader
        view = type(router.routes["list"])(request=request)
        view.router = router
        assert view.has_permission() is False
    finally:
        djcrud.remove_perm(Item, "view", router="scoped-item")


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


def test_lookup_prefers_specific_action_over_model_wide():
    djcrud.add_perm(Item, check=lambda user, **ctx: False)
    djcrud.add_perm(Item, "view", check=lambda user, **ctx: True)
    try:
        check = _lookup_perm(Item, "view", "routing_example.view_item", None)
        assert check is not None
        assert check(
            user=None, model=Item, action="view", perm="", obj=None, router=None
        )
    finally:
        djcrud.remove_perm(Item, "view")
        djcrud.remove_perm(Item)


def test_secured_document_rules_registered_from_djcrud_autodiscover():
    check = _lookup_perm(
        Document,
        "view",
        "security_example.view_document",
        "secured-document",
    )
    scoper = _lookup_scoper(Document, "view", "secured-document")
    assert check is not None
    assert scoper is not None