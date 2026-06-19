"""
Form views for djcrud.
"""

from django.views.generic import FormView as DjangoFormView
from djcrud.mvc import View
from djcrud import attribute
from djcrud.views.unpoly import UnpolyMixin


class FormMixin:
    """
    Mixin for form-based views that provides smart success URL handling.

    This mixin provides get_success_url() logic that:
    1. Checks for a 'next' parameter (from modal links)
    2. Falls back to object's get_absolute_url() if available
    3. Falls back to cancel_url or '/'

    Used by CreateView, UpdateView, and DeleteView to avoid code duplication.
    """

    def get_success_url(self):
        """
        Get the URL to redirect to after successful form submission.

        Checks in order:
        1. POST/GET 'next' parameter (persists through form resubmissions)
        2. Object's get_absolute_url() method
        3. cancel_url or '/' as final fallback
        """
        # Check for next parameter first (from modal links)
        # This requires UnpolyMixin.get_next_url() to be available
        if hasattr(self, 'get_next_url'):
            next_url = self.get_next_url()
            if next_url:
                return next_url

        # Fall back to object's get_absolute_url
        if hasattr(self, 'object') and self.object and hasattr(self.object, 'get_absolute_url'):
            return self.object.get_absolute_url()

        # Final fallback
        return getattr(self, 'cancel_url', None) or '/'


class FormView(View, DjangoFormView):
    """
    Generic form view.

    Use this for forms that don't directly create/update model instances
    (like login, search, contact forms, etc.).

    For model forms, use CreateView or UpdateView instead.

    Attributes:
        form_class: Form class to use
        template_name: Template to render (default: djcrud/form.html)
        success_url: Where to redirect on success
        title: Page title

    Example:
        class SearchView(FormView):
            form_class = SearchForm
            template_name = 'search.html'
            success_url = '/results/'

            def form_valid(self, form):
                # Process form
                return super().form_valid(form)
    """
    template_name = 'djcrud/form.html'

    @attribute.getter
    def title(self):
        """Return page title.

        The title() getter does all the work.
        """
        # If a title was explicitly set on the instance/class (e.g. via clone), use it.
        # Otherwise return default. The @attribute.getter on title() itself is handled
        # by the descriptor system without recursion.
        if hasattr(type(self), 'title') and not callable(getattr(type(self), 'title', None)):
            # title is a plain attribute (from clone or subclass)
            return getattr(self, 'title')
        return 'Form'

    def get_context_data(self, **kwargs):
        """The base mvc.View.get_context_data already injects `view` and `site_controller=root_controller`."""
        return super().get_context_data(**kwargs)

    @attribute.cached
    def cancel_url(self):
        """Return URL to go back to."""
        # TODO: Implement proper back URL
        return '/'

    @attribute.cached
    def main_menu(self):
        """Get main navigation menu."""
        from djcrud.menu import get_menu
        if not self.root_controller:
            return []
        return get_menu(self.root_controller, 'main', self.request, exclude_current=self)


__all__ = ['FormMixin', 'FormView']
