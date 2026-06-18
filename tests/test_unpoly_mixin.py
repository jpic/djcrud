"""Unit tests for Unpoly mixins."""

from django.test import RequestFactory
from django.views.generic import FormView
from django import forms

from djcrud.views.unpoly import UnpolyModalMixin


class DjangoTestForm(forms.Form):
    """Test form for modal mixin tests."""
    name = forms.CharField()


class TestUnpolyModalMixin:
    """Test UnpolyModalMixin dispatch method."""

    def test_dispatch_without_modal_mode(self):
        """When no X-Up-Mode header, return normal response without X-Up-Location."""
        class MyView(UnpolyModalMixin, FormView):
            form_class = DjangoTestForm
            success_url = '/success/'

        request = RequestFactory().post('/create/', data={'name': 'test'})
        view = MyView.as_view()

        response = view(request)

        # Should be a redirect response (status 302) without X-Up-Location
        assert response.status_code == 302
        assert 'X-Up-Location' not in response

    def test_dispatch_with_modal_mode_redirect(self):
        """When X-Up-Mode is 'modal' and redirect, add X-Up-Location header."""
        class MyView(UnpolyModalMixin, FormView):
            form_class = DjangoTestForm
            success_url = '/success/'

        request = RequestFactory().post('/create/?page=2', data={'name': 'test'}, HTTP_X_UP_MODE='modal')
        view = MyView.as_view()

        response = view(request)

        # Should have redirect with X-Up-Location header
        assert response.status_code == 302
        assert response['X-Up-Location'] == '/create/?page=2'

    def test_dispatch_with_drawer_mode(self):
        """When X-Up-Mode is 'drawer', add X-Up-Location header."""
        class MyView(UnpolyModalMixin, FormView):
            form_class = DjangoTestForm
            success_url = '/success/'

        request = RequestFactory().post('/create/', data={'name': 'test'}, HTTP_X_UP_MODE='drawer')
        view = MyView.as_view()

        response = view(request)

        assert response.status_code == 302
        assert response['X-Up-Location'] == '/create/'

    def test_dispatch_preserves_query_string(self):
        """X-Up-Location includes query string from request."""
        class MyView(UnpolyModalMixin, FormView):
            form_class = DjangoTestForm
            success_url = '/success/'

        request = RequestFactory().post('/create/?sort=name&page=3', data={'name': 'test'}, HTTP_X_UP_MODE='modal')
        view = MyView.as_view()

        response = view(request)

        assert response.status_code == 302
        assert response['X-Up-Location'] == '/create/?sort=name&page=3'
