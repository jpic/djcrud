"""
Test Bulma navbar topbar rendering.

Requirements:
1. Navbar contains hamburger-menu web component
2. Navbar displays root controller name in center
3. Navbar displays views tagged with 'topbar' on the right
4. LoginView and LogoutView are tagged with 'topbar'
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.bulma
class TestBulmaNavbarRendering:
    """Test that the Bulma navbar renders correctly."""

    @pytest.fixture
    def superuser(self):
        """Create a superuser."""
        return User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )

    def test_navbar_has_hamburger_menu_component(self, superuser):
        """Navbar should contain hamburger-menu web component."""
        client = Client()
        client.force_login(superuser)

        response = client.get('/auth/user/')

        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Should have hamburger-menu web component
        assert '<hamburger-menu' in content
        assert 'target="#sidebar"' in content

    def test_navbar_displays_controller_name(self, superuser):
        """Navbar should display root controller name in center."""
        client = Client()
        client.force_login(superuser)

        response = client.get('/auth/user/')

        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Should display the root controller name
        assert 'navbar-start' in content
        # Root site controller has name = 'djcrud Example'
        assert 'djcrud Example' in content

    def test_navbar_displays_topbar_views(self, superuser):
        """Navbar should display views tagged with 'topbar' on the right."""
        client = Client()
        client.force_login(superuser)

        response = client.get('/auth/user/')

        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Should have navbar-end section
        assert 'navbar-end' in content

        # Logout should be in topbar (authenticated user)
        assert 'Logout' in content
        assert '/auth/logout/' in content

        # Should have logout icon
        assert 'bi-box-arrow-right' in content

    def test_navbar_shows_login_for_anonymous(self):
        """Anonymous users should see Login in topbar."""
        client = Client()

        response = client.get('/')

        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Should have Login in navbar (anonymous)
        assert 'navbar-end' in content
        assert 'Login' in content
        assert '/auth/login/' in content

        # Should have login icon
        assert 'bi-box-arrow-in-right' in content

    def test_navbar_structure(self, superuser):
        """Test complete navbar structure."""
        client = Client()
        client.force_login(superuser)

        response = client.get('/auth/user/')

        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Verify navbar structure
        assert '<nav class="navbar"' in content
        assert '<div class="navbar-brand">' in content
        assert '<div class="navbar-menu">' in content
        assert '<div class="navbar-start">' in content
        assert '<div class="navbar-end">' in content

    def test_hamburger_script_loaded(self, superuser):
        """Hamburger menu JavaScript should be loaded."""
        client = Client()
        client.force_login(superuser)

        response = client.get('/auth/user/')

        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Should load hamburger.js module
        assert 'djcrud_bulma/js/hamburger.js' in content
        assert 'type="module"' in content
