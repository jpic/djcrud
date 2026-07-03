import time

import pytest
from django.urls import reverse

from djcrud.views.delete import DeleteObjectsView
from djcrud_example.routing_example.models import Item

DELETE_OBJECTS_MESSAGE = "Are you sure you want to delete the selected"


def _wait_for_url(browser, substring, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if substring in browser.url:
            return
        time.sleep(0.1)
    raise AssertionError(f"{substring!r} not in {browser.url!r}")


@pytest.mark.django_db
def test_list_actions_on_auth_user_list(client, admin_user):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    User.objects.create_user("listed", email="l@e.c", password="x")
    client.force_login(admin_user)
    response = client.get("/auth/user/")
    assert response.status_code == 200
    assert b"data-pk=" in response.content
    assert b"list-action-bar" in response.content


@pytest.mark.django_db
def test_list_actions_on_routing_list(client, admin_user):
    Item.objects.create(name="A")
    client.force_login(admin_user)
    response = client.get(reverse("site:item:list"))
    assert response.status_code == 200
    assert b"list-action-bar" in response.content
    assert b'data-role="count"' in response.content
    assert b"Clear selection" in response.content
    assert b"data-pk=" in response.content


@pytest.mark.django_db
def test_delete_objects_loads_pks(rf, admin_user):
    a = Item.objects.create(name="A")
    b = Item.objects.create(name="B")
    item_router = __import__("djcrud").site.routes["item"]
    route = item_router.routes["deleteobjects"]
    request = rf.get(f"/item/deleteobjects/?pks={a.pk}&pks={b.pk}")
    request.user = admin_user
    view = type(route)(request=request)
    assert list(view.object_list.values_list("pk", flat=True)) == [a.pk, b.pk]
    assert view.invalid_pks == 0


@pytest.mark.django_db
def test_invalid_pks_for_unauthorized_objects(rf, admin_user):
    obj = Item.objects.create(name="A")
    item_router = __import__("djcrud").site.routes["item"]
    route = item_router.routes["deleteobjects"]
    request = rf.get(f"/item/deleteobjects/?pks={obj.pk}&pks=99999")
    request.user = admin_user
    view = type(route)(request=request)
    assert view.object_list.count() == 1
    assert view.invalid_pks == 1


@pytest.mark.django_db
def test_delete_objects_view(client, admin_user):
    a = Item.objects.create(name="A")
    b = Item.objects.create(name="B")
    client.force_login(admin_user)

    url = reverse("site:item:deleteobjects") + f"?pks={a.pk}&pks={b.pk}"
    assert client.get(url).status_code == 200
    client.post(url, {"next": reverse("site:item:list")})
    assert Item.objects.count() == 0


@pytest.mark.django_db
def test_delete_objects_lists_clickable_objects(client, admin_user):
    a = Item.objects.create(name="Alice")
    b = Item.objects.create(name="Bob")
    client.force_login(admin_user)

    url = reverse("site:item:deleteobjects") + f"?pks={a.pk}&pks={b.pk}"
    response = client.get(url)
    content = response.content.decode()

    assert "Summary" in content
    assert "Items: 2" in content
    assert "djcrud-deletion-objects" in content
    assert "Alice" in content
    assert "Bob" in content
    assert reverse("site:item:detail", args=[a.pk]) in content
    assert reverse("site:item:detail", args=[b.pk]) in content
    assert 'name="pks"' in content


@pytest.mark.django_db
def test_unpoly_attributes_list_action_bar(rf, admin_user):
    item_router = __import__("djcrud").site.routes["item"]
    route = item_router.routes["deleteobjects"]
    request = rf.get("/item/deleteobjects/")
    request.user = admin_user
    view = type(route)(request=request)
    attrs = view.unpoly_attributes("list_action_bar")
    assert attrs["data-list-action"] == "urlupdate"
    assert attrs["up-layer"] == "new modal"
    assert attrs["up-history"] is False
    assert attrs["up-on-accepted"] == (
        "djcrudClearListActionSelections(); up.visit(response.url)"
    )


@pytest.mark.django_db
def test_checkbox_column_respects_object_permission(rf, admin_user):
    from djcrud.views.tables2 import CheckboxColumn

    class DenyObjectDelete(DeleteObjectsView):
        def has_permission(self):
            obj = getattr(self, "object", None)
            if obj is not None and obj.name == "denied":
                return False
            return super().has_permission()

    allowed = Item.objects.create(name="allowed")
    denied = Item.objects.create(name="denied")
    item_router = __import__("djcrud").site.routes["item"]
    original_route = item_router.routes["deleteobjects"]
    item_router.routes["deleteobjects"] = DenyObjectDelete
    try:
        list_route = item_router.routes["list"]
        request = rf.get("/item/")
        request.user = admin_user
        view = type(list_route)(request=request)
        view.object_list = Item.objects.all()
        column = CheckboxColumn()
        table = view.table
        assert "data-pk=" in column.render(allowed, table)
        assert "data-pk=" not in column.render(denied, table)
    finally:
        item_router.routes["deleteobjects"] = original_route


@pytest.mark.django_db
def test_delete_view_omits_cascade_message_without_relations(client, admin_user):
    stage = Item.objects.create(name="Lonely")
    client.force_login(admin_user)

    response = client.get(reverse("site:item:delete", args=[stage.pk]))
    content = response.content.decode()

    assert "Are you sure you want to delete the" in content
    assert "Lonely" in content


def _visit_user_list(browser, live_server):
    browser.execute_script("sessionStorage.clear()")
    browser.visit(f"{live_server.url}/auth/user/")
    assert browser.is_element_present_by_css("list-action-bar", wait_time=5)


def _visit_item_list(browser, live_server):
    browser.execute_script("sessionStorage.clear()")
    browser.visit(f"{live_server.url}/item/")
    assert browser.is_element_present_by_css("list-action-bar", wait_time=5)
    assert browser.is_element_present_by_css(
        'input[type="checkbox"][data-pk]', wait_time=5
    )


def _row_checkbox_count(browser):
    return browser.execute_script(
        "return document.querySelectorAll("
        '".djcrud-list input[type=\\"checkbox\\"][data-pk]"'
        ").length;",
    )


def _wait_for_at_least_row_checkboxes(browser, minimum, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        count = _row_checkbox_count(browser)
        if count >= minimum:
            return count
        time.sleep(0.1)
    raise AssertionError(
        f"Expected at least {minimum} row checkboxes in .djcrud-list, got {count}",
    )


def _wait_for_row_checkboxes(browser, expected, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        count = _row_checkbox_count(browser)
        if count == expected:
            return count
        time.sleep(0.1)
    raise AssertionError(
        f"Expected {expected} row checkboxes in .djcrud-list, got {count}",
    )


def _selection_count_text(browser):
    return browser.execute_script(
        """
        const el = document.querySelector('list-action-bar [data-role="count"]');
        return el ? el.textContent.trim() : '';
        """,
    )


def _wait_for_selection_count(browser, count, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        text = _selection_count_text(browser)
        if text and str(count) in text and "selected" in text:
            return text
        time.sleep(0.1)
    raise AssertionError(
        f"Selection count did not reach {count!r}, last label: {text!r}",
    )


def _check_row(browser, index=0):
    browser.execute_script(
        """
        const boxes = document.querySelectorAll(
            '.djcrud-list input[type="checkbox"][data-pk]',
        );
        const cb = boxes[arguments[0]];
        if (!cb) {
            throw new Error(`No checkbox at index ${arguments[0]}`);
        }
        cb.checked = true;
        cb.dispatchEvent(new Event('change', {bubbles: true}));
        """,
        index,
    )


def _select_rows(browser, indices):
    _wait_for_at_least_row_checkboxes(browser, max(indices) + 1)
    for index in indices:
        _check_row(browser, index)
    _wait_for_selection_count(browser, len(indices))


def _assert_bar_shows_count(browser, count):
    text = _wait_for_selection_count(browser, count)
    if count == 1:
        assert text == "1 selected"
    else:
        assert text == f"All {count} selected"


def _assert_bar_hidden(browser, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if browser.is_text_present("selected", wait_time=0):
            time.sleep(0.1)
            continue
        state = browser.execute_script(
            """
            const bar = document.querySelector('list-action-bar');
            const storageKeys = Object.keys(sessionStorage).filter(
                (key) => key.startsWith('djcrud:list-action:'),
            );
            return {
                hidden: bar?.hidden ?? true,
                storageKeys,
            };
            """,
        )
        if state["hidden"] and state["storageKeys"] == []:
            return
        time.sleep(0.1)
    raise AssertionError("List action bar still shows a selection")


def _open_bulk_delete_modal(browser):
    browser.find_by_css('list-action-bar a[data-list-action="urlupdate"]').first.click()
    assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=5)


def _assert_delete_modal(browser, count, names):
    assert browser.is_text_present(DELETE_OBJECTS_MESSAGE, wait_time=5)
    assert browser.is_text_present(f"Items: {count}", wait_time=2)
    for name in names:
        assert browser.is_text_present(name, wait_time=2)


def _submit_delete_modal(browser):
    browser.find_by_css('[up-main="modal"] button[type="submit"]').first.click()


def _wait_modal_closed(browser, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not browser.is_element_present_by_css('[up-main="modal"]', wait_time=0):
            return
        time.sleep(0.1)
    raise AssertionError("Delete modal did not close")


def _wait_delete_accepted(browser, *, expected_rows=None, timeout=15):
    """Wait for modal close and list-action-bar state to clear after bulk delete."""
    _wait_modal_closed(browser, timeout)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = browser.execute_script(
            """
            return {
                barHidden: document.querySelector('list-action-bar')?.hidden ?? true,
                keys: Object.keys(sessionStorage).filter(
                    (key) => key.startsWith('djcrud:list-action:'),
                ),
                rows: document.querySelectorAll(
                    '.djcrud-list input[type="checkbox"][data-pk]',
                ).length,
            };
            """,
        )
        rows_ok = expected_rows is None or state["rows"] == expected_rows
        if state["barHidden"] and state["keys"] == [] and rows_ok:
            return
        time.sleep(0.1)
    raise AssertionError(
        "Bulk delete did not finish updating list-action-bar state: " f"{state!r}",
    )


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_list_checkboxes_on_user_list(
    browser, live_server, browser_login, admin_user, many_users
):
    browser_login()
    _visit_user_list(browser, live_server)

    assert browser.is_element_present_by_css(
        'input[type="checkbox"][data-pk]', wait_time=5
    )
    assert browser.is_element_present_by_css(
        'input[type="checkbox"][data-master]', wait_time=2
    )


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_list_action_bar_shows_selection_count(
    browser, live_server, browser_login, admin_user, many_users
):
    browser_login()
    _visit_user_list(browser, live_server)

    _check_row(browser)
    assert browser.is_text_present("1 selected", wait_time=5)


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_list_selection_persists_across_pages(
    browser, live_server, browser_login, admin_user, many_users
):
    browser_login()
    _visit_user_list(browser, live_server)

    _check_row(browser)
    assert browser.is_text_present("1 selected", wait_time=5)

    browser.find_by_css('a[aria-label="Next page"]').first.click()
    _wait_for_url(browser, "page=2")
    assert browser.is_element_present_by_css(
        'form.djcrud-page-form input[name="page"]', wait_time=5
    )
    assert browser.is_element_present_by_css(
        'input[type="checkbox"][data-pk]', wait_time=5
    )

    _check_row(browser)
    _assert_bar_shows_count(browser, 2)

    browser.find_by_css('[data-role="clear"]').first.click()
    assert browser.is_text_not_present("selected", wait_time=5)


@pytest.mark.splinter(screenshot_dir="./screenshots")
@pytest.mark.django_db
def test_bulk_delete_twice_clears_selection(
    browser,
    live_server,
    browser_login,
    admin_user,
    routing_bulk_items,
):
    browser_login()
    _visit_item_list(browser, live_server)

    _select_rows(browser, [0, 1])
    _assert_bar_shows_count(browser, 2)
    _open_bulk_delete_modal(browser)
    _assert_delete_modal(browser, 2, ["item-0", "item-1"])
    _submit_delete_modal(browser)
    _wait_delete_accepted(browser, expected_rows=2)
    _assert_bar_hidden(browser)
    assert browser.is_text_not_present("item-0", wait_time=5)
    assert browser.is_text_not_present("item-1", wait_time=2)
    assert browser.is_text_present("item-2", wait_time=2)
    assert browser.is_text_present("item-3", wait_time=2)

    _select_rows(browser, [0, 1])
    _assert_bar_shows_count(browser, 2)
    _open_bulk_delete_modal(browser)
    _assert_delete_modal(browser, 2, ["item-2", "item-3"])
    _submit_delete_modal(browser)
    _wait_delete_accepted(browser, expected_rows=0)
    _assert_bar_hidden(browser)
    _wait_for_row_checkboxes(browser, 0)
    assert not browser.is_element_present_by_css(
        '.djcrud-list input[type="checkbox"][data-pk]',
        wait_time=5,
    )
    assert Item.objects.count() == 0
