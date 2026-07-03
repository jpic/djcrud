"""Optional DRF API layer for djcrud.

Register :class:`ModelViewSet` subclasses on :data:`site` from your app's
``djcrud.py`` (or any module imported from there).

Install with ``pip install djcrud[drf]`` and add ``djcrud_drf`` to
``INSTALLED_APPS``.
"""

from django.urls import include, path

from .spectacular import spectacular_settings
from .log import LogMixin
from .viewsets import ModelViewSet, RegistryViewSet


class ApiRouter:
    """DRF :class:`~rest_framework.routers.DefaultRouter` wrapper."""

    def __init__(self):
        self._viewsets = []
        self._registry_viewsets = []
        self._drf_router = None

    def register(self, viewset_class):
        if viewset_class not in self._viewsets:
            self._viewsets.append(viewset_class)

    def register_registry(self, viewset_class):
        if viewset_class not in self._registry_viewsets:
            self._registry_viewsets.append(viewset_class)

    def build(self):
        if self._drf_router is not None:
            return self
        from rest_framework.routers import DefaultRouter

        self._drf_router = DefaultRouter()
        for viewset_class in self._viewsets:
            router = viewset_class._built_router
            self._drf_router.register(
                router.urlpath,
                viewset_class,
                basename=viewset_class.model._meta.model_name,
            )
        for viewset_class in self._registry_viewsets:
            self._drf_router.register(
                viewset_class.registry_prefix.strip("/"),
                viewset_class,
                basename=viewset_class.registry_basename,
            )
        return self

    @property
    def urlpatterns(self):
        self.build()
        return list(self._drf_router.urls)


class DrfSite:
    """Root API site at ``/api/``."""

    urlpath = "api/"

    def __init__(self):
        self._registrations = []
        self._registry_registrations = []
        self._built = False

    @property
    def urlname(self):
        return "api"

    def register(self, viewset_class):
        if issubclass(viewset_class, RegistryViewSet):
            if viewset_class not in self._registry_registrations:
                self._registry_registrations.append(viewset_class)
            return
        if viewset_class not in self._registrations:
            self._registrations.append(viewset_class)

    def build(self):
        if self._built:
            return self
        for viewset_class in self._registrations:
            viewset_class._built_router = viewset_class.build_router()
        router.build()
        api._viewsets.clear()
        api._registry_viewsets.clear()
        api._drf_router = None
        for viewset_class in self._registrations:
            api.register(viewset_class)
        for viewset_class in self._registry_registrations:
            api.register_registry(viewset_class)
        api.build()
        self._built = True
        return self

    def schema_urlpatterns(self):
        try:
            from drf_spectacular.views import (
                SpectacularAPIView,
                SpectacularSwaggerView,
            )
        except ImportError:
            return []
        return [
            path("schema/", SpectacularAPIView.as_view(), name="schema"),
            path(
                "docs/",
                SpectacularSwaggerView.as_view(url_name="api:schema"),
                name="docs",
            ),
        ]

    def login_urlpatterns(self):
        from djcrud_api.login import uses_drf_login

        if not uses_drf_login():
            return []
        from djcrud_api.drf_views import login_urlpattern

        return [login_urlpattern()]

    @property
    def urlpatterns(self):
        self.build()
        patterns = []
        patterns += self.login_urlpatterns()
        login_router = get_router()
        login_router.build()
        for route in login_router.routes:
            patterns += route.urlpatterns
        patterns += api.urlpatterns
        patterns += self.schema_urlpatterns()
        return [
            path(
                self.urlpath,
                include((patterns, self.urlname), namespace=self.urlname),
            )
        ]


def _make_api_router():
    from djcrud_api.views import ApiRouter as LoginRouter

    return LoginRouter()


_router = None


def get_router():
    """Return the login API router, creating it after Django apps are ready."""
    global _router
    if _router is None:
        _router = _make_api_router()
    return _router


class _LazyRouterProxy:
    def __getattr__(self, name):
        return getattr(get_router(), name)


site = DrfSite()
api = ApiRouter()
router = _LazyRouterProxy()