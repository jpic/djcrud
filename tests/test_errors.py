import pytest
from django.contrib.auth import get_user_model
from django.template.response import TemplateResponse
from django.urls import reverse

from djcrud.errors import (
    bad_request_response,
    forbidden_response,
    layout_view_for_request,
    not_found_response,
    server_error_response,
)
from djcrud.handlers import handler400, handler403, handler404, handler500

User = get_user_model()


@pytest.fixture
def target_user(db):
    return User.objects.create_user(
        username="foo",
        email="foo@example.com",
        password="Download@123",
    )


def _assert_layout_response(response, status, title):
    assert response.status_code == status
    assert isinstance(response, TemplateResponse)
    content = response.render().content.decode()
    assert title in content
    assert "navbar" in content
    assert f"HTTP {status}" in content


@pytest.mark.django_db
def test_forbidden_response_renders_layout(rf, admin_user):
    import djcrud

    djcrud.site.build()
    request = rf.get("/auth/user/")
    request.user = admin_user
    response = forbidden_response(request, view=layout_view_for_request(request))
    _assert_layout_response(response, 403, "Forbidden")


@pytest.mark.django_db
def test_not_found_response_renders_layout(rf, admin_user):
    request = rf.get("/missing/")
    request.user = admin_user
    response = not_found_response(request, view=layout_view_for_request(request))
    _assert_layout_response(response, 404, "Page not found")


@pytest.mark.django_db
def test_bad_request_response_renders_layout(rf, admin_user):
    request = rf.get("/bad/")
    request.user = admin_user
    response = bad_request_response(request, view=layout_view_for_request(request))
    _assert_layout_response(response, 400, "Bad request")


@pytest.mark.django_db
def test_server_error_response_renders_layout(rf, admin_user):
    request = rf.get("/broken/")
    request.user = admin_user
    response = server_error_response(request, view=layout_view_for_request(request))
    _assert_layout_response(response, 500, "Server error")


@pytest.mark.django_db
def test_handler404_unknown_url(client):
    response = client.get("/this-page-does-not-exist/")
    _assert_layout_response(response, 404, "Page not found")


@pytest.mark.django_db
def test_handler403_via_view_dispatch(client, admin_user, target_user):
    client.force_login(admin_user)
    client.get(reverse("site:auth:user:su", args=[target_user.pk]))
    response = client.get(reverse("site:auth:user:list"))
    _assert_layout_response(response, 403, "Forbidden")
    assert "Back to your account" in response.content.decode()


@pytest.mark.django_db
def test_handler400(client, rf, admin_user):
    request = rf.get("/")
    request.user = admin_user
    response = handler400(request)
    _assert_layout_response(response, 400, "Bad request")


@pytest.mark.django_db
def test_handler500(client, rf, admin_user):
    request = rf.get("/")
    request.user = admin_user
    response = handler500(request)
    _assert_layout_response(response, 500, "Server error")


@pytest.mark.django_db
def test_become_without_session_renders_not_found(client, admin_user):
    client.force_login(admin_user)
    response = client.get(reverse("site:auth:su"))
    _assert_layout_response(response, 404, "Page not found")
