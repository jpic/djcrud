from django.contrib.auth.models import AnonymousUser

import djcrud
from djcrud import tags
from djcrud.router import Router, model_router_codename
from djcrud_example.security_example.models import Document
from djcrud.view import View
from djcrud_example.routing_example.models import Item


def test_get_tagged_views(rf, admin_user):
    class LoginView(View):
        tags = [tags.TOPBAR]

        def has_permission(self):
            return not self.request.user.is_authenticated

    class LogoutView(View):
        tags = [tags.TOPBAR]

        def has_permission(self):
            return self.request.user.is_authenticated

    class Site(Router):
        routes = [
            LoginView,
            Router.clone(routes=[LogoutView]),
        ]

    site = Site()
    site.build()
    request = rf.get("/")
    request.user = AnonymousUser()
    result = site.get_tagged_views(tags.TOPBAR, request=request)
    assert len(result) == 1
    assert type(result[0]).__name__ == "LoginView"
    assert result[0].request is request

    request.user = admin_user
    result = site.get_tagged_views(tags.TOPBAR, request=request)
    assert len(result) == 1
    assert type(result[0]).__name__ == "LogoutView"


def test_model_router_codename_from_class_name():
    class SecuredDocumentRouter(djcrud.ModelRouter):
        model = Document

    assert model_router_codename(SecuredDocumentRouter) == "secured-document"
    assert model_router_codename(djcrud.ModelRouter.clone(model=Item)) == "item"


def test_navigation_list_inherits_router_icon(rf, admin_user):
    class ItemRouter(djcrud.ModelRouter):
        model = Item
        icon = "inbox"

    router = ItemRouter()
    router.build()
    request = rf.get("/item/")
    request.user = admin_user
    list_view = type(router.routes["list"])(request=request)
    assert list_view.icon == "inbox"


def test_site_routes_append():
    class Extra(djcrud.View):
        pass

    site = djcrud.Site()
    site.routes.append(Extra)
    assert Extra in type(site)._declaration


def test_registry():
    from djcrud.registry import Registry

    class MyRouter(Router):
        routes = [View]

    router = MyRouter()
    router.build()
    assert isinstance(router.routes, Registry)
    assert not hasattr(View, "router")
