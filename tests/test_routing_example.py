import pytest
from django.forms import ModelForm
from django.urls import reverse

from djcrud_example.routing_example.models import Item

pytestmark = pytest.mark.tutorial


@pytest.mark.django_db
def test_routing_list_renders_router_icon_in_sidebar(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("site:item:list"))

    assert response.status_code == 200
    assert b"bi-inbox" in response.content


@pytest.mark.django_db
def test_routing_create_get_renders_model_form(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("site:item:create"))

    assert response.status_code == 200
    assert isinstance(response.context["form"], ModelForm)
    assert "name" in response.context["form"].fields


@pytest.mark.django_db
def test_routing_crud(client, admin_user):
    client.force_login(admin_user)

    assert client.get(reverse("site:item:create")).status_code == 200
    client.post(reverse("site:item:create"), {"name": "Alice"})
    obj = Item.objects.get(name="Alice")

    list_response = client.get(reverse("site:item:list"))
    assert list_response.status_code == 200
    assert b"Alice" in list_response.content

    assert client.get(reverse("site:item:detail", args=[obj.pk])).status_code == 200

    client.post(reverse("site:item:update", args=[obj.pk]), {"name": "Bob"})
    obj.refresh_from_db()
    assert obj.name == "Bob"

    assert client.get(reverse("site:item:delete", args=[obj.pk])).status_code == 200
    client.post(reverse("site:item:delete", args=[obj.pk]))
    assert not Item.objects.filter(pk=obj.pk).exists()


@pytest.mark.django_db
def test_routing_bulk_delete(client, admin_user):
    client.force_login(admin_user)
    client.post(reverse("site:item:create"), {"name": "A"})
    client.post(reverse("site:item:create"), {"name": "B"})
    a = Item.objects.get(name="A")
    b = Item.objects.get(name="B")

    url = reverse("site:item:deleteobjects") + f"?pks={a.pk}&pks={b.pk}"
    response = client.get(url)
    assert response.status_code == 200
    content = response.content.decode()
    message = "Are you sure you want to delete the selected"
    assert message in content
    for heading in ("Summary", "Objects"):
        if heading in content:
            assert content.index(message) < content.index(heading)
    client.post(url, {"next": reverse("site:item:list")})
    assert Item.objects.count() == 0