"""
Browser tests for Unpoly modal behavior.

Tests actual browser interaction with modals to verify they open and close correctly.
"""

import pytest
import time


@pytest.mark.django_db
def test_create_modal_closes_on_success(browser, live_server, superuser):
    """Test that create modal opens and closes after successful form submission."""
    # Navigate to user list page
    browser.visit(f'{live_server.url}/auth/user/')

    # Wait for page to load
    assert browser.is_element_present_by_tag('table', wait_time=10), "Table should be present"

    # Find and click the create button (link with up-layer="new modal")
    create_links = browser.find_by_css('a[up-layer="new modal"]')
    create_link = None
    for link in create_links:
        if 'create' in link['href']:
            create_link = link
            break

    assert create_link is not None, "Create button should be found"

    print(f"Create link HTML: {create_link.outer_html}")
    print(f"Create link href: {create_link['href']}")

    # Click the create button
    create_link.click()

    # Wait a bit for modal to appear
    time.sleep(2)

    # Check if modal appeared by looking for form in modal
    # Unpoly should add up-layer or similar attributes to the modal
    print(f"Current URL after click: {browser.url}")
    print(f"Page HTML (first 500 chars): {browser.html[:500]}")

    # Look for the username field (should be in modal)
    assert browser.is_element_present_by_name('username', wait_time=10), "Username field should be present in modal"

    # Fill in the form
    browser.fill('username', 'testuser123')
    browser.fill('password1', 'testpassword123!')
    browser.fill('password2', 'testpassword123!')

    print(f"Form filled, about to submit")

    # Submit the form
    submit_buttons = browser.find_by_css('button[type="submit"]')
    assert len(submit_buttons) > 0, "Submit button should exist"
    submit_buttons.first.click()

    # Wait for response
    time.sleep(3)

    print(f"After submit - URL: {browser.url}")
    print(f"After submit - HTML (first 500 chars): {browser.html[:500]}")

    # Check if we're back on the list page (modal should be closed)
    # URL should not contain 'create'
    assert 'create' not in browser.url, "Should navigate away from create URL"

    # Verify the new user appears in the table
    assert browser.is_text_present('testuser123', wait_time=10), "New user should appear in the table"
