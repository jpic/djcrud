import pytest
from django.urls import reverse
from djcrud_example.example_urls import Site


@pytest.mark.urls("djcrud_example.example_urls")
@pytest.mark.parametrize(
    "name,url",
    (
        ("router:view", "/router/view/"),
        ("router:sub-router:sub-view", "/router/sub-router/sub-view/"),
        (
            "router:sub-router:sub-sub-router:sub-sub-view",
            "/router/sub-router/sub-sub-router/sub-sub-view/",
        ),
    ),
)
def test_routing(name, url):
    assert reverse(name) == url


@pytest.mark.urls("djcrud_example.example_urls")
def test_view_router():
    site = Site()
    site.build()

    view = site.routes[0]
    assert view.router is site
    assert view.router.root is site
    assert view.url == "/router/view/"

    sub_router = site.routes[1]
    assert site.routes["sub-router"] == sub_router

    sub_view = site.routes[1].routes[0]
    assert sub_view.router is sub_router
    assert sub_view.router.root is site
    assert sub_view.url == "/router/sub-router/sub-view/"

    sub_sub_router = site.routes[1].routes[1]
    assert sub_router.routes["sub-view"] == sub_view

    sub_sub_view = site.routes[1].routes[1].routes[0]
    assert sub_sub_view.router is sub_sub_router
    assert sub_sub_view.router.root is site
    assert sub_sub_view.url == "/router/sub-router/sub-sub-router/sub-sub-view/"
