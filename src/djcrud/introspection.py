import djcrud

from .router import Router


def compute_fullurlpath(route):
    """Return the URL path for *route* by walking router ancestors."""
    try:
        return route.url
    except Exception:
        parts = []
        current = route
        while current is not None:
            segment = getattr(current, "urlpath", "")
            if segment:
                parts.insert(0, segment.strip("/"))
            current = getattr(current, "router", None)
        if not parts:
            return "/"
        return "/" + "/".join(parts) + "/"


def walk_leaf_views(router):
    """Yield built view route instances under *router*."""
    routes = getattr(router, "routes", None)
    if routes is None:
        return
    for route in routes:
        if isinstance(route, Router):
            yield from walk_leaf_views(route)
        else:
            yield route


def walk_model_routers(router):
    """Yield :class:`~djcrud.ModelRouter` instances in the tree."""
    if getattr(type(router), "model", None) is not None:
        yield router
    routes = getattr(router, "routes", None)
    if routes is None:
        return
    for route in routes:
        if isinstance(route, Router):
            yield from walk_model_routers(route)


def get_built_site(site):
    """Return *site* after :meth:`~djcrud.Site.build` if needed."""
    if not hasattr(site, "registry"):
        site.build()
    return site


def instantiate_view(route, request):
    """Return a view instance bound to *request* from a built route."""
    view = type(route)(request=request)
    view.args = ()
    view.kwargs = {}
    return view
