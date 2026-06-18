"""
Test simplified menu system.

Requirements:
1. Main menu shows only views with menus=['main'] (no controller submenus)
2. UserListView, LoginView, LogoutView appear in main menu with menus=['main']
3. Menu is a flat list of view instances
4. LoginView shows only when NOT authenticated
5. LogoutView shows only when authenticated
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

User = get_user_model()

from djcrud.mvc import Controller
from djcrud.menu import get_menu
from djcrud.crud import UserListView, ModelController
from djcrud_auth.views import LoginView, LogoutView
from djcrud_auth.crud import UserController, AuthController
from djcrud import attribute


@pytest.fixture
def request_factory():
    """Return Django request factory."""
    return RequestFactory()


@pytest.fixture
def anonymous_user_request(request_factory):
    """Request with anonymous user."""
    request = request_factory.get('/')
    from django.contrib.auth.models import AnonymousUser
    request.user = AnonymousUser()
    return request


@pytest.fixture
def authenticated_user_request(request_factory, user):
    """Request with authenticated user."""
    request = request_factory.get('/')
    request.user = user
    return request


@pytest.fixture
def superuser_user(db):
    """Create a superuser."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='admin123'
    )


@pytest.fixture
def superuser_request(request_factory, superuser_user):
    """Request with superuser."""
    request = request_factory.get('/')
    request.user = superuser_user
    return request


@pytest.mark.django_db
class TestMainMenu:
    """Test simplified flat main menu."""

    def test_user_list_and_logout_in_main_menu_for_authenticated(self, superuser_request):
        """Authenticated superuser sees UserListView and LogoutView in main menu."""
        # UserController is already configured with User model
        auth_controller = AuthController(views=[
            LoginView,
            LogoutView,
            UserController,
        ])
        root = Controller(views=[auth_controller])

        menu = get_menu(root, 'main', superuser_request)

        # Should have LogoutView and UserListView (not LoginView)
        assert len(menu) == 2

        # All should be view instances
        from djcrud.mvc import View
        assert all(isinstance(item, View) for item in menu)

        # Get view class names
        view_names = [v.__class__.__name__ for v in menu]
        assert 'LogoutView' in view_names
        assert 'UserListView' in view_names
        assert 'LoginView' not in view_names

    def test_login_shows_for_anonymous(self, anonymous_user_request):
        """Anonymous user sees LoginView but not LogoutView."""
        auth_controller = AuthController(views=[
            LoginView,
            LogoutView,
        ])
        root = Controller(views=[auth_controller])

        menu = get_menu(root, 'main', anonymous_user_request)

        # Should have only LoginView
        assert len(menu) == 1
        assert menu[0].__class__.__name__ == 'LoginView'

    def test_logout_shows_username(self, authenticated_user_request, user):
        """LogoutView displays 'Logout USERNAME' when authenticated."""
        logout_view_class = LogoutView.clone()
        logout_view = logout_view_class()
        logout_view.request = authenticated_user_request

        title = logout_view.title
        assert 'Logout' in title
        assert user.username in title




@pytest.mark.django_db
class TestMenuHTMLRendering:
    """Test that menus actually render in HTML."""

    def test_home_page_renders_main_menu_for_superuser(self, superuser_user):
        """Home page renders main menu with UserListView and LogoutView."""
        from django.test import Client

        client = Client()
        client.force_login(superuser_user)

        response = client.get('/')

        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Should have sidebar navigation
        assert 'sidebar' in content.lower()

        # Should have Users link (UserListView with menus=['main'])
        assert 'users' in content.lower() or 'user' in content.lower()

        # Should have Logout (not Login, since we're authenticated)
        assert 'logout' in content.lower()

    def test_anonymous_sees_login(self):
        """Anonymous users see Login in menu."""
        from django.test import Client

        client = Client()
        response = client.get('/')

        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Should have Login (anonymous)
        assert 'login' in content.lower()


