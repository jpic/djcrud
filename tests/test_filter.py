"""Tests for list filter form."""

import time
from urllib.parse import parse_qs, urlparse

import pytest
from django import forms
from django.template import Context, Template
from django.views import generic

from djcrud.view import ViewMixin
from djcrud.views.filter import FilterMixin
from djcrud.views.list import ListMixin, ListView
from djcrud.views.search import SearchMixin
from djcrud.views.template import TemplateViewMixin
from djcrud.model import ModelMixin
from djcrud_example.routing_example.models import Item


def _wait_for_url_without(browser, substring, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if substring not in browser.url:
            return
        time.sleep(0.1)
    raise AssertionError(f"{substring!r} still in {browser.url!r}")


def _open_filter_sidebar(browser):
    sidebar = browser.find_by_css("#djcrud-filter-sidebar").first
    if "is-hidden" in (sidebar["class"] or ""):
        browser.find_by_css("filter-sidebar-toggle button").first.click()
    assert browser.is_element_present_by_css(
        "#djcrud-filter-sidebar:not(.is-hidden)",
        wait_time=2,
    )


class _MockRouter:
    model = Item
    codename = "item"
    router = None
    routes = []

    @property
    def model_router(self):
        return self

    def get_queryset(self, *, user, model, action, perm, obj=None):
        return model._default_manager.all()

    def find_route(self, codename):
        return None

    def _iter_tagged_routes(self, tag):
        return []


def _build_filter_view(**attrs):
    return ListView.clone(**attrs)


@pytest.fixture
def mock_router():
    return _MockRouter()


@pytest.mark.django_db
def test_search_auto_added_to_filter_field_names(rf, admin_user, mock_router):
    view_cls = _build_filter_view()
    request = rf.get("/")
    request.user = admin_user
    view = view_cls()
    view.router = mock_router
    view.setup(request)

    assert view.get_filter_field_names() == ["search"]
    assert "search" in view.filter_form.fields


@pytest.mark.django_db
def test_filter_fields_extend_defaults(rf, admin_user, mock_router):
    view_cls = _build_filter_view(filter_fields=["name"])
    request = rf.get("/")
    request.user = admin_user
    view = view_cls()
    view.router = mock_router
    view.setup(request)

    assert view.get_filter_field_names() == ["search", "name"]
    assert "name" in view.filter_form.fields


@pytest.mark.django_db
def test_no_filter_form_without_fields(rf, admin_user, mock_router):
    view_cls = _build_filter_view()
    request = rf.get("/")
    request.user = admin_user
    view = view_cls()
    view.router = mock_router
    view.setup(request)
    view.search_fields = []

    assert view.get_filter_field_names() == []
    assert view.filter_form is None


@pytest.mark.django_db
def test_filter_fields_without_search(rf, admin_user, mock_router):
    view_cls = _build_filter_view(filter_fields=["name"])
    request = rf.get("/")
    request.user = admin_user
    view = view_cls()
    view.router = mock_router
    view.setup(request)
    view.search_fields = []

    assert view.get_filter_field_names() == ["name"]
    assert "search" not in view.filter_form.fields


@pytest.mark.django_db
def test_filter_form_class_override(rf, admin_user, mock_router):
    class CustomFilterForm(forms.Form):
        q = forms.CharField(required=False)

    view_cls = _build_filter_view(filter_form_class=CustomFilterForm)
    request = rf.get("/")
    request.user = admin_user
    view = view_cls()
    view.router = mock_router
    view.setup(request)

    assert type(view.filter_form) is CustomFilterForm


@pytest.mark.django_db
def test_filter_attributes_include_history(rf, admin_user, mock_router):
    view_cls = _build_filter_view()
    request = rf.get("/")
    request.user = admin_user
    view = view_cls()
    view.router = mock_router
    view.setup(request)

    assert view.filter_attributes["up-history"] is True
    assert view.filter_target == "[up-list]"


@pytest.mark.django_db
def test_has_active_filters_and_clear_url(rf, admin_user, mock_router):
    view_cls = _build_filter_view()
    request = rf.get("/?search=foo&page=2&per_page=10")
    request.user = admin_user
    view = view_cls()
    view.router = mock_router
    view.setup(request)

    assert view.has_active_filters is True
    url = view.clear_filter_url()
    params = parse_qs(urlparse(url).query)
    assert urlparse(url).path == "/"
    assert "search" not in params
    assert "page" not in params
    assert params.get("per_page") == ["10"]


@pytest.mark.django_db
def test_filter_submit_label_on_filter_mixin(rf, admin_user, mock_router):
    view_cls = type(
        "TestFilterOnlyView",
        (FilterMixin, TemplateViewMixin, ModelMixin, generic.ListView),
        {},
    )
    request = rf.get("/")
    request.user = admin_user
    view = view_cls()
    view.router = mock_router
    view.setup(request)

    assert view.filter_submit_label == "Apply"


@pytest.mark.django_db
def test_filter_form_renders_in_sidebar(rf, admin_user, mock_router):
    view_cls = _build_filter_view()
    request = rf.get("/")
    request.user = admin_user
    view = view_cls()
    view.router = mock_router
    view.setup(request)
    view.object_list = view.get_queryset()

    template = Template("""
    {% load djcrud crispy_forms_tags django_tables2 %}
    {% render_table view.table 'djcrud/_tables2.html' %}
    """)
    output = template.render(Context({"view": view, "request": request}))
    assert "djcrud-filter-sidebar" in output
    assert "filter-sidebar-toggle" in output
    assert 'method="get"' in output
    assert 'name="search"' in output
    assert 'type="submit"' in output
    assert "Apply" in output
    assert 'method="undefined"' not in output
    assert "field is-grouped" not in output


@pytest.mark.django_db
def test_filter_sidebar_hidden_without_active_filters(rf, admin_user, mock_router):
    view_cls = _build_filter_view()
    request = rf.get("/")
    request.user = admin_user
    view = view_cls()
    view.router = mock_router
    view.setup(request)
    view.object_list = view.get_queryset()

    template = Template("""
    {% load djcrud crispy_forms_tags django_tables2 %}
    {% render_table view.table 'djcrud/_tables2.html' %}
    """)
    output = template.render(Context({"view": view, "request": request}))
    assert "djcrud-filter-sidebar is-hidden" in output


@pytest.mark.django_db
def test_filter_sidebar_open_with_active_filters(rf, admin_user, mock_router):
    view_cls = _build_filter_view()
    request = rf.get("/?search=foo")
    request.user = admin_user
    view = view_cls()
    view.router = mock_router
    view.setup(request)
    view.object_list = view.get_queryset()

    template = Template("""
    {% load djcrud crispy_forms_tags django_tables2 %}
    {% render_table view.table 'djcrud/_tables2.html' %}
    """)
    output = template.render(Context({"view": view, "request": request}))
    assert "djcrud-filter-sidebar is-hidden" not in output
    assert 'id="djcrud-filter-sidebar"' in output


@pytest.mark.django_db
def test_filter_fields_narrow_queryset(rf, admin_user, mock_router, db):
    Item.objects.create(name="alpha")
    Item.objects.create(name="beta")
    view_cls = _build_filter_view(filter_fields=["name"])
    request = rf.get("/?name=alpha")
    request.user = admin_user
    view = view_cls()
    view.router = mock_router
    view.setup(request)

    names = list(view.get_queryset().values_list("name", flat=True))
    assert names == ["alpha"]


@pytest.mark.django_db
def test_search_filters_queryset(rf, admin_user, mock_router, db):
    Item.objects.create(name="alpha")
    Item.objects.create(name="beta")
    view_cls = _build_filter_view()
    request = rf.get("/?search=alpha")
    request.user = admin_user
    view = view_cls()
    view.router = mock_router
    view.setup(request)

    names = list(view.get_queryset().values_list("name", flat=True))
    assert names == ["alpha"]


@pytest.mark.django_db
def test_filter_form_method_is_get(rf, admin_user, mock_router):
    """Regression: form method must be 'get', not leaked context named 'method'."""
    import djcrud

    list_route = djcrud.site.routes["auth"].routes["user"].routes["list"]
    request = rf.get("/auth/user/?search=foo")
    request.user = admin_user
    view = type(list_route)()
    view.setup(request)
    view.object_list = view.get_queryset()

    template = Template("""
    {% load djcrud crispy_forms_tags django_tables2 %}
    {% render_table view.table 'djcrud/_tables2.html' %}
    """)
    output = template.render(Context({"view": view, "request": request}))
    assert "up-list" in output
    assert 'method="get"' in output
    assert 'method="undefined"' not in output
    assert "Clear" in output


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_filter_search_on_user_list(
    browser,
    live_server,
    browser_login,
    admin_user,
    many_users,
):
    browser_login()
    browser.execute_script("sessionStorage.clear()")
    browser.visit(f"{live_server.url}/auth/user/")

    assert browser.is_element_present_by_css("filter-sidebar-toggle", wait_time=5)
    _open_filter_sidebar(browser)

    form = browser.find_by_css("form.djcrud-filter-form").first
    assert form["method"] == "get"

    search_input = browser.find_by_css(
        'form.djcrud-filter-form input[name="search"]',
    ).first
    search_input.fill("user42")
    browser.find_by_css('form.djcrud-filter-form button[type="submit"]').first.click()

    assert browser.is_element_present_by_css("[up-list]", wait_time=5)
    assert browser.is_element_present_by_css(
        '[up-list][up-source*="search=user42"]',
        wait_time=5,
    )
    assert browser.is_text_present("user42", wait_time=5)

    table_text = browser.find_by_css("[up-table]").first.text
    assert "user42" in table_text
    assert "user0" not in table_text
    assert browser.find_by_css('input[name="search"]').first.value == "user42"
    assert browser.is_text_present("Clear", wait_time=2)


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_filter_clear_on_user_list(
    browser,
    live_server,
    browser_login,
    admin_user,
    many_users,
):
    browser_login()
    browser.visit(f"{live_server.url}/auth/user/?search=user42")

    assert browser.is_element_present_by_css(
        "form.djcrud-filter-form .djcrud-filter-clear",
        wait_time=5,
    )
    browser.find_by_css("form.djcrud-filter-form .djcrud-filter-clear").first.click()

    assert browser.is_element_present_by_css("[up-list]", wait_time=5)
    _wait_for_url_without(browser, "search=")
    assert browser.is_text_present("user0", wait_time=5)
    assert browser.find_by_css('input[name="search"]').first.value == ""


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_filter_sidebar_toggle(
    browser,
    live_server,
    browser_login,
    admin_user,
    many_users,
):
    browser_login()
    browser.execute_script("sessionStorage.clear()")
    browser.visit(f"{live_server.url}/auth/user/")

    assert browser.is_element_present_by_css(
        "#djcrud-filter-sidebar.is-hidden", wait_time=5
    )

    browser.find_by_css("filter-sidebar-toggle button").first.click()
    assert browser.is_element_present_by_css(
        "#djcrud-filter-sidebar:not(.is-hidden)",
        wait_time=2,
    )

    browser.find_by_css("filter-sidebar-toggle button").first.click()
    assert browser.is_element_present_by_css(
        "#djcrud-filter-sidebar.is-hidden",
        wait_time=2,
    )
