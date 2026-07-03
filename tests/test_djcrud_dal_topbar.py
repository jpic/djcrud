import pytest
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from djcrud.views.log import ADDITION
from djcrud_dal_topbar.lookup import find_detail_url, iter_searchable_list_views
from djcrud_example.routing_example.models import Item

User = get_user_model()


@pytest.mark.django_db
def test_site_search_autocomplete(admin_client, admin_user):
    User.objects.create_user("member", password="pass")
    admin_client.force_login(admin_user)
    response = admin_client.get(reverse("site:autocomplete"), {"q": "member"})
    assert response.status_code == 200
    content = response.content.decode()
    assert "member" in content
    assert "data-url" in content
    assert "/detail/" in content


@pytest.mark.django_db
def test_find_detail_url_for_user(admin_user):
    user = User.objects.create_user("member", password="pass")
    url = find_detail_url(User, user.pk)
    assert url == reverse("site:auth:user:detail", args=[user.pk])


@pytest.mark.django_db
def test_site_search_excludes_models_without_list_permission(db, client):
    user = User.objects.create_user("viewer", password="pass")
    User.objects.create_user("member", password="pass")
    client.force_login(user)
    response = client.get(reverse("site:search"), {"q": "member"})
    assert response.status_code == 200
    assert b"No results found" in response.content


@pytest.mark.django_db
def test_site_search_excludes_models_without_add_search(admin_client, admin_user):
    marker = "unique_logentry_marker_xyz"
    ct = ContentType.objects.get_for_model(Item)
    LogEntry.objects.create(
        user_id=admin_user.pk,
        content_type=ct,
        object_id="1",
        object_repr=marker,
        action_flag=ADDITION,
        change_message="[]",
    )
    admin_client.force_login(admin_user)
    list_response = admin_client.get(reverse("site:logentry:list"))
    assert list_response.status_code == 200
    assert marker.encode() in list_response.content

    response = admin_client.get(reverse("site:search"), {"q": marker})
    assert response.status_code == 200
    assert "No results found" in response.content.decode()


@pytest.mark.django_db
def test_site_search_includes_item(admin_client, admin_user):
    Item.objects.create(name="searchable_item_xyz")
    admin_client.force_login(admin_user)
    response = admin_client.get(reverse("site:autocomplete"), {"q": "searchable_item"})
    assert response.status_code == 200
    content = response.content.decode()
    assert "searchable_item_xyz" in content
    assert "data-url" in content


@pytest.mark.django_db
def test_search_landing_page(admin_client, admin_user):
    admin_client.force_login(admin_user)
    response = admin_client.get(reverse("site:search"))
    assert response.status_code == 200
    content = response.content.decode()
    assert "djcrud-search-landing-box" in content
    assert "djcrud-search-form--landing" in content
    assert "djcrud-search-results-header" not in content


@pytest.mark.django_db
def test_search_get_shows_results(admin_client, admin_user):
    Item.objects.create(name="get_item_xyz")
    admin_client.force_login(admin_user)
    response = admin_client.get(reverse("site:search"), {"q": "get_item"})
    assert response.status_code == 200
    content = response.content.decode()
    assert "get_item_xyz" in content
    assert "djcrud-search-results-header" in content
    assert "table" in content


@pytest.mark.django_db
def test_search_results_page(admin_client, admin_user):
    Item.objects.create(name="results_item_xyz")
    admin_client.force_login(admin_user)
    response = admin_client.get(reverse("site:search"), {"q": "results_item"})
    assert response.status_code == 200
    content = response.content.decode()
    assert "results_item_xyz" in content
    assert "table" in content
    assert "djcrud-search-results-header" in content
    assert reverse("site:autocomplete") in content


@pytest.mark.django_db
def test_iter_searchable_list_views_respects_add_search(rf, admin_user):
    request = rf.get("/search/")
    request.user = admin_user
    models = {view.model for view in iter_searchable_list_views(request)}
    assert User in models
    assert Item in models
    from django.contrib.auth.models import Group

    assert Group in models
    assert LogEntry not in models


@pytest.mark.django_db
def test_pages_include_site_search_widget(admin_client, admin_user):
    admin_client.force_login(admin_user)
    response = admin_client.get(reverse("site:auth:user:list"))
    content = response.content.decode()
    assert "djcrud-site-search" in content
    assert reverse("site:search") in content
    assert reverse("site:autocomplete") in content
    assert "djcrud-site-search-wrap" in content
    assert 'slot="input"' in content
    assert "UNDEFINED" not in content
