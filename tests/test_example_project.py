"""
Integration tests for the djcrud_example project.

These tests actually make HTTP requests to verify the full stack works.
"""

import pytest
from django.test import Client
from django.contrib.auth import get_user_model


# User = get_user_model()  # Avoid early import of swapped model; use fixture instead


@pytest.mark.django_db
def test_home_page_renders():
    """Home page renders successfully for anonymous users."""
    client = Client()
    response = client.get('/')

    assert response.status_code == 200
    assert b'djcrud' in response.content
    assert b'Welcome' in response.content


@pytest.mark.django_db
def test_home_page_has_frontend():
    """Home page includes either Bootstrap or Bulma CSS (depending on DJCRUD_FRONTEND)."""
    client = Client()
    response = client.get('/')

    assert response.status_code == 200
    # Check for either frontend (bootstrap CDN or bulma)
    content = response.content.lower()
    assert b'bootstrap' in content or b'bulma' in content


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
    from django.urls import reverse
    from django.urls.exceptions import NoReverseMatch

    # Home page should be reversible (the site controller from djcrud_example/urls.py
    # registers it at the root).
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
def test_logout_redirects(user):
    """Logout shows confirmation page on GET, redirects on POST."""
    client = Client()
    # Login first
    client.force_login(user)

    # GET should show confirmation page
    response = client.get('/auth/logout/')
    assert response.status_code == 200
    assert 'logout' in response.content.decode().lower()

    # POST should log out and redirect
    response = client.post('/auth/logout/')
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


@pytest.mark.django_db
def test_user_create_page(superuser):
    """Test the User create page at /auth/user/create/.

    Uses superuser because User creation is restricted (secure-by-default).
    On failure, prints the exact URL being tested (as requested).
    """
    client = Client()
    url = '/auth/user/create/'
    client.force_login(superuser)

    try:
        response = client.get(url)
        assert response.status_code == 200, f"Expected 200, got {response.status_code} for {url}"
        # Basic content checks (form should be present)
        assert b'form' in response.content.lower() or b'Create' in response.content, f"Expected form or title on {url}"
        assert b'User' in response.content or b'create' in response.content.lower(), f"Expected User create content on {url}"
    except Exception as e:
        print(f"\n=== TEST FAILED FOR URL: {url} ===")
        print(f"Error: {type(e).__name__}: {e}")
        print("This is the URL that failed (as requested).")
        raise


@pytest.mark.django_db
def test_user_create_and_list(superuser):
    """Test creating a user via POST to UserCreateView, then verify it appears in the list.

    Uses the superuser fixture for permission. Tests the full create -> list flow.
    """
    client = Client()
    client.force_login(superuser)

    # 1. POST to create a new user (uses UserCreationForm from djcrud_auth)
    create_url = '/auth/user/create/'
    username = 'testcreateduser'
    password = 'testpass123'

    response = client.post(
        create_url,
        {
            'username': username,
            'password1': password,
            'password2': password,
        },
        follow=False,  # Don't follow redirects, just check it redirects successfully
    )

    # Should redirect to detail view or fallback to home
    assert response.status_code == 302, f"Create should redirect, got {response.status_code}"

    # 2. GET the user list and ensure the new user appears
    list_url = '/auth/user/'
    response = client.get(list_url)

    assert response.status_code == 200, f"List view failed for {list_url}"
    assert username.encode() in response.content, f"Created username '{username}' not found in list view"
