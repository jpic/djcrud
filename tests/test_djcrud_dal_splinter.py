import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from alight_helpers import type_and_select, wait_alight_ready
from dal_screenshots import capture, prepare_browser
from test_filter import _open_filter_sidebar

User = get_user_model()


@pytest.fixture
def editors_group(db):
    return Group.objects.create(name="editors")


@pytest.fixture
def reviewers_group(db):
    return Group.objects.create(name="reviewers")


@pytest.fixture
def grouped_users(db, editors_group):
    member = User.objects.create_user("member", password="pass")
    member.groups.add(editors_group)
    outsider = User.objects.create_user("outsider", password="pass")
    return member, outsider


def _assert_filter_form_layout(browser):
    """Filter sidebar: vertical crispy fields with search + FK autocomplete."""
    form = browser.find_by_css("form.djcrud-filter-form").first
    assert form["method"] == "get"
    assert browser.is_element_present_by_css(
        "#djcrud-filter-sidebar form.djcrud-filter-form",
        wait_time=2,
    )
    assert browser.is_element_present_by_css(
        'form.djcrud-filter-form input[name="search"]',
        wait_time=2,
    )
    assert browser.is_element_present_by_css(
        "form.djcrud-filter-form autocomplete-select",
        wait_time=2,
    )
    assert browser.is_element_present_by_css(
        "form.djcrud-filter-form label",
        wait_time=2,
    )
    assert not browser.is_element_present_by_css(
        "form.djcrud-filter-form .field.is-grouped",
        wait_time=0,
    )


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_user_update_groups_autocomplete(
    browser,
    live_server,
    browser_login,
    admin_user,
    editors_group,
    reviewers_group,
    grouped_users,
):
    member, _ = grouped_users
    browser_login()
    browser.visit(f"{live_server.url}/auth/user/{member.pk}/update/")

    wait_alight_ready(browser)
    groups_css = "#div_id_groups autocomplete-select"
    assert browser.is_element_present_by_css(groups_css, wait_time=5)

    prepare_browser(browser)
    capture(browser, "user-update-groups-initial")

    type_and_select(
        browser,
        "reviewers",
        container_css=groups_css,
        input_css="#div_id_groups autocomplete-select-input input",
    )
    capture(browser, "user-update-groups-selected")
    browser.find_by_css('button[type="submit"]').first.click()

    assert browser.is_text_present("member", wait_time=5)
    member.refresh_from_db()
    assert member.groups.filter(name="reviewers").exists()
    assert member.groups.filter(name="editors").exists()


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_user_list_filter_groups_autocomplete(
    browser,
    live_server,
    browser_login,
    admin_user,
    editors_group,
    grouped_users,
):
    member, outsider = grouped_users
    browser_login()
    browser.execute_script("sessionStorage.clear()")
    browser.visit(f"{live_server.url}/auth/user/")

    assert browser.is_element_present_by_css("filter-sidebar-toggle", wait_time=5)
    _open_filter_sidebar(browser)

    filter_groups_css = "form.djcrud-filter-form autocomplete-select"
    assert browser.is_element_present_by_css(filter_groups_css, wait_time=5)
    wait_alight_ready(browser)
    _assert_filter_form_layout(browser)

    prepare_browser(browser)
    capture(browser, "user-list-filter-groups-initial")

    type_and_select(
        browser,
        "editors",
        container_css=filter_groups_css,
        input_css="form.djcrud-filter-form autocomplete-select-input input",
    )
    capture(browser, "user-list-filter-groups-selected")
    browser.find_by_css('form.djcrud-filter-form button[type="submit"]').first.click()

    assert browser.is_element_present_by_css("[up-list]", wait_time=5)
    assert f"groups={editors_group.pk}" in browser.url
    table_text = browser.find_by_css("[up-table]").first.text
    assert member.username in table_text
    assert outsider.username not in table_text
    capture(browser, "user-list-filter-groups-filtered")
