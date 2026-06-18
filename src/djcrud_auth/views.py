"""
Authentication views for djcrud_auth.

Login and logout views that integrate with Django's authentication system.
"""

from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect
from django.views.generic import RedirectView

from djcrud import mvc
from djcrud.views.form import FormView


class LoginView(FormView):
    """Login view using Django's authentication."""
    form_class = AuthenticationForm
    template_name = 'djcrud/form.html'
    urlpath = 'login'
    urlname = 'login'
    menus = ['main']
    icon = 'box-arrow-in-right'

    def get_title(self):
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


class LogoutView(mvc.View, RedirectView):
    """Logout view."""
    urlpath = 'logout'
    urlname = 'logout'
    menus = ['main']
    icon = 'box-arrow-right'
    permanent = False

    @property
    def has_perm(self):
        """Show logout only to authenticated users."""
        return self.request.user.is_authenticated

    def get_title(self):
        """Return 'Logout USERNAME' for authenticated users."""
        if self.request.user.is_authenticated:
            return f'Logout {self.request.user.username}'
        return 'Logout'

    def get_redirect_url(self, *args, **kwargs):
        logout(self.request)
        return '/'


__all__ = ['LoginView', 'LogoutView']
