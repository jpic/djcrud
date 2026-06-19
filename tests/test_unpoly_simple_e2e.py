"""Simple E2E test to verify modal behavior with Unpoly."""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def admin_user(db):
    """Create an admin user for testing."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )


@pytest.mark.splinter(screenshot_dir='./screenshots')
def test_user_list_page_loads(browser, live_server, admin_user):
    """Test that we can load the user list page."""
    # Login
    browser.visit(f'{live_server.url}/auth/login/')
    browser.fill('username', 'admin')
    browser.fill('password', 'admin123')
    browser.find_by_css('button[type="submit"]').first.click()

    # Verify login succeeded by waiting for Logout link to appear
    assert browser.is_text_present('Logout', wait_time=5), "Login failed - should see Logout link"
    print(f"✓ Login succeeded")

    # Navigate to user list
    browser.visit(f'{live_server.url}/auth/user/')

    # Should see admin user in the list
    assert browser.is_text_present('admin')
    print(f"✓ User list loaded successfully")


@pytest.mark.splinter(screenshot_dir='./screenshots')
def test_create_modal_opens(browser, live_server, admin_user):
    """Test that clicking create button opens a modal."""
    # Login
    browser.visit(f'{live_server.url}/auth/login/')
    browser.fill('username', 'admin')
    browser.fill('password', 'admin123')
    browser.find_by_css('button[type="submit"]').first.click()

    # Verify login succeeded by waiting for Logout link
    assert browser.is_text_present('Logout', wait_time=5), "Login failed - user not authenticated"
    print(f"✓ Login succeeded")

    # Navigate to user list
    browser.visit(f'{live_server.url}/auth/user/')
    print(f"Current URL: {browser.url}")

    # Look for create button - try different selectors
    create_buttons = browser.find_by_text('Create')
    if not create_buttons:
        create_buttons = browser.find_by_css('a[href*="create"]')

    if create_buttons:
        print(f"✓ Found {len(create_buttons)} create button(s)")
        create_buttons.first.click()

        # Wait for modal to appear by checking for modal element
        assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=5), "Modal did not open"
        print(f"✓ Modal opened successfully")
    else:
        print(f"✗ Create button not found")
        print(f"Available links: {[a.text for a in browser.find_by_tag('a')[:10]]}")
        assert False, "Create button not found"


@pytest.mark.splinter(screenshot_dir='./screenshots')
def test_form_validation_error_stays_in_modal(browser, live_server, admin_user):
    """
    Critical test: Form validation errors should keep the modal open,
    not render the full page layout.
    """
    # Login
    browser.visit(f'{live_server.url}/auth/login/')
    browser.fill('username', 'admin')
    browser.fill('password', 'admin123')
    browser.find_by_css('button[type="submit"]').first.click()

    # Verify login succeeded by waiting for Logout link
    assert browser.is_text_present('Logout', wait_time=5), "Login failed - should see Logout link"

    # Navigate to user list
    browser.visit(f'{live_server.url}/auth/user/')
    initial_url = browser.url
    print(f"Initial URL: {initial_url}")

    # Click create
    create_buttons = browser.find_by_text('Create')
    if not create_buttons:
        create_buttons = browser.find_by_css('a[href*="create"]')

    create_buttons.first.click()

    # Wait for modal to open
    assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=5), "Modal should be open"
    print("✓ Modal opened")

    # Submit form WITHOUT filling required fields (should cause validation error)
    submit_btn = browser.find_by_css('[up-main="modal"] button[type="submit"]').first
    submit_btn.click()

    # Wait for form to re-render with errors (modal should still be present)
    # CRITICAL CHECK 1: Modal should STILL be open
    modal_still_there = browser.is_element_present_by_css('[up-main="modal"]', wait_time=5)
    print(f"Modal still present after validation error: {modal_still_there}")

    # CRITICAL CHECK 2: Should NOT see full page layout inside modal
    # Check if sidebar is visible (it shouldn't be in modal)
    sidebar_in_modal = False
    if modal_still_there:
        modal_element = browser.find_by_css('[up-main="modal"]').first
        # Try to find sidebar class within modal
        modal_html = modal_element.html
        sidebar_in_modal = 'sidebar' in modal_html and '<nav' in modal_html

    print(f"Sidebar rendered in modal: {sidebar_in_modal}")
    print(f"Current URL: {browser.url}")

    # Assertions
    assert modal_still_there, "❌ FAIL: Modal closed on validation error (should stay open)"
    assert not sidebar_in_modal, "❌ FAIL: Full page layout rendered in modal"

    print("✓ PASS: Validation error keeps modal open without full layout")


@pytest.mark.splinter(screenshot_dir='./screenshots')
def test_validation_error_does_not_update_main_page(browser, live_server, admin_user):
    """
    Critical test: Form validation errors should stay in modal AND
    should NOT update the main page content behind the modal.
    """
    # Login
    browser.visit(f'{live_server.url}/auth/login/')
    browser.fill('username', 'admin')
    browser.fill('password', 'admin123')
    browser.find_by_css('button[type="submit"]').first.click()

    # Verify login succeeded
    assert browser.is_text_present('Logout', wait_time=5), "Login failed"

    # Navigate to user list
    browser.visit(f'{live_server.url}/auth/user/')

    # Capture initial main page state - should show "Users" heading
    assert browser.is_text_present('Users'), "Should see Users heading on list page"
    main_page_has_table = browser.is_element_present_by_css('table')
    print(f"Main page has table: {main_page_has_table}")

    # Click create to open modal
    create_buttons = browser.find_by_text('Create')
    if not create_buttons:
        create_buttons = browser.find_by_css('a[href*="create"]')
    create_buttons.first.click()

    # Wait for modal to open
    assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=5), "Modal should open"
    print("✓ Modal opened")

    # Submit form with validation error (missing required fields)
    submit_btn = browser.find_by_css('[up-main="modal"] button[type="submit"]').first
    submit_btn.click()

    # Wait for response
    assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=5), "Modal should stay open"

    # CRITICAL CHECK: Main page content should NOT have changed
    # The root layer's [up-main] should still show the table, NOT the form
    root_main_has_form = browser.is_element_present_by_css('main[up-main]:not([up-main="modal"]) form')
    root_main_has_table = browser.is_element_present_by_css('main[up-main]:not([up-main="modal"]) table')

    print(f"Root main has form: {root_main_has_form}")
    print(f"Root main has table: {root_main_has_table}")
    print(f"URL after validation error: {browser.url}")

    # The root main should still have the table (list page), not the form
    assert root_main_has_table, "❌ FAIL: Main page content changed - table disappeared"
    assert not root_main_has_form, "❌ FAIL: Form rendered in main page instead of modal"

    print("✓ PASS: Validation error stayed in modal, main page unchanged")


@pytest.mark.splinter(screenshot_dir='./screenshots')
def test_successful_form_redirects_to_list_not_home(browser, live_server, admin_user):
    """
    Critical test: After successful form submission, should redirect to
    the list page that opened the modal, NOT to home page.
    """
    # Login
    browser.visit(f'{live_server.url}/auth/login/')
    browser.fill('username', 'admin')
    browser.fill('password', 'admin123')
    browser.find_by_css('button[type="submit"]').first.click()

    # Verify login succeeded by waiting for Logout link
    assert browser.is_text_present('Logout', wait_time=5), "Login failed - should see Logout link"

    # Navigate to user list
    browser.visit(f'{live_server.url}/auth/user/')
    list_url = browser.url
    print(f"List URL: {list_url}")

    # Click create
    create_buttons = browser.find_by_text('Create')
    if not create_buttons:
        create_buttons = browser.find_by_css('a[href*="create"]')

    create_buttons.first.click()

    # Wait for modal to open
    assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=5), "Modal should open"

    # Fill form with valid data (Django UserCreationForm uses password1/password2)
    browser.fill('username', 'newuser123')
    browser.fill('password1', 'testpass123')
    browser.fill('password2', 'testpass123')

    # Submit
    browser.find_by_css('[up-main="modal"] button[type="submit"]').first.click()

    # Wait for modal to close by checking that it's no longer present
    # Use a custom wait to check modal is gone
    modal_closed = browser.is_element_not_present_by_css('[up-main="modal"]', wait_time=5)
    print(f"Modal closed: {modal_closed}")

    # Wait for new user to appear in list
    new_user_visible = browser.is_text_present('newuser123', wait_time=5)
    print(f"New user visible in list: {new_user_visible}")

    # CRITICAL CHECK: Should be back on list page, NOT home page
    final_url = browser.url
    print(f"Final URL after submit: {final_url}")
    print(f"Expected URL (list): {list_url}")

    # Assertions
    assert modal_closed, "❌ FAIL: Modal did not close after successful submit"
    assert final_url == list_url, f"❌ FAIL: Redirected to {final_url} instead of list page {list_url}"
    assert new_user_visible, "❌ FAIL: New user not visible in list"

    print("✓ PASS: Successfully redirected to list page after form submit")
