"""
Test that Actions column is not orderable.
"""

import pytest
from django.test import Client


@pytest.mark.django_db
def test_actions_column_not_orderable(superuser):
    """Actions column header should be plain text, not a clickable link."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    User.objects.create(username='test_user', email='test@example.com')

    client = Client()
    client.force_login(superuser)
    response = client.get('/auth/user/')

    assert response.status_code == 200
    content = response.content.decode()

    # Check that Actions header exists
    assert 'Actions' in content

    # The Actions column should NOT have a sortable link
    # In django-tables2, orderable columns have links like: <a href="?sort=...">
    # We check that there's no link containing 'Actions' as the link text in the table header
    import re
    # Look for <a> tags that contain 'Actions' with a sort URL
    sortable_actions_pattern = r'<a\s+href="[^"]*sort[^"]*"[^>]*>Actions</a>'

    assert not re.search(sortable_actions_pattern, content), \
        "Actions column should not be rendered as a sortable link"
