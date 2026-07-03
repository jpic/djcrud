"""Test pagination controls on list views."""

import time

import pytest
from django.template import Context, Template
from selenium.webdriver.common.keys import Keys


def _wait_for_url(browser, substring, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if substring in browser.url:
            return
        time.sleep(0.1)
    raise AssertionError(f"{substring!r} not in {browser.url!r}")


@pytest.mark.django_db
def test_table_respects_per_page_query_param(rf, admin_user, many_users):
    import djcrud
    from djcrud.views.generic import ListView

    list_route = djcrud.site.routes["auth"].routes["user"].routes["list"]
    request = rf.get("/auth/user/?per_page=10")
    request.user = admin_user
    view = type(list_route)()
    view.setup(request)
    view.object_list = view.get_queryset()
    paginate_by = view.get_paginate_by(view.object_list)
    paginator, page, object_list, _ = view.paginate_queryset(
        view.object_list,
        paginate_by,
    )
    view.object_list = object_list
    view.page_obj = page

    assert paginator.per_page == 10
    assert paginator.num_pages == 6


@pytest.mark.django_db
def test_pagination_hidden_fields_preserve_query_params(rf, admin_user, many_users):
    import djcrud

    list_route = djcrud.site.routes["auth"].routes["user"].routes["list"]
    request = rf.get("/auth/user/?search=foo&sort=username&page=2&per_page=10")
    request.user = admin_user
    view = type(list_route)()
    view.setup(request)

    assert dict(view.per_page_form_hidden_fields) == {
        "search": "foo",
        "sort": "username",
    }
    assert dict(view.page_form_hidden_fields) == {
        "search": "foo",
        "sort": "username",
        "per_page": "10",
    }


@pytest.mark.django_db
def test_page_beyond_last_renders_last_page(rf, admin_user, many_users):
    import djcrud

    list_route = djcrud.site.routes["auth"].routes["user"].routes["list"]
    request = rf.get("/auth/user/?page=999")
    request.user = admin_user
    view = type(list_route)()
    view.setup(request)
    view.object_list = view.get_queryset()
    paginate_by = view.get_paginate_by(view.object_list)
    paginator, page, object_list, _ = view.paginate_queryset(
        view.object_list,
        paginate_by,
    )

    assert page.number == paginator.num_pages
    assert len(object_list) > 0


@pytest.mark.django_db
def test_page_below_one_renders_first_page(rf, admin_user, many_users):
    import djcrud

    list_route = djcrud.site.routes["auth"].routes["user"].routes["list"]
    request = rf.get("/auth/user/?page=0")
    request.user = admin_user
    view = type(list_route)()
    view.setup(request)
    view.object_list = view.get_queryset()
    paginate_by = view.get_paginate_by(view.object_list)
    _, page, _, _ = view.paginate_queryset(view.object_list, paginate_by)

    assert page.number == 1


@pytest.mark.django_db
def test_pagination_form_attributes(rf, admin_user, many_users):
    import djcrud

    list_route = djcrud.site.routes["auth"].routes["user"].routes["list"]
    request = rf.get("/auth/user/")
    request.user = admin_user
    view = type(list_route)()
    view.setup(request)

    assert view.pagination_form_attributes == {
        "up-submit": True,
        "up-target": "[up-list]",
        "up-history": True,
        "up-autosubmit": True,
    }


@pytest.mark.django_db
def test_pagination_renders_autosubmit_forms(rf, admin_user, many_users):
    import djcrud

    list_route = djcrud.site.routes["auth"].routes["user"].routes["list"]
    request = rf.get("/auth/user/")
    request.user = admin_user
    view = type(list_route)()
    view.setup(request)
    view.object_list = view.get_queryset()
    paginate_by = view.get_paginate_by(view.object_list)
    _, page, object_list, _ = view.paginate_queryset(view.object_list, paginate_by)
    view.object_list = object_list
    view.page_obj = page

    template = Template("""
    {% load djcrud django_tables2 %}
    {% render_table view.table 'djcrud/_tables2.html' %}
    """)
    output = template.render(Context({"view": view, "request": request}))
    assert "djcrud-per-page-form" in output
    assert "djcrud-page-form" in output
    assert "up-autosubmit" in output
    assert "per-page-selector" not in output
    assert "page-input" not in output


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_pagination_controls_present(
    browser, live_server, browser_login, admin_user, many_users
):
    browser_login()
    browser.visit(f"{live_server.url}/auth/user/")

    assert browser.is_element_present_by_css("form.djcrud-per-page-form", wait_time=5)
    assert browser.is_text_present("Paginate by:", wait_time=2)
    assert browser.is_element_present_by_css("i.bi-chevron-bar-left", wait_time=2)
    assert browser.is_element_present_by_css("i.bi-chevron-left", wait_time=2)
    assert browser.is_element_present_by_css(
        'form.djcrud-page-form input[name="page"]', wait_time=2
    )
    assert browser.is_element_present_by_css("i.bi-chevron-right", wait_time=2)
    assert browser.is_element_present_by_css("i.bi-chevron-bar-right", wait_time=2)


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_paginate_by_selector(
    browser, live_server, browser_login, admin_user, many_users
):
    browser_login()
    browser.visit(f"{live_server.url}/auth/user/")

    selector = browser.find_by_css("form.djcrud-per-page-form select").first
    assert selector.value == "25"

    selector.select("10")
    assert browser.is_element_present_by_css("form.djcrud-per-page-form", wait_time=5)

    selector = browser.find_by_css("form.djcrud-per-page-form select").first
    assert selector.value == "10"
    _wait_for_url(browser, "per_page=10")


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_page_navigation_buttons(
    browser, live_server, browser_login, admin_user, many_users
):
    browser_login()
    browser.visit(f"{live_server.url}/auth/user/")

    page_input = browser.find_by_css('form.djcrud-page-form input[name="page"]').first
    assert page_input.value == "1"

    browser.find_by_css("i.bi-chevron-right").first.click()
    _wait_for_url(browser, "page=2")
    assert browser.is_element_present_by_css(
        'form.djcrud-page-form input[name="page"]', wait_time=5
    )
    page_input = browser.find_by_css('form.djcrud-page-form input[name="page"]').first
    assert page_input.value == "2"

    browser.find_by_css('a[aria-label="Previous page"]').first.click()
    _wait_for_url(browser, "page=1")
    assert browser.is_element_present_by_css(
        'form.djcrud-page-form input[name="page"]', wait_time=5
    )
    page_input = browser.find_by_css('form.djcrud-page-form input[name="page"]').first
    assert page_input.value == "1"


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_page_number_input(browser, live_server, browser_login, admin_user, many_users):
    browser_login()
    browser.visit(f"{live_server.url}/auth/user/")

    page_input = browser.find_by_css('form.djcrud-page-form input[name="page"]').first
    page_input.click()
    page_input.fill("2")
    page_input._element.send_keys(Keys.RETURN)

    _wait_for_url(browser, "page=2")
    assert browser.is_element_present_by_css(
        'form.djcrud-page-form input[name="page"]', wait_time=5
    )
    page_input = browser.find_by_css('form.djcrud-page-form input[name="page"]').first
    assert page_input.value == "2"
    table_text = browser.find_by_css("[up-table]").first.text
    assert "user25" in table_text
    assert "user0" not in table_text
