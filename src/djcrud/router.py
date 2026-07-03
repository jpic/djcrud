import re

from django.urls import include, path

from .clonable import Clonable
from .permission import call_with_context
from .permissions import get_queryset as registry_get_queryset
from .permissions import has_permission as registry_has_permission
from .registry import Registry
from .route import Route


def _camel_to_kebab(name):
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s1).lower()


def model_router_codename(router_cls):
    """URL segment from a :class:`~djcrud.ModelRouter` subclass name.

    ``SecuredDocumentRouter`` → ``secured-document``; plain ``ModelRouter``
    (or ``{Model}Router``) falls back to :attr:`~djcrud.ModelRouter.model`.
    """
    name = router_cls.__name__
    if name.endswith("Router"):
        stem = name[: -len("Router")]
    else:
        stem = name
    model = getattr(router_cls, "model", None)
    if not stem or stem == "Model":
        if model is not None:
            return model.__name__.lower()
        return stem.lower() or "model"
    if model is not None and stem == model.__name__:
        return model.__name__.lower()
    return _camel_to_kebab(stem)


class RoutesDescriptor:
    """Return the built registry on instances after build(), else the declaration list."""

    def __get__(self, instance, owner):
        obj = instance or owner
        return getattr(obj, "registry", obj._declaration)


class RouterMeta(type):
    """Move class-body ``routes = [...]`` into ``_declaration``; wire ``routes`` as the accessor."""

    def __new__(mcs, name, bases, namespace):
        routes = namespace.pop("routes", None)
        cls = super().__new__(mcs, name, bases, namespace)
        if routes is None:
            cls._declaration = list(bases[0]._declaration) if bases else []
        else:
            cls._declaration = list(routes)
        cls.routes = RoutesDescriptor()
        return cls


class Router(Clonable, Route, metaclass=RouterMeta):
    """Group child routes under a shared URL prefix.

    Attributes:
        routes: Declared child routes (classes or instances). Before
            :meth:`build`, this is the declaration list; afterward it is a
            :class:`~djcrud.registry.Registry` of built route instances.
        icon (str): Bootstrap Icons name for the sidebar entry. Navigation
            list views inherit this when they do not set their own ``icon``.
        color (str): Bulma color name for the sidebar icon (``primary``,
            ``info``, …).
    """

    routes = []

    def build(self):
        """Instantiate child routes into a :class:`~djcrud.registry.Registry`."""
        self.registry = Registry(self, list(type(self)._declaration))
        for route in self.routes:
            if build := getattr(route, "build", None):
                build()
        return self

    @property
    def codename(self):
        """URL segment with the ``router`` suffix removed from the class name."""
        return super().codename.replace("router", "")

    def find_route(self, codename):
        """Walk up the router tree and return the first route named *codename*."""
        current = self
        while current is not None:
            try:
                return current.routes[codename]
            except KeyError:
                current = getattr(current, "router", None)
        return None

    @property
    def model_router(self):
        """Nearest ancestor :class:`~djcrud.ModelRouter`, or ``None``."""
        current = self
        while current is not None:
            if getattr(type(current), "model", None) is not None:
                return current
            current = getattr(current, "router", None)
        return None

    def _permission_context(self, *, user, model, action, perm, obj=None):
        return dict(
            user=user,
            model=model,
            action=action,
            perm=perm,
            obj=obj,
        )

    def has_permission(self, *, user, model, action, perm, obj=None):
        """Delegate permission checks to the nearest :class:`~djcrud.ModelRouter`."""
        ctx = self._permission_context(
            user=user,
            model=model,
            action=action,
            perm=perm,
            obj=obj,
        )
        model_router = self.model_router
        if model_router is None:
            return registry_has_permission(**ctx)
        return call_with_context(model_router.has_permission, ctx)

    def get_queryset(self, *, user, model, action, perm, obj=None):
        """Delegate queryset scoping to the nearest :class:`~djcrud.ModelRouter`."""
        ctx = self._permission_context(
            user=user,
            model=model,
            action=action,
            perm=perm,
            obj=obj,
        )
        model_router = self.model_router
        if model_router is None:
            return registry_get_queryset(**ctx)
        return call_with_context(model_router.get_queryset, ctx)

    def get_tagged_views(self, tag, **kwargs):
        """Return permitted child views whose ``tags`` contain *tag*."""

        def process(router):
            views = []
            for route in router.routes:
                if isinstance(route, Router):
                    views += process(route)
                    continue

                if tag not in getattr(route, "tags", []):
                    continue

                view = type(route)(**kwargs)
                if view.has_permission():
                    views.append(view)
            return views

        return process(self)

    @property
    def root(self):
        """Topmost router ancestor."""
        router = getattr(self, "router", None)
        if not router:
            return self

        while hasattr(router, "router"):
            router = router.router
        return router

    @property
    def urlpatterns(self):
        """Include child :attr:`~djcrud.route.Route.urlpatterns` under this prefix."""
        patterns = []

        for route in self.routes:
            patterns += route.urlpatterns

        return [
            path(
                self.urlpath,
                include(
                    (patterns, self.urlname),
                    namespace=self.urlname,
                ),
            )
        ]
