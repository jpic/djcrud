"""Test pagination controls functionality."""
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


@pytest.fixture
def many_users(db):
    """Create many users for pagination testing."""
    users = []
    for i in range(50):
        users.append(User.objects.create_user(
            username=f'user{i}',
            email=f'user{i}@example.com',
            password='testpass123'
        ))
    return users


@pytest.mark.splinter(screenshot_dir='./screenshots')
def test_pagination_controls_present(browser, live_server, admin_user, many_users):
    """Test that pagination controls are present on the list page."""
    # Login
    browser.visit(f'{live_server.url}/auth/login/')
    browser.fill('username', 'admin')
    browser.fill('password', 'admin123')
    browser.find_by_css('button[type="submit"]').first.click()

    # Verify login succeeded
    assert browser.is_text_present('Logout', wait_time=5), "Login failed"
    print("✓ Login succeeded")

    # Navigate to user list
    browser.visit(f'{live_server.url}/auth/user/')

    # Check for rows per page selector (web component)
    assert browser.is_element_present_by_css('per-page-selector', wait_time=5), "Rows per page selector not found"
    print("✓ Rows per page selector present")

    # Check for pagination controls (should be visible since we have 50+ users)
    # First page button
    assert browser.is_element_present_by_css('i.bi-chevron-bar-left', wait_time=2), "First page button not found"
    print("✓ First page button present")

    # Previous page button
    assert browser.is_element_present_by_css('i.bi-chevron-left', wait_time=2), "Previous page button not found"
    print("✓ Previous page button present")

    # Page number input
    assert browser.is_element_present_by_css('input[type="number"]', wait_time=2), "Page number input not found"
    print("✓ Page number input present")

    # Next page button
    assert browser.is_element_present_by_css('i.bi-chevron-right', wait_time=2), "Next page button not found"
    print("✓ Next page button present")

    # Last page button
    assert browser.is_element_present_by_css('i.bi-chevron-bar-right', wait_time=2), "Last page button not found"
    print("✓ Last page button present")


@pytest.mark.splinter(screenshot_dir='./screenshots')
def test_rows_per_page_selector(browser, live_server, admin_user, many_users):
    """Test that rows per page selector changes the number of rows displayed."""
    # Login
    browser.visit(f'{live_server.url}/auth/login/')
    browser.fill('username', 'admin')
    browser.fill('password', 'admin123')
    browser.find_by_css('button[type="submit"]').first.click()

    # Verify login succeeded
    assert browser.is_text_present('Logout', wait_time=5), "Login failed"

    # Navigate to user list
    browser.visit(f'{live_server.url}/auth/user/')

    # Default should be 25 rows per page
    selector = browser.find_by_css('per-page-selector select').first
    assert selector.value == '25', f"Default should be 25, got {selector.value}"
    print("✓ Default rows per page is 25")

    # Change to 10 rows per page
    selector.select('10')

    # Wait for page to reload
    assert browser.is_element_present_by_css('per-page-selector', wait_time=5), "Page did not reload"

    # Verify selector updated
    selector = browser.find_by_css('per-page-selector select').first
    assert selector.value == '10', f"Should be 10, got {selector.value}"
    print("✓ Changed to 10 rows per page")


@pytest.mark.splinter(screenshot_dir='./screenshots')
def test_page_navigation_buttons(browser, live_server, admin_user, many_users):
    """Test that page navigation buttons work correctly."""
    # Login
    browser.visit(f'{live_server.url}/auth/login/')
    browser.fill('username', 'admin')
    browser.fill('password', 'admin123')
    browser.find_by_css('button[type="submit"]').first.click()

    # Verify login succeeded
    assert browser.is_text_present('Logout', wait_time=5), "Login failed"

    # Navigate to user list
    browser.visit(f'{live_server.url}/auth/user/')

    # Should be on page 1
    page_input = browser.find_by_css('input[type="number"]').first
    assert page_input.value == '1', f"Should start on page 1, got {page_input.value}"
    print("✓ Starting on page 1")

    # Click next page
    next_button = browser.find_by_css('i.bi-chevron-right').first
    next_button.click()

    # Wait for update
    assert browser.is_element_present_by_css('input[type="number"]', wait_time=5), "Page did not update"

    # Should be on page 2
    page_input = browser.find_by_css('input[type="number"]').first
    assert page_input.value == '2', f"Should be on page 2, got {page_input.value}"
    print("✓ Navigated to page 2")

    # Click previous page
    prev_button = browser.find_by_css('i.bi-chevron-left').first
    prev_button.click()

    # Wait for update
    assert browser.is_element_present_by_css('input[type="number"]', wait_time=5), "Page did not update"

    # Should be back on page 1
    page_input = browser.find_by_css('input[type="number"]').first
    assert page_input.value == '1', f"Should be back on page 1, got {page_input.value}"
    print("✓ Navigated back to page 1")


@pytest.mark.splinter(screenshot_dir='./screenshots')
def test_page_number_input(browser, live_server, admin_user, many_users):
    """Test that page number input allows direct navigation."""
    # Login
    browser.visit(f'{live_server.url}/auth/login/')
    browser.fill('username', 'admin')
    browser.fill('password', 'admin123')
    browser.find_by_css('button[type="submit"]').first.click()

    # Verify login succeeded
    assert browser.is_text_present('Logout', wait_time=5), "Login failed"

    # Navigate to user list
    browser.visit(f'{live_server.url}/auth/user/')

    # Should be on page 1
    page_input = browser.find_by_css('input[type="number"]').first
    assert page_input.value == '1', f"Should start on page 1, got {page_input.value}"
    print("✓ Starting on page 1")

    # Enter page 2 and submit
    page_input.fill('2')
    page_input.type('\n')  # Press Enter

    # Wait for update
    assert browser.is_element_present_by_css('input[type="number"]', wait_time=5), "Page did not update"

    # Should be on page 2
    page_input = browser.find_by_css('input[type="number"]').first
    assert page_input.value == '2', f"Should be on page 2 after input, got {page_input.value}"
    print("✓ Navigated to page 2 via input")
