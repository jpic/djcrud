"""
Tests for Unpoly modal support in djcrud.
"""

import pytest
from django.test import Client


@pytest.mark.django_db
def test_create_view_renders_full_page():
    """Create view renders full page when accessed directly."""
    client = Client()
    response = client.get('/auth/user/create/')

    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.content or b'<html' in response.content


@pytest.mark.django_db
def test_create_view_renders_full_page_for_unpoly(user):
    """Create view renders full HTML for Unpoly (Unpoly extracts the target element)."""
    client = Client()
    client.force_login(user)

    # Simulate Unpoly modal request with X-Up-Mode header
    # Unpoly will extract the target element from the full HTML response
    response = client.get('/auth/user/create/', HTTP_X_UP_MODE='modal')

    assert response.status_code == 200
    # Should still have full HTML structure - Unpoly extracts client-side
    content = response.content.decode()
    assert '<!DOCTYPE html>' in content
    # Should have the form content
    assert 'card' in content.lower() or 'box' in content.lower()


@pytest.mark.django_db
def test_delete_view_renders_full_page(superuser):
    """Delete view renders full page when accessed directly."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    test_user = User.objects.create(username='delete_test_user', email='delete@example.com')

    client = Client()
    client.force_login(superuser)
    response = client.get(f'/auth/user/{test_user.pk}/delete/')

    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.content or b'<html' in response.content


@pytest.mark.django_db
def test_delete_view_renders_full_page_for_unpoly(superuser):
    """Delete view renders full HTML for Unpoly (Unpoly extracts the target element)."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    test_user = User.objects.create(username='delete_partial_user', email='deletepartial@example.com')

    client = Client()
    client.force_login(superuser)

    # Simulate Unpoly modal request
    # Unpoly will extract the target element from the full HTML response
    response = client.get(f'/auth/user/{test_user.pk}/delete/', HTTP_X_UP_MODE='modal')

    assert response.status_code == 200
    # Should still have full HTML structure - Unpoly extracts client-side
    content = response.content.decode()
    assert '<!DOCTYPE html>' in content


@pytest.mark.django_db
def test_actions_column_appears_in_table(superuser):
    """Actions column should appear in user list table."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    # Create a test user
    User.objects.create(username='actions_test_user', email='actions@example.com')

    client = Client()
    client.force_login(superuser)
    response = client.get('/auth/user/')

    assert response.status_code == 200
    content = response.content.decode()

    # Check for Actions column header
    assert 'Actions' in content
    # Check for edit/delete buttons or links in the table
    assert 'edit' in content.lower() or 'pencil' in content.lower()
    assert 'delete' in content.lower() or 'trash' in content.lower()


@pytest.mark.django_db
def test_id_column_links_to_detail(superuser):
    """ID column should link to detail view."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    test_user = User.objects.create(username='id_link_test_user', email='idlink@example.com')

    client = Client()
    client.force_login(superuser)
    response = client.get('/auth/user/')

    assert response.status_code == 200
    content = response.content.decode()

    # Check that the ID is a link to the detail view
    assert f'/auth/user/{test_user.pk}/' in content


@pytest.mark.django_db
def test_table_has_uuid_and_unpoly_attributes(superuser):
    """Table container should have UUID id and Unpoly attributes on links."""
    from django.contrib.auth import get_user_model
    import re

    User = get_user_model()
    User.objects.create(username='unpoly_test_user', email='unpoly@example.com')

    client = Client()
    client.force_login(superuser)
    response = client.get('/auth/user/')

    assert response.status_code == 200
    content = response.content.decode()

    # Check for table-container with UUID id
    # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    uuid_pattern = r'<div class="table-container" id="([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"'
    match = re.search(uuid_pattern, content)
    assert match, "Table container should have a UUID id"

    table_id = match.group(1)

    # Check that links have up-follow and up-target attributes
    assert 'up-follow' in content, "Links should have up-follow attribute"
    assert f'up-target="#{table_id}"' in content, "Links should target the table UUID"
