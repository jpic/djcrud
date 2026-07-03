import pytest
from django.urls import reverse


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_create_modal_focuses_first_input(
    browser, live_server, browser_login, admin_user
):
    browser_login()
    list_path = reverse("site:item:list")
    browser.visit(f"{live_server.url}{list_path}")

    assert browser.is_element_present_by_css('a[href$="/item/create/"]', wait_time=5)
    browser.find_by_css('a[href$="/item/create/"]').first.click()

    assert browser.is_element_present_by_css(
        '[up-main="modal"] form[method="post"]', wait_time=5
    )

    active_name = browser.execute_script(
        "const modal = document.querySelector('[up-main=\"modal\"]');"
        "const active = document.activeElement;"
        "return active && modal.contains(active) ? active.name : null;",
    )
    assert active_name == "name"


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_create_modal_does_not_change_history(
    browser,
    live_server,
    browser_login,
    admin_user,
):
    browser_login()
    list_path = reverse("site:item:list")
    browser.visit(f"{live_server.url}{list_path}")

    browser.find_by_css('a[href$="/item/create/"]').first.click()
    assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=5)

    pathname = browser.execute_script("return window.location.pathname")
    assert pathname == list_path


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_filter_sidebar_focuses_search_input(
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

    active_name = browser.execute_script(
        'const sidebar = document.querySelector("#djcrud-filter-sidebar");'
        "const active = document.activeElement;"
        "return active && sidebar.contains(active) ? active.name : null;",
    )
    assert active_name == "search"
