"""djcrud public API.

:data:`site` is the root :class:`Site` router. Append routers to
``site.routes`` in each app's ``djcrud.py`` module; :meth:`Site.build` imports
those modules via autodiscovery (like Django admin's ``admin.py``).
"""

from django.utils.module_loading import autodiscover_modules

from .permissions import (
    add_perm,
    add_queryset,
    add_search,
    all_of,
    any_of,
    authenticated,
    get_queryset,
    has_permission,
    has_site_permission,
    is_owner,
    owner,
    perm_code,
    remove_perm,
    remove_queryset,
    remove_search,
    superuser,
)
from .router import Router
from .view import View
from .model import ModelMixin
from .views import generic


class ModelRouter(ModelMixin, Router):
    """CRUD router for a single Django model.

    Attributes:
        routes: Default list, detail, create, update, delete, and bulk-delete
            views. Extend with ``ModelRouter.routes + [MyView]`` or
            replace entries by codename (see :class:`~djcrud.registry.Registry`).
        model: Django model class managed by this router.
        icon (str): Bootstrap Icons name for the navigation list view.
        color (str): Bulma color for the navigation list icon.
    """

    routes = [
        generic.ListView,
        generic.DetailView,
        generic.UpdateView,
        generic.DeleteView,
        generic.DeleteObjectsView,
        generic.CreateView,
    ]

    @property
    def codename(self):
        """URL segment from :attr:`model` name (lowercase)."""
        return self.model.__name__.lower()

    def has_permission(self, *, user, model, action, perm, obj=None):
        """Return whether *user* may perform *action* via the permission registry."""
        return has_permission(
            user=user,
            model=model,
            action=action,
            perm=perm,
            obj=obj,
        )

    def get_queryset(self, *, user, model, action, perm, obj=None):
        """Return rows visible to *user* via the permission registry, then all rows."""
        return get_queryset(
            user=user,
            model=model,
            action=action,
            perm=perm,
            obj=obj,
        )


class Home(generic.TemplateView):
    """Site root page at ``/``."""

    urlpath = ""

    def has_permission(self):
        """Allow anonymous access to the home page."""
        return True


class Site(Router):
    """Root site router; autodiscovers ``djcrud.py`` in installed apps."""

    urlpath = ""
    routes = [
        Home,
    ]

    def autodiscover(self):
        """Import ``djcrud`` modules from every installed app."""
        autodiscover_modules("djcrud")
        return self

    def build(self):
        """Autodiscover app routes, then build the route registry."""
        self.autodiscover()
        return super().build()


site = Site()
