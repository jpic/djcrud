def get_menu(controller, name, request, **kwargs):
    """
    Return allowed view objects which have ``name`` in their ``menus``.

    For each view class in controller.views which have ``name`` in their
    ``menus`` attribute, instanciate the view class with ``request`` and
    kwargs, call ``has_perm()`` on it.

    Return the list of view instances for which ``has_perm()`` has passed.
    """
    views = []

    for v in controller.views:
        if name not in getattr(v, 'menus', []):
            continue

        view = v.clone(request=request, **kwargs)()

        if view.has_perm():
            views.append(view)

    return views
