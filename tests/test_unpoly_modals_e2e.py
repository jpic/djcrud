"""End-to-end tests for Unpoly modal CRUD operations using pytest-splinter."""
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
def test_users(db):
    """Create test users."""
    users = []
    for i in range(3):
        user = User.objects.create_user(
            username=f'user{i}',
            email=f'user{i}@example.com',
            password='test123'
        )
        users.append(user)
    return users


@pytest.mark.splinter
class TestUnpolyModalCRUD:
    """Test CRUD operations with Unpoly modals."""

    def test_create_user_modal_opens_and_closes_on_success(self, browser, admin_user, live_server):
        """
        Test that:
        1. Create button opens modal
        2. Form submission with valid data closes modal
        3. User is redirected back to list page
        4. New user appears in the list
        """
        # Login as admin
        browser.visit(f'{live_server.url}/auth/login/')
        browser.fill('username', 'admin')
        browser.fill('password', 'admin123')
        browser.find_by_css('button[type="submit"]').first.click()

        # Verify login was successful by checking for Logout link in sidebar
        assert browser.is_text_present('Logout'), "Login should have succeeded - Logout link should be visible"
        assert not browser.is_text_present('Login'), "After login, Login link should not be visible"

        # Navigate to user list
        browser.visit(f'{live_server.url}/auth/user/')
        initial_url = browser.url

        # Verify we're still logged in after navigation
        assert browser.is_text_present('Logout'), "Should still be logged in after navigation"

        # Click create button - should open modal
        create_button = browser.find_by_css('a[href*="/auth/user/create"]').first
        create_button.click()

        # Wait for modal to appear
        assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=2)

        # Fill form with valid data (UserCreationForm uses password1 and password2)
        browser.fill('username', 'newuser')
        browser.fill('password1', 'newpass123')
        browser.fill('password2', 'newpass123')

        # Submit form
        browser.find_by_css('[up-main="modal"] button[type="submit"]').first.click()

        # Wait for modal to close (up-main="modal" should disappear)
        # and we should be back on the list page
        assert browser.is_element_not_present_by_css('[up-main="modal"]', wait_time=2)
        assert browser.url == initial_url, f"Expected {initial_url}, got {browser.url}"

        # Verify new user appears in the list
        assert browser.is_text_present('newuser')

    def test_create_user_modal_stays_open_on_validation_error(self, browser, admin_user, live_server):
        """
        Test that:
        1. Create button opens modal
        2. Form submission with invalid data keeps modal open
        3. Validation errors are displayed in modal
        4. Modal content doesn't render full page layout
        """
        # Login
        browser.visit(f'{live_server.url}/auth/login/')
        browser.fill('username', 'admin')
        browser.fill('password', 'admin123')
        browser.find_by_css('button[type="submit"]').first.click()

        # Verify login was successful
        assert browser.is_text_present('Logout'), "Login should have succeeded"

        # Navigate to user list
        browser.visit(f'{live_server.url}/auth/user/')

        # Click create button
        browser.find_by_css('a[href*="/auth/user/create"]').first.click()

        # Wait for modal
        assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=2)

        # Fill form with MISMATCHED passwords to trigger Django validation error
        browser.fill('username', 'testuser')
        browser.fill('password1', 'password123')
        browser.fill('password2', 'differentpassword456')

        # Submit form with validation error (mismatched passwords)
        browser.find_by_css('[up-main="modal"] button[type="submit"]').first.click()

        # Modal should STAY open due to validation error
        assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=2)

        # Error message should be visible (password mismatch)
        assert browser.is_text_present("password", wait_time=2), "Password validation error should be visible"

        # Should NOT see full page layout elements (navbar, sidebar) inside modal
        modal = browser.find_by_css('[up-main="modal"]').first
        # Check that sidebar/navbar is NOT inside the modal
        assert not modal.find_by_css('.navbar'), "Full navbar should not be in modal"
        assert not modal.find_by_css('.sidebar'), "Sidebar should not be in modal"

    def test_edit_user_modal_updates_and_redirects(self, browser, admin_user, test_users, live_server):
        """
        Test that:
        1. Edit button opens modal with pre-filled form
        2. Form submission updates the user
        3. Modal closes and returns to list page
        4. Updated data is visible
        """
        # Login
        browser.visit(f'{live_server.url}/auth/login/')
        browser.fill('username', 'admin')
        browser.fill('password', 'admin123')
        browser.find_by_css('button[type="submit"]').first.click()

        # Verify login was successful
        assert browser.is_text_present('Logout'), "Login should have succeeded"

        # Navigate to user list
        browser.visit(f'{live_server.url}/auth/user/')
        initial_url = browser.url

        # Find and click edit button for first test user
        user = test_users[0]
        edit_button = browser.find_by_css(f'a[href*="/auth/user/{user.pk}/edit"]').first
        edit_button.click()

        # Wait for modal
        assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=2)

        # Form should be pre-filled with user data
        username_input = browser.find_by_css('[up-main="modal"] input[name="username"]').first
        assert username_input.value == user.username

        # Update username
        browser.fill('username', f'{user.username}_updated')

        # Submit form
        browser.find_by_css('[up-main="modal"] button[type="submit"]').first.click()

        # Modal should close and return to list
        assert browser.is_element_not_present_by_css('[up-main="modal"]', wait_time=2)
        assert browser.url == initial_url

        # Updated username should be visible
        assert browser.is_text_present(f'{user.username}_updated')

    def test_delete_confirmation_modal(self, browser, admin_user, test_users, live_server):
        """
        Test that:
        1. Delete button opens confirmation modal
        2. Clicking delete removes the user
        3. Modal closes and returns to list
        4. Deleted user is not in list
        """
        # Login
        browser.visit(f'{live_server.url}/auth/login/')
        browser.fill('username', 'admin')
        browser.fill('password', 'admin123')
        browser.find_by_css('button[type="submit"]').first.click()

        # Verify login was successful
        assert browser.is_text_present('Logout'), "Login should have succeeded"

        # Navigate to user list
        browser.visit(f'{live_server.url}/auth/user/')
        initial_url = browser.url

        # Get username before deletion
        user = test_users[0]
        username = user.username

        # Click delete button
        delete_button = browser.find_by_css(f'a[href*="/auth/user/{user.pk}/delete"]').first
        delete_button.click()

        # Wait for confirmation modal
        assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=2)

        # Should see confirmation message
        assert browser.is_text_present('Are you sure')

        # Click delete button in modal
        browser.find_by_css('[up-main="modal"] button[type="submit"]').first.click()

        # Modal should close
        assert browser.is_element_not_present_by_css('[up-main="modal"]', wait_time=2)
        assert browser.url == initial_url

        # User should not be in list anymore
        assert not browser.is_text_present(username)

    def test_cancel_button_closes_modal_without_changes(self, browser, admin_user, test_users, live_server):
        """
        Test that:
        1. Cancel button in modal closes it without making changes
        2. Returns to list page
        """
        # Login
        browser.visit(f'{live_server.url}/auth/login/')
        browser.fill('username', 'admin')
        browser.fill('password', 'admin123')
        browser.find_by_css('button[type="submit"]').first.click()

        # Verify login was successful
        assert browser.is_text_present('Logout'), "Login should have succeeded"

        # Navigate to user list
        browser.visit(f'{live_server.url}/auth/user/')
        initial_url = browser.url
        initial_user_count = User.objects.count()

        # Open create modal
        browser.find_by_css('a[href*="/auth/user/create"]').first.click()
        assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=2)

        # Click cancel button
        browser.find_by_css('[up-main="modal"] button[up-dismiss]').first.click()

        # Modal should close
        assert browser.is_element_not_present_by_css('[up-main="modal"]', wait_time=2)

        # Should be back on list page
        assert browser.url == initial_url

        # No new users should be created
        assert User.objects.count() == initial_user_count

    def test_multiple_validation_errors_persist_through_resubmissions(self, browser, admin_user, live_server):
        """
        Test that:
        1. Modal stays open through multiple failed submissions
        2. Error messages are displayed correctly each time
        3. next parameter persists through resubmissions
        """
        # Login
        browser.visit(f'{live_server.url}/auth/login/')
        browser.fill('username', 'admin')
        browser.fill('password', 'admin123')
        browser.find_by_css('button[type="submit"]').first.click()

        # Verify login was successful
        assert browser.is_text_present('Logout'), "Login should have succeeded"

        # Navigate to user list
        browser.visit(f'{live_server.url}/auth/user/')
        initial_url = browser.url

        # Open create modal
        browser.find_by_css('a[href*="/auth/user/create"]').first.click()
        assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=2)

        # First failed submission - no username
        browser.find_by_css('[up-main="modal"] button[type="submit"]').first.click()
        assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=2)

        # Second failed submission - still no username
        browser.find_by_css('[up-main="modal"] button[type="submit"]').first.click()
        assert browser.is_element_present_by_css('[up-main="modal"]', wait_time=2)

        # Third time - fill correctly (UserCreationForm uses password1 and password2)
        browser.fill('username', 'finallyright')
        browser.fill('password1', 'pass123Strong!')
        browser.fill('password2', 'pass123Strong!')
        browser.find_by_css('[up-main="modal"] button[type="submit"]').first.click()

        # Should close and redirect to initial URL
        assert browser.is_element_not_present_by_css('[up-main="modal"]', wait_time=2)
        assert browser.url == initial_url
        assert browser.is_text_present('finallyright')
