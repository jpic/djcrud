import djcrud
from djcrud.router import Router


def find_autocomplete_url(model):
    """Return urlfullname for *model*'s autocomplete route, or None."""
    site = djcrud.site
    if not getattr(site, "registry", None):
        return None
    return _find_in_tree(site, model)


def _find_in_tree(router, model):
    for route in router.routes:
        if isinstance(route, Router):
            url = _find_in_tree(route, model)
            if url:
                return url
    if getattr(type(router), "model", None) is model:
        autocomplete = router.find_route("autocomplete")
        if autocomplete is not None:
            return autocomplete.urlfullname
    return None
