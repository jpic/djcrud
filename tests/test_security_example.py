import pytest
from django.urls import reverse

from djcrud_example.models import User
from djcrud_example.security_example.models import Document

pytestmark = pytest.mark.tutorial


@pytest.mark.django_db
def test_permission_anonymous_sees_only_published_documents(client):
    owner = User.objects.create_user("owner", password="pass")
    Document.objects.create(title="Public", owner=owner, published=True)
    Document.objects.create(title="Draft", owner=owner, published=False)

    response = client.get(reverse("site:secured-document:list"))
    assert response.status_code == 200
    assert b"Public" in response.content
    assert b"Draft" not in response.content


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
def test_publish_action(client, django_user_model):
    owner = django_user_model.objects.create_user(username="author", password="x")
    doc = Document.objects.create(
        title="Draft",
        published=False,
        owner=owner,
    )
    client.force_login(owner)

    url = reverse("site:secured-document:publish", args=[doc.pk])
    assert client.get(url).status_code == 200
    response = client.post(url)
    assert response.status_code == 302
    doc.refresh_from_db()
    assert doc.published is True

    response = client.get(reverse("site:secured-document:detail", args=[doc.pk]))
    assert response.status_code == 200
    assert b"/publish/" not in response.content


@pytest.mark.django_db
def test_publish_denied_for_non_owner(client, django_user_model):
    owner = django_user_model.objects.create_user(username="owner", password="x")
    stranger = django_user_model.objects.create_user(username="other", password="x")
    doc = Document.objects.create(
        title="Draft",
        published=False,
        owner=owner,
    )
    client.force_login(stranger)
    response = client.post(reverse("site:secured-document:publish", args=[doc.pk]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_publish_denied_when_already_published(client, django_user_model):
    owner = django_user_model.objects.create_user(username="author", password="x")
    doc = Document.objects.create(
        title="Live",
        published=True,
        owner=owner,
    )
    client.force_login(owner)
    response = client.post(reverse("site:secured-document:publish", args=[doc.pk]))
    assert response.status_code == 403