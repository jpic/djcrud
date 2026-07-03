import pytest
from django.urls import reverse

from djcrud_example.models import User
from djcrud_example.security_example.models import Document

pytestmark = pytest.mark.tutorial


@pytest.mark.django_db
def test_permission_anonymous_can_list_secured_documents(client):
    owner = User.objects.create_user("owner", password="pass")
    Document.objects.create(title="Secured", owner=owner)

    response = client.get(reverse("site:secured-document:list"))
    assert response.status_code == 200
    assert b"Secured" in response.content


@pytest.mark.django_db
def test_permission_anonymous_cannot_create(client):
    response = client.get(reverse("site:secured-document:create"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_permission_owner_can_update_own_secured_document(client):
    owner = User.objects.create_user("owner", password="pass")
    other = User.objects.create_user("other", password="pass")
    doc = Document.objects.create(title="Mine", owner=owner)
    client.force_login(owner)

    assert (
        client.get(
            reverse("site:secured-document:update", args=[doc.pk])
        ).status_code
        == 200
    )

    client.force_login(other)
    assert (
        client.get(
            reverse("site:secured-document:update", args=[doc.pk])
        ).status_code
        == 404
    )


@pytest.mark.django_db
def test_permission_bulk_delete_intersects_scope(client, admin_user):
    owner = User.objects.create_user("owner", password="pass")
    other = User.objects.create_user("other", password="pass")
    mine = Document.objects.create(title="mine", owner=owner)
    theirs = Document.objects.create(title="theirs", owner=other)
    client.force_login(owner)

    url = (
        reverse("site:secured-document:deleteobjects")
        + f"?pks={mine.pk}&pks={theirs.pk}"
    )
    response = client.get(url)
    content = response.content.decode()
    assert "mine" in content
    assert "theirs" not in content

    client.post(url, {"next": reverse("site:secured-document:list")})
    assert Document.objects.filter(pk=mine.pk).exists() is False
    assert Document.objects.filter(pk=theirs.pk).exists() is True