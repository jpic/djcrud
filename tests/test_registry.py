import pytest
from django.urls import reverse

import djcrud
from djcrud.router import Router
from djcrud.registry import Registry
from djcrud.view import View


def test_runtime_register():
    class Extra(View):
        tags = ["navigation"]

    class MySite(Router):
        routes = []

    site = MySite()
    site.routes.append(Extra)
    site.build()
    assert site.routes["extra"].router is site


def test_register_is_idempotent_by_codename():
    class Extra(View):
        tags = ["navigation"]

    class MySite(Router):
        routes = []

    site = MySite()
    site.build()
    first = site.routes.register(Extra)
    second = site.routes.register(Extra)
    assert len(list(site.routes)) == 1
    assert site.routes["extra"] is second
    assert first is not second


def test_runtime_delete():
    class Home(djcrud.views.TemplateView):
        pass

    class Extra(djcrud.views.TemplateView):
        pass

    class MySite(Router):
        routes = [Home, Extra]

    site = MySite()
    site.build()
    del site.routes["extra"]
    assert len(list(site.routes)) == 1
    assert site.routes["home"].router is site
    with pytest.raises(KeyError):
        site.routes["extra"]


def test_whole_entry_swap():
    class Home(djcrud.views.TemplateView):
        pass

    class Dashboard(djcrud.views.TemplateView):
        urlpath = ""

    class MySite(Router):
        routes = [Home]

    site = MySite()
    site.build()
    site.routes["home"] = Dashboard.clone()
    assert site.routes["home"].urlpath == ""


def test_routes_is_declaration_before_build():
    class MySite(Router):
        routes = [View]

    site = MySite()
    assert isinstance(site.routes, list)


@pytest.mark.urls("djcrud_example.example_urls")
def test_routes_is_registry_after_build():
    class MySite(Router):
        routes = [View]

    assert isinstance(MySite.routes, list)
    site = MySite()
    site.build()
    assert isinstance(MySite.routes, list)
    assert isinstance(site.routes, Registry)


@pytest.mark.urls("djcrud_example.example_urls")
def test_nested_router_urlpatterns():
    from djcrud_example.example_urls import Site

    site = Site()
    site.build()
    assert isinstance(site.routes, Registry)
    assert reverse("router:view") == "/router/view/"
    assert (
        reverse("router:sub-router:sub-sub-router:sub-sub-view")
        == "/router/sub-router/sub-sub-router/sub-sub-view/"
    )
