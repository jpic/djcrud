"""
Pytest configuration and fixtures for djcrud tests.
"""

import pytest


@pytest.fixture
def rf():
    """Django RequestFactory instance."""
    from django.test import RequestFactory
    return RequestFactory()


@pytest.fixture
def user(db):
    """Regular user (not staff, not superuser)."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )


@pytest.fixture
def superuser(db):
    """Superuser for permission tests."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123"
    )


@pytest.fixture
def anonymous_request(rf):
    """Request with anonymous user."""
    request = rf.get('/')
    from django.contrib.auth.models import AnonymousUser
    request.user = AnonymousUser()
    return request


@pytest.fixture
def user_request(rf, user):
    """Request with authenticated regular user."""
    request = rf.get('/')
    request.user = user
    return request


@pytest.fixture
def superuser_request(rf, superuser):
    """Request with authenticated superuser."""
    request = rf.get('/')
    request.user = superuser
    return request
