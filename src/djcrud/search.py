"""Site search registry.

Opt models into the global site search (used by djcrud_dal_topbar etc.).

Search visibility reuses the "view" queryset scoping already registered
via djcrud.permissions.add_queryset.
"""

from __future__ import annotations

_SEARCH_ENABLED: set[tuple[str, str]] = set()


def _model_key(model):
    return model._meta.app_label, model._meta.model_name


def add_search(model):
    """Opt a model into site-wide search.

    Row visibility uses the same ``view`` queryset scoping already
    registered via :func:`djcrud.permissions.add_queryset`.
    """
    if not _is_model(model):
        raise TypeError("add_search() expects a model class")
    _SEARCH_ENABLED.add(_model_key(model))


def remove_search(model):
    """Remove a model from site-wide search."""
    if not _is_model(model):
        raise TypeError("remove_search() expects a model class")
    _SEARCH_ENABLED.discard(_model_key(model))


def is_search_enabled(model):
    """Return whether *model* is opted into site search."""
    return _model_key(model) in _SEARCH_ENABLED


def clear():
    """Remove all registered search models (primarily for tests)."""
    _SEARCH_ENABLED.clear()


def _is_model(target):
    return isinstance(target, type) and hasattr(target, "_meta")
