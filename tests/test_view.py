import functools

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.template.response import TemplateResponse
from django.shortcuts import resolve_url
from django.views import generic

from djcrud.view import ViewMixin
from djcrud_example.models import User


@pytest.mark.django_db
def test_view_security(rf, admin_user):
    class UserDetailView(ViewMixin, generic.DetailView):
        queryset = User.objects.all()

        def has_permission(self):
            return self.request.user == self.object

        @functools.cached_property
        def object(self):
            return self.get_object()

    request = rf.get("/users/1/")
    request.user = admin_user
    view = UserDetailView(request=request, object=admin_user)
    assert view.has_permission() is True

    other_user = User.objects.create_user("other", password="pass")
    view = UserDetailView(request=request, object=other_user)
    assert view.has_permission() is False

    request.user = AnonymousUser()
    view = UserDetailView(request=request, object=admin_user)
    assert view.has_permission() is False

    request.user = AnonymousUser()
    view = UserDetailView(request=request, object=admin_user)
    response = view.dispatch(request)
    assert response.status_code == 302
    assert response.url == (resolve_url(settings.LOGIN_URL) + "?next=/users/1/")

    request.user = admin_user
    view = UserDetailView(request=request, object=other_user)
    response = view.dispatch(request)
    assert response.status_code == 403
    assert isinstance(response, TemplateResponse)


@pytest.mark.django_db
def test_login_url_default():
    assert resolve_url(settings.LOGIN_URL) == "/auth/login/"
