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
def test_modal_request_excludes_layout(user):
    """Modal requests should not render sidebar/navbar (only main content)."""
    client = Client()
    client.force_login(user)

    # Simulate Unpoly modal request
    response = client.get('/auth/user/create/', HTTP_X_UP_MODE='modal')

    assert response.status_code == 200
    content = response.content.decode()

    # Should NOT have sidebar/navbar elements
    assert 'sidebar' not in content.lower()
    assert 'navbar' not in content.lower()
    assert 'navigation' not in content.lower() or 'role="navigation"' not in content

    # Should have main content with up-main attribute
    assert 'up-main' in content
    # Should have form content (card/box)
    assert 'card' in content.lower() or 'box' in content.lower()


@pytest.mark.django_db
def test_table_has_uptable_and_unpoly_attributes(superuser):
    """Table container should have up-table attribute and Unpoly attributes on links."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    User.objects.create(username='unpoly_test_user', email='unpoly@example.com')

    client = Client()
    client.force_login(superuser)
    response = client.get('/auth/user/')

    assert response.status_code == 200
    content = response.content.decode()

    # Check for table-container with up-table attribute
    assert '<div class="table-container" up-table>' in content, "Table container should have up-table attribute"

    # Check that links have up-follow and up-target attributes
    assert 'up-follow' in content, "Links should have up-follow attribute"
    assert 'up-target="[up-table]"' in content, "Links should target [up-table]"


@pytest.mark.django_db
def test_detail_view_action_has_up_target(superuser):
    """DetailView action links should have up-target attribute."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    test_user = User.objects.create(username='detail_test_user', email='detail@example.com')

    client = Client()
    client.force_login(superuser)
    response = client.get('/auth/user/')

    assert response.status_code == 200
    content = response.content.decode()

    # Check that detail view link (eye icon) has up-target attribute
    # The link should have up-target="[up-main]" since DetailView.up_target is set
    assert 'up-target="[up-main]"' in content, "DetailView action link should have up-target=\"[up-main]\""
    # The detail view should be the eye icon
    assert 'bi-eye' in content, "DetailView action should have eye icon"
