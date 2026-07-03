from django.core.exceptions import ImproperlyConfigured

from .permission import call_with_context


class ModelMixin:
    """Resolve ``model`` and scoped querysets from the enclosing router.

    Views nested under a :class:`~djcrud.ModelRouter` inherit its ``model``
    and :meth:`~djcrud.ModelRouter.get_queryset` scoping.
    """

    @property
    def title(self):
        """Human-readable label with the model class name removed."""
        return super().title.replace(self.model.__name__, "")

    @property
    def codename(self):
        """URL segment with the model name removed from the default codename."""
        return super().codename.replace(self.model.__name__.lower(), "")

    @property
    def model(self):
        """Django model from the nearest ancestor :class:`~djcrud.ModelRouter`."""
        current = self.router
        while not hasattr(current, "model"):
            try:
                current = current.router
            except AttributeError:
                raise Exception("Model not found")
        return current.model

    @property
    def model_meta(self):
        """``model._meta`` exposed for templates (``._meta`` is blocked)."""
        return self.model._meta

    def _router_queryset(self):
        if self.router:
            ctx = self.permission_context()
            router = self.router
            get_queryset = getattr(router, "get_queryset", None)
            if get_queryset is None:
                router = getattr(router, "model_router", router)
            return call_with_context(router.get_queryset, ctx)
        if self.model:
            return self.model._default_manager.all()
        raise ImproperlyConfigured(
            "%(cls)s is missing a QuerySet. Define %(cls)s.model, "
            "%(cls)s.queryset, or override %(cls)s.get_queryset()."
            % {
                "cls": self.__class__.__name__,
            }
        )

    def get_object_queryset(self):
        """Scoped model rows for resolving ``self.object`` from the URL."""
        return self._router_queryset()

    def get_queryset(self):
        """Scoped queryset for list and action views."""
        return self._router_queryset()

    def breadcrumbs(self, with_self=True):
        """Breadcrumb trail via list view, optionally including this view."""
        crumbs = []
        list_route = self.router.find_route("list")
        if list_route:
            list_view = type(list_route)(request=self.request)
            if list_view.has_permission():
                crumbs.append(list_view)
        if with_self:
            crumbs.append(self)
        return crumbs
