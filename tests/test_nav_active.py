import time

import pytest
from django.urls import reverse


def _wait_for_url(browser, substring, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if substring in browser.url:
            return
        time.sleep(0.1)
    raise AssertionError(f"{substring!r} not in {browser.url!r}")


def _is_nav_active(browser, path):
    return browser.execute_script(
        'return document.querySelector(arguments[0])?.classList.contains("is-active")',
        f'#sidebar .menu-list a[href="{path}"]',
    )


def _is_sidebar_hidden(browser):
    return browser.execute_script(
        'return document.querySelector("#sidebar").classList.contains("is-hidden")',
    )


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_nav_active_moves_on_unpoly_navigation(
    browser, live_server, browser_login, admin_user
):
    item_list_url = reverse("site:item:list")
    users_url = reverse("site:auth:user:list")

    browser_login()
    browser.visit(f"{live_server.url}{item_list_url}")

    assert _is_nav_active(browser, item_list_url)
    assert not _is_nav_active(browser, users_url)

    browser.find_by_css(f'#sidebar .menu-list a[href="{users_url}"]').first.click()
    _wait_for_url(browser, users_url)

    assert _is_nav_active(browser, users_url)
    assert not _is_nav_active(browser, item_list_url)


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_nav_stays_active_on_pagination(
    browser, live_server, browser_login, admin_user, many_users
):
    users_url = reverse("site:auth:user:list")

    browser_login()
    browser.visit(f"{live_server.url}{users_url}")

    assert _is_nav_active(browser, users_url)

    browser.find_by_css("i.bi-chevron-right").first.click()
    _wait_for_url(browser, "page=2")

    assert _is_nav_active(browser, users_url)


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_sidebar_visibility_preserved_on_nav(
    browser, live_server, browser_login, admin_user
):
    item_list_url = reverse("site:item:list")
    users_url = reverse("site:auth:user:list")

    browser_login()
    browser.visit(f"{live_server.url}{item_list_url}")

    browser.execute_script('document.querySelector("hamburger-menu").toggle()')
    assert _is_sidebar_hidden(browser)

    # Sidebar links are not clickable while hidden; navigate via Unpoly directly.
    browser.execute_script("up.visit(arguments[0])", users_url)
    _wait_for_url(browser, users_url)

    assert _is_sidebar_hidden(browser)
    assert _is_nav_active(browser, users_url)
