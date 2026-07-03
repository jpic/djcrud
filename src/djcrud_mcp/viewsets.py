from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from djcrud_drf.viewsets import ModelViewSet


def discover_viewsets() -> list[type[ModelViewSet]]:
    """Return registered :class:`~djcrud_drf.ModelViewSet` classes."""
    import djcrud_drf

    djcrud_drf.site.build()
    return list(djcrud_drf.site._registrations)


def api_path_for(viewset_class: type[ModelViewSet]) -> str:
    """API collection path for a registered ViewSet."""
    model = viewset_class.model
    return f"/api/{model.__name__.lower()}/"


def model_name_for(viewset_class: type[ModelViewSet]) -> str:
    return viewset_class.model.__name__.lower()