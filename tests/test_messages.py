import pytest
from django.urls import reverse

from djcrud_example.routing_example.models import Item


@pytest.mark.django_db
def test_flashes_render_outside_layout(client, admin_user):
    """[up-flashes] must not sit between sidebar and main in the flex layout."""
    client.force_login(admin_user)

    response = client.get(reverse("site:item:list"))
    html = response.content.decode()

    layout_pos = html.find('class="djcrud-layout"')
    main_close = html.find("</main>")
    flashes_pos = html.find("up-flashes")

    assert layout_pos != -1
    assert main_close != -1
    assert flashes_pos != -1
    assert (
        flashes_pos > main_close
    ), "up-flashes should render after </main>, outside djcrud-layout"


@pytest.mark.django_db
def test_create_success_flash(client, admin_user):
    client.force_login(admin_user)

    response = client.post(
        reverse("site:item:create"),
        {"name": "Alice", "next": reverse("site:item:list")},
        follow=True,
    )

    assert response.status_code == 200
    assert b"up-flashes" in response.content
    assert b"was added successfully" in response.content
    assert b"Alice" in response.content
    assert Item.objects.filter(name="Alice").exists()


@pytest.mark.django_db
def test_user_create_invalid_field_flash_with_translated_labels(client, admin_user):
    """UserCreationForm uses gettext_lazy field labels — must not crash join()."""
    client.force_login(admin_user)

    response = client.post(
        reverse("site:auth:user:create"),
        {
            "username": "",
            "password1": "",
            "password2": "",
            "next": reverse("site:auth:user:list"),
        },
    )

    assert response.status_code == 400
    assert b"up-flashes" in response.content
    assert b"Please correct the errors below" in response.content


@pytest.mark.django_db
def test_create_invalid_field_flash_lists_field_names(client, admin_user):
    client.force_login(admin_user)

    response = client.post(
        reverse("site:item:create"),
        {"name": "", "next": reverse("site:item:list")},
    )

    assert response.status_code == 400
    assert b"up-flashes" in response.content
    assert b"Please correct the error below" in response.content


@pytest.mark.django_db
def test_login_invalid_shows_non_field_error_flash(client):
    response = client.post(
        reverse("site:auth:login"),
        {
            "username": "admin",
            "password": "wrong-password",
            "next": "/",
        },
    )

    assert response.status_code == 400
    assert b"up-flashes" in response.content
    assert b"correct username and password" in response.content


@pytest.mark.django_db
def test_bulk_delete_success_flash(client, admin_user):
    client.force_login(admin_user)
    a = Item.objects.create(name="A")
    b = Item.objects.create(name="B")

    url = reverse("site:item:deleteobjects") + f"?pks={a.pk}&pks={b.pk}"
    response = client.post(
        url,
        {"next": reverse("site:item:list")},
        follow=True,
    )

    assert response.status_code == 200
    assert b"up-flashes" in response.content
    assert b"Successfully deleted 2" in response.content
    assert Item.objects.count() == 0


@pytest.mark.django_db
def test_delete_success_flash(client, admin_user):
    client.force_login(admin_user)
    obj = Item.objects.create(name="ToDelete")

    response = client.post(
        reverse("site:item:delete", args=[obj.pk]),
        {"next": reverse("site:item:list")},
        follow=True,
    )

    assert response.status_code == 200
    assert b"up-flashes" in response.content
    assert b"was deleted successfully" in response.content
    assert b"ToDelete" in response.content
    assert not Item.objects.filter(pk=obj.pk).exists()


@pytest.mark.django_db
def test_login_success_flash(client, admin_user):
    client.logout()

    response = client.post(
        reverse("site:auth:login"),
        {
            "username": "admin",
            "password": "password",
            "next": "/",
        },
        follow=True,
    )

    assert response.status_code == 200
    assert b"up-flashes" in response.content
    assert b"Logged in as" in response.content


@pytest.mark.django_db
def test_logout_success_flash(client, admin_user):
    client.force_login(admin_user)

    response = client.post(
        reverse("site:auth:logout"),
        {"next": "/"},
        follow=True,
    )

    assert response.status_code == 200
    assert b"up-flashes" in response.content
    assert b"Logged out" in response.content
