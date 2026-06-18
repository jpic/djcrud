"""
Form views for djcrud.
"""

from django.views.generic import FormView as DjangoFormView
from djcrud.mvc import View
from djcrud import attribute


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

    def get_title(self):
        """Return page title."""
        if hasattr(self, 'title'):
            return self.title() if callable(self.title) else self.title
        return 'Form'

    def get_context_data(self, **kwargs):
        """Add view to context - templates access everything via view."""
        context = super().get_context_data(**kwargs)
        context['view'] = self
        return context

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
        return get_menu(self.root_controller, 'main', self.request)


__all__ = ['FormView']
