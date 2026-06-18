"""
Generic CRUD views and controllers for models.
"""

from django.contrib.auth.models import User as DjangoUser
from djcrud import mvc, attribute
# Generic views live in djcrud.views.generic (not __init__ or the old crud module).
# The User*View classes below are thin wrappers that add User-specific
# configuration (menus, urlpath, fields='__all__').
from djcrud.views import generic
from djcrud.views.tables2 import Tables2Mixin


class UserListView(Tables2Mixin, generic.ListView):
    """List view for User model (thin wrapper over generic ListView)."""
    template_name = 'djcrud/list.html'
    body_class = 'small-margin'
    menus = ['main']
    urlpath = ''
    urlname = 'list'
    has_perm = True

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

    # table_class now provided by Tables2Mixin using table_fields getter
    # table_fields should be set via .clone(table_fields=[...]) when instantiating
    # (no longer a custom UserTable; uses dynamic Table with model + fields)


class UserDetailView(generic.DetailView):
    """Detail view for User objects (thin wrapper over generic DetailView).

    Note: get_absolute_url is on the custom model in djcrud_auth/models.py instead.
    Per user guidance: "adding get_absolute_url to the crud is useless".
    """
    urlpath = '<int:pk>/'
    urlname = 'detail'
    menus = ['object']
    icon = 'eye'
    has_perm = True


class UserCreateView(generic.CreateView):
    """Create view for User objects (thin wrapper over generic CreateView).

    Uses fields='__all__' (the generic case). For djcrud_auth we override via
    .clone(form_class=UserCreationForm).
    """
    urlpath = 'create'
    urlname = 'create'
    menus = ['model']
    icon = 'plus-circle'
    fields = '__all__'
    has_perm = True


class UserUpdateView(generic.UpdateView):
    """Update view for User objects (thin wrapper over generic UpdateView).

    Uses fields='__all__' (the generic case). For djcrud_auth we override via
    .clone(form_class=UserChangeForm).
    """
    urlpath = '<int:pk>/edit/'
    urlname = 'edit'
    menus = ['object']
    icon = 'pencil'
    fields = '__all__'
    has_perm = True


class UserDeleteView(generic.DeleteView):
    """Delete view for User objects (thin wrapper over generic DeleteView)."""
    urlpath = '<int:pk>/delete/'
    urlname = 'delete'
    menus = ['object']
    icon = 'trash'
    has_perm = True


class ModelController(mvc.Controller):
    """
    Generic controller for CRUD operations on a model.

    Usage:
        ProductController = ModelController.clone(model=Product)
        # or for special cases:
        UserController = ModelController.clone(
            model=DjangoUser,  # avoid name clash with custom User in djcrud_auth.models
            views=[UserListView, UserDetailView, UserCreateView.clone(...), ...]
        )

    The default views list uses the thin User*View wrappers (which inherit from
    the generic ones in djcrud.views.generic). This module still has a User
    dependency only for the auth example; the generic views live in views/generic.py.
    """
    model = None

    # Default CRUD views - will be cloned and configured per model.
    # For special models like User, the caller (djcrud_auth/crud.py) clones
    # the Create/Update views with a custom form_class (see comment there).
    views = [
        UserListView,
        UserDetailView,
        UserCreateView,
        UserUpdateView,
        UserDeleteView,
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
        """Generate URL name from model name if not explicitly set.

        Uses model._meta.model_name (e.g. 'user' for User). This works with the
        updated slugify logic in mvc.View.urlname and mvc.Controller.urlname.
        See tests/test_url_consistency.py for 'auth:user:list' reverse examples.
        """
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
    # The generic views are re-exported from djcrud.views (which pulls from .generic)
]
