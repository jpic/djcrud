import time

import pytest
from django.urls import reverse


def _wait_for_hamburger(browser, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if browser.is_element_present_by_css(
            "hamburger-menu .navbar-burger", wait_time=0
        ):
            return
        time.sleep(0.1)
    raise AssertionError("hamburger-menu .navbar-burger not found")


def _burger_is_active(browser):
    return browser.execute_script(
        'return document.querySelector("hamburger-menu .navbar-burger")'
        '?.classList.contains("is-active")',
    )


def _burger_aria_expanded(browser):
    return browser.execute_script(
        'return document.querySelector("hamburger-menu .navbar-burger")'
        '?.getAttribute("aria-expanded")',
    )


def _is_sidebar_hidden(browser):
    return browser.execute_script(
        'return document.querySelector("#sidebar").classList.contains("is-hidden")',
    )


def _click_burger(browser):
    browser.find_by_css("hamburger-menu .navbar-burger").first.click()


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_hamburger_active_when_sidebar_open_on_load(
    browser, live_server, browser_login, admin_user
):
    item_list_url = reverse("site:item:list")

    browser_login()
    browser.visit(f"{live_server.url}{item_list_url}")
    _wait_for_hamburger(browser)

    assert not _is_sidebar_hidden(browser), "sidebar should be visible on load"
    assert _burger_is_active(
        browser
    ), "burger should be is-active when sidebar is open on load"
    assert _burger_aria_expanded(browser) == "true"


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_hamburger_toggles_with_sidebar(
    browser, live_server, browser_login, admin_user
):
    item_list_url = reverse("site:item:list")

    browser_login()
    browser.visit(f"{live_server.url}{item_list_url}")
    _wait_for_hamburger(browser)

    assert _burger_is_active(browser)
    assert not _is_sidebar_hidden(browser)

    _click_burger(browser)
    assert not _burger_is_active(
        browser
    ), "burger should lose is-active when sidebar closes"
    assert _is_sidebar_hidden(browser)

    _click_burger(browser)
    assert _burger_is_active(
        browser
    ), "burger should regain is-active when sidebar reopens"
    assert not _is_sidebar_hidden(browser)
