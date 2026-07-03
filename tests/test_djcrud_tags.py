import djcrud
import pytest
from django.template import Context, Template
from django.test import RequestFactory

from djcrud.templatetags.djcrud import html_attributes, unpoly_attributes
from djcrud.view import ViewMixin
from djcrud.views.pagination import PaginationMixin
from djcrud_example.routing_example.models import Item


class _PaginatedView(ViewMixin, PaginationMixin):
    pass


def test_html_attributes_renders_key_value_pairs():
    assert html_attributes({"up-layer": "new modal"}) == 'up-layer="new modal"'


def test_html_attributes_renders_boolean_true():
    assert html_attributes({"up-submit": True}) == "up-submit"


def test_html_attributes_renders_boolean_false():
    assert html_attributes({"up-follow": False}) == 'up-follow="false"'


def test_html_attributes_escapes_values():
    result = html_attributes({"data-x": '"<&>'})
    assert result == 'data-x="&quot;&lt;&amp;&gt;"'


def test_html_attributes_skips_malformed_keys():
    assert html_attributes({'foo" onclick': "x"}) == ""


def test_unpoly_attributes_filter_for_form_view():
    rf = RequestFactory()
    request = rf.get("/item/")
    item_router = djcrud.site.routes["item"]
    create_route = item_router.routes["create"]
    view = type(create_route)(request=request)
    attrs = unpoly_attributes(view, "model_menu")
    assert attrs["up-layer"] == "new modal"
    assert attrs["up-history"] is False
    assert attrs["up-accept-location"] == "/item/"


def test_unpoly_attributes_filter_without_method():
    rf = RequestFactory()
    request = rf.get("/item/1/detail/")
    item_router = djcrud.site.routes["item"]
    detail_route = item_router.routes["detail"]
    obj = Item(name="x")
    view = type(detail_route)(request=request, object=obj, pk=1)
    assert unpoly_attributes(view, "object_menu") == {
        "up-follow": True,
        "up-target": "[up-main]",
    }


def test_querystring_preserves_params():
    rf = RequestFactory()
    request = rf.get("/items/?search=foo&page=2")
    view = _PaginatedView()
    view.request = request
    result = view.querystring(page="3")
    assert "search=foo" in result
    assert "page=3" in result


def test_querystring_replaces_existing_params():
    rf = RequestFactory()
    request = rf.get("/items/?search=foo&page=2")
    view = _PaginatedView()
    view.request = request
    result = view.querystring(page="1")
    assert result.count("page=") == 1
    assert "page=1" in result
    assert "page=2" not in result


def test_pagination_url_via_eval():
    rf = RequestFactory()
    request = rf.get("/items/?search=foo")
    view = _PaginatedView()
    view.request = request
    template = Template("""
    {% load djcrud %}
    {% eval view.pagination_url 2 as url %}
    {{ url }}
    """)
    output = template.render(Context({"view": view}))
    assert "search=foo" in output
    assert "page=2" in output


def test_unpoly_attributes_filter_in_template():
    template = Template(
        "{% load djcrud %}" '{{ view|unpoly_attributes:"model_menu"|html_attributes }}'
    )
    rf = RequestFactory()
    request = rf.get("/item/")
    item_router = djcrud.site.routes["item"]
    create_route = item_router.routes["create"]
    view = type(create_route)(request=request)
    output = template.render(Context({"view": view}))
    assert 'up-layer="new modal"' in output
    assert 'up-accept-location="/item/"' in output
