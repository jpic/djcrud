"""
Authentication views for djcrud_auth.

Login and logout views that integrate with Django's authentication system.
"""

from django import forms
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect
from django.http import HttpResponseRedirect

from djcrud import mvc, attribute
from djcrud.views.form import FormView
from djcrud.views.unpoly import UnpolyModalMixin


class LoginView(FormView):
    """Login view using Django's authentication."""
    form_class = AuthenticationForm
    template_name = 'djcrud_auth/login.html'
    urlpath = 'login'
    urlname = 'login'
    tags = ['main']
    icon = 'box-arrow-in-right'

    @attribute.getter
    def title(self):
        """Return page title."""
        return 'Login'

    @property
    def has_perm(self):
        """Show login only to anonymous users."""
        return not self.request.user.is_authenticated

    def form_valid(self, form):
        login(self.request, form.get_user())
        return redirect(self.get_success_url())

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        return next_url if next_url else '/'


class LogoutConfirmForm(forms.Form):
    """Empty form for logout confirmation."""
    pass


class LogoutView(UnpolyModalMixin, FormView):
    """Logout confirmation view."""
    form_class = LogoutConfirmForm
    template_name = 'djcrud_auth/logout_confirm.html'
    urlpath = 'logout'
    urlname = 'logout'
    tags = ['main']
    icon = 'box-arrow-right'
    action = 'click->modal#open'
    partial_name = 'content'

    @property
    def has_perm(self):
        """Show logout only to authenticated users."""
        return self.request.user.is_authenticated

    @attribute.getter
    def title(self):
        """Return 'Logout USERNAME' for authenticated users."""
        if self.request.user.is_authenticated:
            return f'Logout {self.request.user.username}'
        return 'Logout'

    def form_valid(self, form):
        """Log out the user and redirect to homepage."""
        logout(self.request)
        return HttpResponseRedirect('/')

    def get_success_url(self):
        return '/'


__all__ = ['LoginView', 'LogoutView']
