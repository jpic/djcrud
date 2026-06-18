"""
Generic CRUD views and controllers for models.
"""

from django.contrib.auth.models import User
from djcrud import views, mixins, mvc, attribute


class UserListView(mixins.Tables2Mixin, views.ListView):
    """List view for User model."""
    template_name = 'djcrud/list.html'
    body_class = 'small-margin'
    menus = ['main']
    urlpath = ''

    @attribute.cached
    def title(self):
        """Get title from model's verbose name plural."""
        if self.model:
            return self.model._meta.verbose_name_plural.capitalize()
        return 'List'

    @attribute.cached
    def icon(self):
        """Get icon from model or default to list icon."""
        return getattr(self.model, 'djcrud_icon', 'list')

    @attribute.cached
    def table_class(self):
        """Build django-tables2 table class for User."""
        import django_tables2 as tables

        class UserTable(tables.Table):
            class Meta:
                model = User
                fields = ('username', 'email')

        return UserTable


class UserDetailView(views.DetailView):
    """Detail view for User objects."""
    urlpath = '<int:pk>/'
    urlname = 'detail'
    menus = ['object']
    icon = 'eye'


class UserCreateView(views.CreateView):
    """Create view for User objects."""
    urlpath = 'create'
    urlname = 'create'
    menus = ['model']
    icon = 'plus-circle'


class UserUpdateView(views.UpdateView):
    """Update view for User objects."""
    urlpath = '<int:pk>/edit/'
    urlname = 'edit'
    menus = ['object']
    icon = 'pencil'


class ModelController(mvc.Controller):
    """
    Generic controller for CRUD operations on a model.

    Usage:
        UserController = ModelController.clone(model=User)
        # urlpath and urlname automatically set to 'user'
    """
    model = None

    # Default CRUD views - will be cloned and configured per model
    views = [
        UserListView,
        UserDetailView,
        UserCreateView,
        UserUpdateView,
    ]

    @attribute.getter
    def urlpath(self):
        """Generate URL path from model name if not explicitly set."""
        # Check if urlpath was explicitly set on this class
        if 'urlpath' in self.__class__.__dict__:
            return self.__class__.__dict__['urlpath']
        # Otherwise generate from model name
        if self.model:
            return self.model._meta.model_name
        return ''

    @attribute.getter
    def urlname(self):
        """Generate URL name from model name if not explicitly set."""
        # Check if urlname was explicitly set on this class
        if 'urlname' in self.__class__.__dict__:
            return self.__class__.__dict__['urlname']
        # Otherwise generate from model name
        if self.model:
            return self.model._meta.model_name
        return ''


__all__ = [
    'UserListView',
    'UserDetailView',
    'UserCreateView',
    'UserUpdateView',
    'ModelController',
]
