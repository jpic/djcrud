"""Unit tests for Unpoly mixins."""

from django.test import RequestFactory
from django.views.generic import FormView
from django import forms

from djcrud.views.unpoly import UnpolyMixin


class DjangoTestForm(forms.Form):
    """Test form for modal mixin tests."""
    name = forms.CharField()


class TestUnpolyMixin:
    """Test UnpolyMixin dispatch method."""

    def test_dispatch_without_modal_mode(self):
        """When no X-Up-Mode header, return normal response without X-Up-Location."""
        class MyView(UnpolyMixin, FormView):
            form_class = DjangoTestForm
            success_url = '/success/'

        request = RequestFactory().post('/create/', data={'name': 'test'})
        view = MyView.as_view()

        response = view(request)

        # Should be a redirect response (status 302) without X-Up-Location
        assert response.status_code == 302
        assert 'X-Up-Location' not in response

    def test_dispatch_with_modal_mode_redirect(self):
        """When X-Up-Mode is 'modal' and redirect, add X-Up-Accept-Layer and X-Up-Location headers."""
        class MyView(UnpolyMixin, FormView):
            form_class = DjangoTestForm
            success_url = '/success/'

        request = RequestFactory().post('/create/?page=2', data={'name': 'test'}, HTTP_X_UP_MODE='modal')
        view = MyView.as_view()

        response = view(request)

        # Should have redirect with X-Up-Accept-Layer (to close modal) and X-Up-Location (to navigate)
        assert response.status_code == 302
        assert response['X-Up-Accept-Layer'] == 'null'
        assert response['X-Up-Location'] == '/success/'

    def test_dispatch_with_drawer_mode(self):
        """When X-Up-Mode is 'drawer', add X-Up-Accept-Layer and X-Up-Location headers."""
        class MyView(UnpolyMixin, FormView):
            form_class = DjangoTestForm
            success_url = '/success/'

        request = RequestFactory().post('/create/', data={'name': 'test'}, HTTP_X_UP_MODE='drawer')
        view = MyView.as_view()

        response = view(request)

        assert response.status_code == 302
        assert response['X-Up-Accept-Layer'] == 'null'
        assert response['X-Up-Location'] == '/success/'

    def test_dispatch_navigates_to_success_url(self):
        """X-Up-Location navigates to the redirect target (success_url)."""
        class MyView(UnpolyMixin, FormView):
            form_class = DjangoTestForm
            success_url = '/success/?status=created'

        request = RequestFactory().post('/create/?sort=name&page=3', data={'name': 'test'}, HTTP_X_UP_MODE='modal')
        view = MyView.as_view()

        response = view(request)

        assert response.status_code == 302
        assert response['X-Up-Accept-Layer'] == 'null'
        assert response['X-Up-Location'] == '/success/?status=created'

    def test_dispatch_with_form_errors_keeps_modal_open(self):
        """When form has errors in modal mode, don't set X-Up-Location (modal stays open)."""
        from django.http import HttpResponse

        class MyView(UnpolyMixin, FormView):
            form_class = DjangoTestForm
            success_url = '/success/'

            def render_to_response(self, context, **response_kwargs):
                """Override to avoid template rendering in test."""
                return HttpResponse("Form with errors", status=200)

        # Submit invalid form (missing required 'name' field)
        request = RequestFactory().post('/create/', data={}, HTTP_X_UP_MODE='modal')
        view = MyView.as_view()

        response = view(request)

        # Should render form with errors (status 200)
        assert response.status_code == 200
        # Should NOT set X-Up-Location (modal stays open, Unpoly handles it)
        assert 'X-Up-Location' not in response
        # Should NOT set X-Up-Target (let Unpoly's default behavior work)
        assert 'X-Up-Target' not in response

    def test_up_target_attribute_available(self):
        """View can have up_target attribute for forms that should update root layer."""
        from djcrud.mvc import View

        class MyView(UnpolyMixin, View, FormView):
            form_class = DjangoTestForm
            success_url = '/success/'
            up_target = 'root'

        request = RequestFactory().get('/login/')
        view = MyView()
        view.request = request

        # Should have up_target attribute set
        assert view.up_target == 'root'

    def test_dispatch_redirects_to_next_in_modal_mode(self):
        """When in modal mode with next parameter, redirect to next instead of success_url."""
        class MyView(UnpolyMixin, FormView):
            form_class = DjangoTestForm
            success_url = '/success/'

        # Simulate a form submission from a list page in modal mode with next parameter
        request = RequestFactory().post(
            '/create/',
            data={'name': 'test', 'next': '/list/'},
            HTTP_X_UP_MODE='modal'
        )
        view = MyView.as_view()
        response = view(request)

        # Should redirect to next, not success_url
        assert response.status_code == 302
        assert response['Location'] == '/list/'
        assert response['X-Up-Accept-Layer'] == 'null'
        assert response['X-Up-Location'] == '/list/'

    def test_dispatch_without_next_parameter_uses_success_url(self):
        """When in modal mode without next parameter, use success_url for redirect."""
        class MyView(UnpolyMixin, FormView):
            form_class = DjangoTestForm
            success_url = '/success/'

        # Simulate form submission in modal mode without next parameter
        request = RequestFactory().post(
            '/create/',
            data={'name': 'test'},
            HTTP_X_UP_MODE='modal'
        )
        view = MyView.as_view()
        response = view(request)

        # Should redirect to success_url when no next parameter
        assert response.status_code == 302
        assert response['Location'] == '/success/'
        assert response['X-Up-Accept-Layer'] == 'null'
        assert response['X-Up-Location'] == '/success/'
