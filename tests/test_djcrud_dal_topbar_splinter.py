import time

import pytest
from django.contrib.auth import get_user_model

from alight_helpers import (
    ensure_navbar_menu_visible,
    type_and_select,
    type_autocomplete_query,
    wait_alight_ready,
    wait_input_interactable,
)
from doc_screenshots import capture as capture_doc
from topbar_screenshots import capture, prepare_browser

User = get_user_model()


def _wait_for_url_contains(browser, substring, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if substring in browser.url:
            return
        time.sleep(0.1)
    raise AssertionError(f"{substring!r} not in {browser.url!r}")


@pytest.fixture
def grouped_users(db):
    member = User.objects.create_user("member", password="pass")
    outsider = User.objects.create_user("outsider", password="pass")
    return member, outsider


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_site_search_navigates_to_user_detail(
    browser,
    live_server,
    browser_login,
    admin_user,
    grouped_users,
):
    member, _ = grouped_users
    browser_login()
    prepare_browser(browser)
    browser.visit(f"{live_server.url}/auth/user/")

    wait_alight_ready(browser)
    assert browser.is_element_present_by_css(".djcrud-site-search", wait_time=5)
    ensure_navbar_menu_visible(browser)
    wait_input_interactable(browser, ".djcrud-site-search input")

    capture(browser, "site-search-initial")

    type_autocomplete_query(browser, "member", input_css=".djcrud-site-search input")
    assert browser.is_element_present_by_css(
        ".autocomplete-light-box [data-value]",
        wait_time=5,
    )
    capture(browser, "site-search-results")
    capture_doc(browser, "site-search")

    type_and_select(
        browser,
        "member",
        container_css=".djcrud-site-search",
        input_css=".djcrud-site-search input",
    )

    detail_path = f"/auth/user/{member.pk}/detail/"
    _wait_for_url_contains(browser, detail_path)
    assert browser.is_element_present_by_css("[up-main]", wait_time=5)
    assert browser.is_text_present("member", wait_time=5)
    capture(browser, "site-search-detail")
