"""Capture browser screenshots for Sphinx documentation.

Run with::

    pytest tests/test_docs_screenshots.py -n0 --splinter-headless

Writes PNGs to ``docs/_static/screenshots/``.
"""

import time

import pytest
from django.urls import reverse

from djcrud_example.action_example.models import Memo
from djcrud_example.security_example.models import Document
from djcrud_example.listaction_example.models import Post
from djcrud_example.routing_example.models import Item
from djcrud_example.views_example.models import Article

from doc_screenshots import assert_all_captured, capture, prepare_browser

pytestmark = [
    pytest.mark.docs_screenshot,
    pytest.mark.splinter(screenshot_dir="./screenshots"),
    pytest.mark.django_db,
]


def _check_row(browser, index=0):
    browser.execute_script(
        """
        const boxes = document.querySelectorAll('input[type="checkbox"][data-pk]');
        const cb = boxes[arguments[0]];
        cb.checked = true;
        cb.dispatchEvent(new Event('change', {bubbles: true}));
        """,
        index,
    )


@pytest.mark.django_db
def test_capture_doc_screenshots(browser, live_server, browser_login, admin_user):
    prepare_browser(browser)
    browser_login()

    for item in ("Widget", "Gadget", "Gizmo"):
        Item.objects.create(name=item)
    for i in range(6):
        Article.objects.create(
            title=f"Article {i}",
            body="body",
            category="news" if i % 2 == 0 else "blog",
        )
    for title in ("Morning post", "Evening post", "Weekend post"):
        Post.objects.create(title=title, category="news")

    browser.visit(f"{live_server.url}{reverse('site:item:list')}")
    assert browser.is_element_present_by_css("[up-table]", wait_time=5)
    capture(browser, "item-list")

    browser.find_by_css('a[href$="/item/create/"]').first.click()
    assert browser.is_element_present_by_css('form[method="post"]', wait_time=5)
    browser.fill("name", "DocScreenshot")
    browser.find_by_css('form[method="post"] button[type="submit"]').first.click()
    assert browser.is_text_present("was added successfully", wait_time=5)
    assert browser.is_element_present_by_css(
        "[up-flashes] .djcrud-toast.is-success", wait_time=2
    )
    capture(browser, "success-toast")

    browser.visit(f"{live_server.url}{reverse('site:article:list')}?category=news")
    assert browser.is_element_present_by_css("form.djcrud-filter-form", wait_time=5)
    assert browser.is_element_present_by_css(
        "#djcrud-filter-sidebar:not(.is-hidden)",
        wait_time=5,
    )
    capture(browser, "article-list")

    article = Article.objects.get(title="Article 0")
    browser.visit(
        f"{live_server.url}{reverse('site:article:detail', args=[article.pk])}"
    )
    assert browser.is_text_present("Article 0", wait_time=5)
    capture(browser, "article-detail")

    memo = Memo.objects.create(title="Draft memo")
    browser.visit(f"{live_server.url}{reverse('site:memo:detail', args=[memo.pk])}")
    assert browser.is_text_present("Duplicate", wait_time=5)
    capture(browser, "duplicate-action-menu")

    browser.find_by_css('a[href$="/duplicate/"]').first.click()
    assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=5)
    browser.find_by_css(
        '[up-main="modal"] form[method="post"] button[type="submit"]'
    ).first.click()
    assert browser.is_text_present("was changed successfully", wait_time=5)
    time.sleep(0.3)
    capture(browser, "duplicate-action-success")

    draft = Document.objects.create(
        title="Draft document", published=False, owner=admin_user
    )
    browser.visit(
        f"{live_server.url}{reverse('site:secured-document:detail', args=[draft.pk])}"
    )
    assert browser.is_text_present("Publish", wait_time=5)
    capture(browser, "publish-action-menu")

    browser.find_by_css('a[href$="/publish/"]').first.click()
    assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=5)
    browser.find_by_css(
        '[up-main="modal"] form[method="post"] button[type="submit"]'
    ).first.click()
    assert browser.is_text_present("was changed successfully", wait_time=5)
    time.sleep(0.3)
    capture(browser, "publish-action-success")

    browser.execute_script("sessionStorage.clear()")
    browser.visit(f"{live_server.url}{reverse('site:post:list')}")
    assert browser.is_element_present_by_css("list-action-bar", wait_time=5)
    _check_row(browser, 0)
    _check_row(browser, 1)
    assert browser.is_text_present("2 selected", wait_time=5)
    time.sleep(0.3)
    capture(browser, "list-action-bar")

    browser.find_by_css('list-action-bar a[href*="setcategory"]').first.click()
    assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=5)
    time.sleep(0.3)
    capture(browser, "set-category-modal")

    browser.execute_script("sessionStorage.clear()")
    browser.visit(f"{live_server.url}{reverse('site:item:list')}")
    assert browser.is_element_present_by_css("list-action-bar", wait_time=5)
    _check_row(browser, 0)
    _check_row(browser, 1)
    assert browser.is_text_present("2 selected", wait_time=5)
    browser.find_by_css('list-action-bar a[data-list-action="urlupdate"]').first.click()
    assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=5)
    time.sleep(0.3)
    capture(browser, "bulk-delete-modal")

    assert_all_captured()


@pytest.mark.drf
@pytest.mark.django_db
def test_capture_api_swagger_screenshot(
    browser, live_server, browser_login, admin_user, drf_settings
):
    prepare_browser(browser)
    browser_login()
    browser.visit(f"{live_server.url}/api/docs/")
    assert browser.is_element_present_by_css("#swagger-ui", wait_time=15)
    # #swagger-ui container exists immediately (the JS bundle mounts it),
    # but the actual spec fetch + React render of operations happens async.
    # Wait for rendered content so we don't capture the loading spinner.
    assert browser.is_element_present_by_css(".swagger-ui .opblock", wait_time=15)
    capture(browser, "api-swagger-ui")
