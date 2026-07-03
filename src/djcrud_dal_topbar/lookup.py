import operator
from functools import reduce

import djcrud
from django.db.models import Q
from djcrud.router import Router


def find_detail_url(model, pk):
    """Return the detail page path for *model*/*pk*, or None."""
    site = djcrud.site
    if not getattr(site, "registry", None):
        return None
    router = _find_model_router(site, model)
    if router is None:
        return None
    detail = router.find_route("detail")
    if detail is None:
        return None
    return detail.reverse(pk)


def iter_model_routers(router):
    """Yield every :class:`~djcrud.ModelRouter` under *router*."""
    for route in router.routes:
        if not isinstance(route, Router):
            continue
        if getattr(type(route), "model", None) is not None:
            yield route
        yield from iter_model_routers(route)


def iter_searchable_list_views(request):
    """Yield list views the user may search (permission + site_search + search_fields)."""
    site = djcrud.site
    if not getattr(site, "registry", None):
        return
    for router in iter_model_routers(site):
        list_route = router.find_route("list")
        if list_route is None:
            continue
        list_view = type(list_route)(request=request)
        if not list_view.has_permission():
            continue
        if not list_view.site_search:
            continue
        if not list_view.search_fields:
            continue
        yield list_view


def get_list_queryset(list_view):
    """Scoped queryset for site search (detail ``view`` permission, not list)."""
    mc = list_view.router.model_router
    model = list_view.model
    perm = f"{model._meta.app_label}.view_{model._meta.model_name}"
    qs = mc.get_queryset(
        user=list_view.request.user,
        model=model,
        action="view",
        perm=perm,
        obj=None,
    )
    if list_view.filter_fields and list_view.filterset is not None:
        qs = list_view.filterset.qs
    return qs


def apply_search(qs, search_fields, term):
    """Filter *qs* with icontains OR across *search_fields* for *term*."""
    if not search_fields or not term:
        return qs
    return qs.filter(
        reduce(
            operator.or_,
            [Q(**{f"{field}__icontains": term}) for field in search_fields],
        )
    ).distinct()


def _find_model_router(router, model):
    for route in router.routes:
        if isinstance(route, Router):
            found = _find_model_router(route, model)
            if found is not None:
                return found
    if getattr(type(router), "model", None) is model:
        return router
    return None