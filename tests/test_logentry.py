import json

import pytest
from django.contrib.admin.models import LogEntry
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from djcrud.views.log import ADDITION, CHANGE, DELETION
from djcrud_example.routing_example.models import Item


@pytest.fixture
def routing_item(db):
    return Item.objects.create(name="Alice")


def logentries_for(obj):
    return LogEntry.objects.filter(object_id=str(obj.pk))


@pytest.mark.django_db
def test_create_logs_addition(client, admin_user, routing_item):
    client.force_login(admin_user)
    before = LogEntry.objects.count()

    client.post(reverse("site:item:create"), {"name": "Bob"})
    obj = Item.objects.get(name="Bob")

    assert LogEntry.objects.count() == before + 1
    entry = logentries_for(obj).get()
    assert entry.action_flag == ADDITION
    assert entry.user_id == admin_user.pk
    data = json.loads(entry.change_message)
    assert "extra" in data
    assert data["extra"]["path"] == reverse("site:item:create")


@pytest.mark.django_db
def test_update_logs_changed_fields(client, admin_user, routing_item):
    client.force_login(admin_user)

    client.post(
        reverse("site:item:update", args=[routing_item.pk]),
        {"name": "Bob"},
    )

    entry = logentries_for(routing_item).get()
    assert entry.action_flag == CHANGE
    data = json.loads(entry.change_message)
    assert "changes" in data
    assert data["changes"] == [{"changed": {"fields": ["Name"]}}]


@pytest.mark.django_db
def test_delete_logs_deletion(client, admin_user, routing_item):
    client.force_login(admin_user)
    pk = routing_item.pk

    client.post(reverse("site:item:delete", args=[pk]))

    entry = LogEntry.objects.filter(object_id=str(pk)).get()
    assert entry.action_flag == DELETION


@pytest.mark.django_db
def test_bulk_delete_logs_each(client, admin_user):
    client.force_login(admin_user)
    client.post(reverse("site:item:create"), {"name": "A"})
    client.post(reverse("site:item:create"), {"name": "B"})
    a = Item.objects.get(name="A")
    b = Item.objects.get(name="B")
    before = LogEntry.objects.filter(action_flag=DELETION).count()

    url = reverse("site:item:deleteobjects") + f"?pks={a.pk}&pks={b.pk}"
    client.post(url, {"next": reverse("site:item:list")})

    assert LogEntry.objects.filter(action_flag=DELETION).count() == before + 2
    assert LogEntry.objects.filter(action_flag=DELETION, object_id=str(a.pk)).exists()
    assert LogEntry.objects.filter(action_flag=DELETION, object_id=str(b.pk)).exists()


@pytest.mark.django_db
def test_no_log_when_anonymous(client, routing_item):
    before = LogEntry.objects.count()
    client.post(reverse("site:item:create"), {"name": "Ghost"})
    assert LogEntry.objects.count() == before


@pytest.mark.django_db
def test_model_router_includes_history():
    import djcrud
    from djcrud_history.views import HistoryView

    item_router = djcrud.site.routes["item"]
    assert any(isinstance(route, HistoryView) for route in item_router.routes)


@pytest.mark.django_db
def test_custom_model_router_includes_history():
    import djcrud
    from djcrud_history.views import HistoryView

    user_router = djcrud.site.routes["auth"].routes["user"]
    assert any(isinstance(route, HistoryView) for route in user_router.routes)


@pytest.mark.django_db
def test_history_view_lists_entries(client, admin_user, routing_item):
    client.force_login(admin_user)
    client.post(
        reverse("site:item:update", args=[routing_item.pk]),
        {"name": "Updated"},
    )

    url = reverse("site:item:history", args=[routing_item.pk])
    response = client.get(url)

    assert response.status_code == 200
    assert b"Changed" in response.content
    assert b"Updated" in response.content


@pytest.mark.django_db
def test_history_paginated(client, admin_user, routing_item):
    client.force_login(admin_user)
    for i in range(30):
        client.post(
            reverse("site:item:update", args=[routing_item.pk]),
            {"name": f"Name-{i}"},
        )

    url = reverse("site:item:history", args=[routing_item.pk])
    page1 = client.get(url)
    page2 = client.get(url + "?page=2")

    assert page1.status_code == 200
    assert page2.status_code == 200
    assert page1.content != page2.content


@pytest.mark.django_db
def test_user_detail_shows_history_in_object_menu(client, admin_user):
    client.force_login(admin_user)
    url = reverse("site:auth:user:detail", args=[admin_user.pk])
    response = client.get(url)

    assert response.status_code == 200
    view = response.context["view"]
    menu = view.router.get_tagged_views(
        "object",
        request=view.request,
        object=view.object,
    )
    history_url = reverse("site:auth:user:history", args=[admin_user.pk])
    menu_urls = [item.url for item in menu]
    assert history_url in menu_urls


@pytest.mark.django_db
def test_history_shows_object_menu(client, admin_user, routing_item):
    client.force_login(admin_user)
    url = reverse("site:item:history", args=[routing_item.pk])
    response = client.get(url)

    assert response.status_code == 200
    view = response.context["view"]
    menu = view.router.model_router.get_tagged_views(
        "object",
        request=view.request,
        object=view.object,
    )
    menu_urls = [item.url for item in menu if item.url != view.request.path_info]
    detail_url = reverse("site:item:detail", args=[routing_item.pk])
    assert detail_url in menu_urls


@pytest.mark.django_db
def test_history_page_titles_and_breadcrumbs(client, admin_user, routing_item):
    client.force_login(admin_user)
    url = reverse("site:item:history", args=[routing_item.pk])
    response = client.get(url)

    assert response.status_code == 200
    content = response.content.decode()
    assert str(routing_item) in content
    assert "History" in content
    assert "Detail" in content
    assert "Change Item" in content
    assert "Delete" in content
    assert f"{routing_item} History" not in content
    assert f"{routing_item} Detail" not in content


@pytest.mark.django_db
def test_format_logentry_message_handles_mixed_change_formats():
    from djcrud.views.log import format_logentry_message

    message = json.dumps(
        {
            "label": "Update",
            "changes": [
                {"changed": {"fields": ["first_name"]}},
                {"changed": {"first_name": ["", "aoeueoau"]}},
            ],
            "extra": {"view": "UpdateView", "path": "/auth/user/41/update/"},
        }
    )
    rendered = format_logentry_message(message)

    assert "first_name" in rendered
    assert "aoeueoau" in rendered


@pytest.mark.django_db
def test_user_history_renders_mixed_log_entries(client, admin_user):
    from django.contrib.admin.models import LogEntry
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.create_user(username="historyuser", password="x")
    ct = ContentType.objects.get_for_model(User)
    LogEntry.objects.create(
        user_id=admin_user.pk,
        content_type=ct,
        object_id=str(user.pk),
        object_repr=str(user),
        action_flag=CHANGE,
        change_message=json.dumps(
            {
                "label": "Update",
                "changes": [
                    {"changed": {"fields": ["first_name"]}},
                    {"changed": {"first_name": ["", "newname"]}},
                ],
            }
        ),
    )

    client.force_login(admin_user)
    response = client.get(reverse("site:auth:user:history", args=[user.pk]))

    assert response.status_code == 200
    assert b"newname" in response.content


@pytest.mark.django_db
def test_logentry_router_list(client, admin_user, routing_item):
    client.force_login(admin_user)
    client.post(reverse("site:item:create"), {"name": "Logged"})

    response = client.get(reverse("site:logentry:list"))

    assert response.status_code == 200
    assert b"Logged" in response.content
    assert b"Unknown" not in response.content
    assert b">Addition<" in response.content


@pytest.mark.django_db
def test_history_view_shows_action_labels(client, admin_user, routing_item):
    client.force_login(admin_user)
    client.post(
        reverse("site:item:update", args=[routing_item.pk]),
        {"name": "Updated"},
    )

    response = client.get(reverse("site:item:history", args=[routing_item.pk]))

    assert response.status_code == 200
    assert b"Unknown" not in response.content
    assert b">Change<" in response.content


@pytest.mark.django_db
def test_djcrud_history_requires_admin():
    from unittest.mock import patch

    from django.apps import apps

    config = apps.get_app_config("djcrud_history")
    with patch("django.conf.settings.INSTALLED_APPS", ["django.contrib.auth"]):
        with pytest.raises(ImproperlyConfigured):
            config.ready()
