import pytest
from django.urls import reverse
from django.utils import translation

from djcrud_example.routing_example.models import Item


@pytest.mark.django_db
def test_delete_button_uses_django_admin_translation(client, admin_user):
    client.force_login(admin_user)
    Item.objects.create(name="Test")

    with translation.override("fr"):
        response = client.get(
            reverse("site:item:list"),
            HTTP_ACCEPT_LANGUAGE="fr",
        )

    assert response.status_code == 200
    # French admin translation for Delete
    assert "Supprimer" in response.content.decode()


@pytest.mark.django_db
def test_clear_selection_uses_django_admin_translation(client, admin_user):
    client.force_login(admin_user)

    with translation.override("fr"):
        response = client.get(
            reverse("site:item:list"),
            HTTP_ACCEPT_LANGUAGE="fr",
        )

    assert response.status_code == 200
    # French admin translation for Clear selection
    assert "Effacer la sélection" in response.content.decode()


@pytest.mark.django_db
def test_navigation_label_is_translatable(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("site:item:list"))
    assert "Navigation" in response.content.decode()
