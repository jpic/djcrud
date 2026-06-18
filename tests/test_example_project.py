"""
Integration tests for the djcrud_example project.

These tests actually make HTTP requests to verify the full stack works.
"""

import pytest
from django.test import Client
from django.contrib.auth import get_user_model


User = get_user_model()


@pytest.mark.django_db
def test_home_page_renders():
    """Home page renders successfully for anonymous users."""
    client = Client()
    response = client.get('/')

    assert response.status_code == 200
    assert b'djcrud' in response.content
    assert b'Welcome' in response.content


@pytest.mark.django_db
def test_home_page_has_bootstrap():
    """Home page includes Bootstrap CSS."""
    client = Client()
    response = client.get('/')

    assert response.status_code == 200
    # Check for Bootstrap CDN
    assert b'bootstrap' in response.content.lower()


@pytest.mark.django_db
def test_home_page_has_sidebar():
    """Home page includes the sidebar."""
    client = Client()
    response = client.get('/')

    assert response.status_code == 200
    assert b'sidebar' in response.content.lower()


@pytest.mark.django_db
def test_home_page_public_access():
    """Home page allows anonymous access (has_perm=True)."""
    client = Client()
    # Don't login, test as anonymous
    response = client.get('/')

    # Should not redirect to login
    assert response.status_code == 200
    assert b'Welcome' in response.content


@pytest.mark.django_db
def test_home_page_context():
    """Home page has correct context variables."""
    client = Client()
    response = client.get('/')

    assert response.status_code == 200

    # Check context - everything accessed via view
    assert 'view' in response.context
    assert response.context['view'].icon == 'home'
    assert response.context['view'].title


@pytest.mark.django_db
def test_admin_page_exists():
    """Django admin is accessible."""
    client = Client()
    response = client.get('/admin/')

    # Should redirect to login
    assert response.status_code == 302


@pytest.mark.django_db
def test_url_resolution():
    """URLs are properly resolved from the site controller."""
    from django.urls import reverse, NoReverseMatch

    # Home page should be reversible
    url = reverse('home')
    assert url == '/'


@pytest.mark.django_db
def test_login_page_exists():
    """Login page is accessible at /auth/login/."""
    client = Client()
    response = client.get('/auth/login/')

    assert response.status_code == 200
    assert b'Login' in response.content


@pytest.mark.django_db
def test_login_page_public_access():
    """Login page allows anonymous access (has_perm=True)."""
    client = Client()
    # Don't login, test as anonymous
    response = client.get('/auth/login/')

    # Should not redirect
    assert response.status_code == 200
    assert b'form' in response.content.lower()


@pytest.mark.django_db
def test_logout_redirects():
    """Logout redirects to home page."""
    client = Client()
    response = client.get('/auth/logout/')

    # Should redirect
    assert response.status_code == 302
    assert response.url == '/'


@pytest.mark.django_db
def test_login_form_submission(user):
    """Login form works with valid credentials."""
    client = Client()

    response = client.post('/auth/login/', {
        'username': 'testuser',
        'password': 'testpass123',
    })

    # Should redirect after successful login
    assert response.status_code == 302
