"""Test that form validation errors render correctly in modals."""
import pytest
from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from django.views.generic import CreateView
from django import forms

from djcrud.views.unpoly import UnpolyMixin

User = get_user_model()


class TestForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']


class TestCreateView(UnpolyMixin, CreateView):
    model = User
    form_class = TestForm
    template_name = 'djcrud/form.html'
    success_url = '/success/'


@pytest.mark.django_db
def test_form_validation_error_in_modal_does_not_render_full_layout():
    """When form has validation errors in modal mode, should not render sidebar/navbar."""
    # Create request with Unpoly modal headers and invalid form data
    factory = RequestFactory()
    request = factory.post(
        '/create/',
        data={},  # Missing required username
        HTTP_X_UP_MODE='modal',
        HTTP_X_UP_TARGET='[up-main]',
    )

    view = TestCreateView.as_view()
    response = view(request)

    # Should return 200 (form errors)
    assert response.status_code == 200

    # Render the template response
    response.render()

    # Response content should NOT contain full page layout elements
    content = response.content.decode('utf-8')

    # Should have the modal wrapper
    assert 'up-main="modal"' in content

    # Should NOT have sidebar (it should be hidden by {% if view.unpoly.mode != 'modal' %})
    assert '<nav class="col-md-3' not in content or 'view.unpoly.mode != \'modal\'' in content

    # Verify unpoly context is set
    assert hasattr(response, 'context_data')
    assert 'view' in response.context_data
    assert hasattr(response.context_data['view'], 'unpoly')
    assert response.context_data['view'].unpoly['mode'] == 'modal'


@pytest.mark.django_db
def test_form_success_in_modal_redirects_to_next_parameter():
    """When form succeeds in modal with next parameter, should redirect there."""
    factory = RequestFactory()
    request = factory.post(
        '/create/',
        data={'username': 'testuser', 'next': '/list/'},
        HTTP_X_UP_MODE='modal',
    )

    view = TestCreateView.as_view()
    response = view(request)

    # Should redirect
    assert response.status_code == 302

    # Should redirect to next parameter, not success_url
    assert response['Location'] == '/list/'

    # Should have Unpoly headers to close modal
    assert response['X-Up-Accept-Layer'] == 'null'
    assert response['X-Up-Location'] == '/list/'


@pytest.mark.django_db
def test_form_success_without_next_uses_success_url():
    """When form succeeds without next parameter, should use success_url."""
    factory = RequestFactory()
    request = factory.post(
        '/create/',
        data={'username': 'testuser'},
        HTTP_X_UP_MODE='modal',
    )

    view = TestCreateView.as_view()
    response = view(request)

    # Should redirect
    assert response.status_code == 302

    # Should use success_url since no next parameter
    assert response['Location'] == '/success/'
    assert response['X-Up-Location'] == '/success/'
