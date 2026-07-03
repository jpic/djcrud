"""Permission and queryset registry for djcrud.

Register checks in each app's ``djcrud.py`` via :func:`add_perm` and
:func:`add_queryset`; :meth:`~djcrud.Site.build` imports those modules
automatically (same as ``site.routes.append``).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

_PERM_CHECKS: dict[tuple[str, str, str | None], Callable[..., bool]] = {}
_QUERYSET_SCOPERS: dict[tuple[str, str, str | None], Callable[..., Any]] = {}
_PERM_STRING_CHECKS: dict[str, Callable[..., bool]] = {}
_SEARCH_ENABLED: set[tuple[str, str]] = set()


def perm_code(model, action):
    """Return the Django permission full code for *model* and *action*."""
    return f"{model._meta.app_label}.{action}_{model._meta.model_name}"


def _model_key(model):
    return model._meta.app_label, model._meta.model_name


def _perm_key(model, action):
    app_label, model_name = _model_key(model)
    return app_label, model_name, action


def _store_perm(model, action, check):
    _PERM_CHECKS[_perm_key(model, action)] = check


def _store_queryset(model, action, scoper):
    _QUERYSET_SCOPERS[_perm_key(model, action)] = scoper


def _split_names(value):
    """Split comma-separated registry keys (actions or full permission codes)."""
    if not isinstance(value, str) or "," not in value:
        return [value]
    return [part.strip() for part in value.split(",") if part.strip()]


def add_perm(target, action=None, *, check):
    """Register a permission grant for *target*.

    *target* may be a model class, a full permission string
    (``\"app_label.action_model\"``), or a router class/instance (with *action*
    required).

    *action* may be a comma-separated list (``\"view,add,publish\"``) to bind the
    same *check* to several shortcodes at once.  A string *target* with ``.`` may
    also list several full codes: ``\"app.view_item,app.add_item\"``.

    *check* receives ``(user, *, model, action, perm, obj)`` and returns
    a boolean.  A ``True`` result grants access in addition to Django perms.
    """
    if isinstance(target, str):
        if action is not None:
            raise TypeError("add_perm(string, action, ...) is not supported")
        for perm_name in _split_names(target):
            _PERM_STRING_CHECKS[perm_name] = check
        return
    if _is_model(target):
        for act in _split_names(action):
            _store_perm(target, act, check)
        return
    if action is None:
        raise TypeError("add_perm(router, action, check=...) requires action")
    model = _model_from_router(target)
    for act in _split_names(action):
        _store_perm(model, act, check)


def add_queryset(model, action=None, *, scoper):
    """Register row visibility for *model* (optionally per *action*).

    *action* may be comma-separated to register the same *scoper* for several
    shortcodes.

    *scoper* receives ``(user, *, model, action, perm, obj)`` and
    returns a :class:`~django.db.models.QuerySet`.
    """
    for act in _split_names(action):
        _store_queryset(model, act, scoper)


def remove_perm(target, action=None):
    """Remove a registered permission check."""
    if isinstance(target, str) and "." in target:
        for perm_name in _split_names(target):
            _PERM_STRING_CHECKS.pop(perm_name, None)
        return
    model = target if _is_model(target) else _model_from_router(target)
    for act in _split_names(action):
        _PERM_CHECKS.pop(_perm_key(model, act), None)


def remove_queryset(model, action=None):
    """Remove a registered queryset scoper."""
    for act in _split_names(action):
        _QUERYSET_SCOPERS.pop(_perm_key(model, act), None)


def add_search(model):
    """Opt a model into site-wide search.

    Row visibility uses the same ``view`` queryset scoping already
    registered via :func:`add_queryset`.
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
    """Remove all registered permission and queryset handlers (tests)."""
    _PERM_CHECKS.clear()
    _QUERYSET_SCOPERS.clear()
    _PERM_STRING_CHECKS.clear()
    _SEARCH_ENABLED.clear()


def _is_model(target):
    return isinstance(target, type) and hasattr(target, "_meta")


def _model_from_router(router):
    cls = router if isinstance(router, type) else type(router)
    model = getattr(cls, "model", None)
    if model is None:
        raise TypeError(f"{cls!r} has no model attribute")
    return model


def _lookup_keys(model, action):
    app_label, model_name = _model_key(model)
    return (
        (app_label, model_name, action),
        (app_label, model_name, None),
    )


def _lookup_perm(model, action, perm):
    for key in _lookup_keys(model, action):
        check = _PERM_CHECKS.get(key)
        if check is not None:
            return check
    return _PERM_STRING_CHECKS.get(perm)


def _lookup_scoper(model, action):
    for key in _lookup_keys(model, action):
        scoper = _QUERYSET_SCOPERS.get(key)
        if scoper is not None:
            return scoper
    return None


def _invoke(handler, user, *, model, action, perm, obj):
    return handler(
        user,
        model=model,
        action=action,
        perm=perm,
        obj=obj,
    )


def has_site_permission(*, user, perm, action="view", model=None, obj=None):
    """Check access for views without a model (superuser or ``add_perm`` string).

    Used by site-level views such as :class:`~djcrud.views.spa.SPAView`. Until
    you register a matching permission string with :func:`add_perm`, only
    superusers pass.
    """
    if user.is_superuser:
        return True
    check = _PERM_STRING_CHECKS.get(perm)
    if check is not None:
        return _invoke(
            check,
            user,
            model=model,
            action=action,
            perm=perm,
            obj=obj,
        )
    return False


def has_permission(*, user, model, action, perm, obj=None):
    """Return whether *user* may perform *action* on *model*."""
    if model is None:
        return has_site_permission(
            user=user,
            perm=perm,
            action=action,
            model=model,
            obj=obj,
        )
    check = _lookup_perm(model, action, perm)
    if check is not None and _invoke(
        check,
        user,
        model=model,
        action=action,
        perm=perm,
        obj=obj,
    ):
        return True
    if obj is not None and user.has_perm(perm, obj):
        return True
    return user.has_perm(perm)


def get_queryset(*, user, model, action, perm, obj=None):
    """Return rows visible to *user* for *action* on *model*."""
    scoper = _lookup_scoper(model, action)
    if scoper is not None:
        return _invoke(
            scoper,
            user,
            model=model,
            action=action,
            perm=perm,
            obj=obj,
        )
    return model._default_manager.all()


def authenticated(user, **ctx):
    """Predicate: user is authenticated."""
    return user.is_authenticated


def superuser(user, **ctx):
    """Predicate: user is a superuser."""
    return user.is_superuser


def is_owner(user, *, obj, owner_field="owner_id", **ctx):
    """Predicate: user owns *obj* (compare *owner_field* to ``user.pk``)."""
    if obj is None:
        return False
    value = obj if owner_field == "pk" else getattr(obj, owner_field, None)
    return value == user.pk


owner = is_owner


def any_of(*checks):
    """Combine predicates with OR (short-circuit)."""

    def combined(user, **ctx):
        for check in checks:
            if check(user, **ctx):
                return True
        return False

    return combined


def all_of(*checks):
    """Combine predicates with AND (short-circuit)."""

    def combined(user, **ctx):
        for check in checks:
            if not check(user, **ctx):
                return False
        return True

    return combined
