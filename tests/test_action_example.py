import pytest
from django.urls import reverse

from djcrud_example.action_example.models import Memo

pytestmark = pytest.mark.tutorial


@pytest.mark.django_db
def test_duplicate_action(client, admin_user):
    memo = Memo.objects.create(title="Notes")
    client.force_login(admin_user)

    url = reverse("site:memo:duplicate", args=[memo.pk])
    assert client.get(url).status_code == 200
    response = client.post(url)
    assert response.status_code == 302
    assert Memo.objects.filter(title="Notes (copy)").exists()
