"""
TemplateView for rendering static templates.
"""

from django.views.generic import TemplateView as DjangoTemplateView
from djcrud.mvc import View
from djcrud import attribute


class TemplateView(View, DjangoTemplateView):
    """
    Render a template with context.

    This is useful for static pages like home, about, etc.

    Attributes:
        template_name: Template to render
        title: Page title (optional)
        title_heading: Heading text (optional, defaults to title)
        icon: Icon name (optional)

    Example:
        HomeView = TemplateView.clone(
            template_name='home.html',
            title='Welcome',
            icon='home',
            urlpath='',
            urlname='home',
            has_perm=True,  # Public page
        )
    """

    @attribute.getter
    def title(self):
        """Return page title.

        The title() getter does all the work (replaces previous get_title()).
        """
        # If a title was explicitly set on the instance/class (e.g. via clone), use it.
        # Otherwise return default. The @attribute.getter on title() itself is handled
        # by the descriptor system without recursion.
        if hasattr(type(self), 'title') and not callable(getattr(type(self), 'title', None)):
            # title is a plain attribute (from clone or subclass)
            return getattr(self, 'title')
        return 'Home'

    @attribute.cached
    def title_heading(self):
        """Return heading text."""
        if hasattr(self, '_title_heading'):
            heading = self._title_heading() if callable(self._title_heading) else self._title_heading
            # Empty string means no heading
            if heading == '':
                return ''
            return heading
        # title() is now the @getter; call via attribute access
        return self.title

    def get_context_data(self, **kwargs):
        """Add view to context - templates access everything via view."""
        context = super().get_context_data(**kwargs)
        context['view'] = self
        return context

    @attribute.cached
    def main_menu(self):
        """Get main navigation menu."""
        from djcrud.menu import get_menu
        if not self.root_controller:
            return []
        return get_menu(self.root_controller, 'main', self.request, exclude_current=self)


__all__ = ['TemplateView']
