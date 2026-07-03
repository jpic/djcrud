"""Browser tests for cross-shell navigation between standard and SPA layouts."""

import time

import pytest
from django.urls import reverse


def _wait_for_url(browser, substring, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if substring in browser.url:
            return
        time.sleep(0.1)
    raise AssertionError(f"{substring!r} not in {browser.url!r}")


def _is_standard_shell(browser):
    return browser.execute_script("""
        return document.querySelector('body > nav.navbar') !== null
            && !document.body.classList.contains('djcrud-spa-body');
        """)


def _is_spa_shell(browser):
    return browser.execute_script("""
        return document.body.classList.contains('djcrud-spa-body')
            && document.querySelector('body > nav.navbar') === null;
        """)


def _wait_for_spa_ready(browser, timeout=15):
    """Wait for the Svelte bundle to mount with the burger toolbar."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if browser.is_text_present(
            "SPA demo", wait_time=0
        ) and browser.is_element_present_by_css(
            "#app hamburger-menu .navbar-burger",
            wait_time=0,
        ):
            return
        time.sleep(0.1)
    raise AssertionError("SPA app and burger toolbar did not render")


def _open_spa_sidebar(browser):
    sidebar = browser.find_by_css("#sidebar").first
    if "is-hidden" in (sidebar["class"] or ""):
        browser.find_by_css("#app hamburger-menu .navbar-burger").first.click()
    assert browser.is_element_present_by_css(
        "#sidebar .menu-list a",
        wait_time=5,
    )


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_normal_to_spa_full_page_navigation(
    browser, live_server, browser_login, admin_user
):
    """Standard sidebar link to a *base_spa.html view reloads the full document."""
    item_list_url = reverse("site:item:list")
    spa_url = reverse("site:spa")

    browser_login()
    browser.visit(f"{live_server.url}{item_list_url}")

    assert _is_standard_shell(browser)
    assert browser.is_element_present_by_css("#sidebar .menu-list", wait_time=5)

    browser.find_by_css(f'#sidebar .menu-list a[href="{spa_url}"]').first.click()
    _wait_for_url(browser, spa_url)

    assert _is_spa_shell(browser)
    _wait_for_spa_ready(browser)


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_spa_burger_reveals_server_sidebar(
    browser, live_server, browser_login, admin_user
):
    browser_login()
    browser.visit(f"{live_server.url}{reverse('site:spa')}")

    _wait_for_spa_ready(browser)
    assert "is-hidden" in browser.find_by_css("#sidebar").first["class"]

    _open_spa_sidebar(browser)
    assert "is-hidden" not in browser.find_by_css("#sidebar").first["class"]


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_spa_to_normal_full_page_navigation(
    browser, live_server, browser_login, admin_user
):
    """SPA menu link back to a standard CRUD view reloads navbar and server sidebar."""
    item_list_url = reverse("site:item:list")
    spa_url = reverse("site:spa")

    browser_login()
    browser.visit(f"{live_server.url}{spa_url}")

    assert _is_spa_shell(browser)
    _wait_for_spa_ready(browser)
    _open_spa_sidebar(browser)

    browser.find_by_css(f'#sidebar .menu-list a[href="{item_list_url}"]').first.click()
    _wait_for_url(browser, item_list_url)

    assert _is_standard_shell(browser)
    assert browser.is_element_present_by_css("#sidebar .menu-list", wait_time=5)
    assert browser.is_element_present_by_css("nav.navbar", wait_time=2)
    assert browser.is_element_present_by_css("[up-table]", wait_time=5)
