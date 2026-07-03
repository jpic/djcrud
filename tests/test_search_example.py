import pytest
from django.urls import reverse

from djcrud_example.search_example.models import Page

pytestmark = pytest.mark.tutorial


@pytest.mark.django_db
def test_search_finds_page(client, admin_user):
    Page.objects.create(title="Tutorial page")
    client.force_login(admin_user)

    response = client.get(reverse("site:search"), {"q": "Tutorial"})
    assert response.status_code == 200
    assert b"Tutorial page" in response.content
