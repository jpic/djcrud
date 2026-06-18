from djcrud.mvc import Controller


def _get_views_recursive(controller, name, request, **kwargs):
    """
    Recursively find all views matching the menu name.

    Returns a flat list of view instances only (no controller submenus).
    """
    views = []

    for v in controller.views:
        # Check if it's a controller (instance or class)
        is_controller_instance = isinstance(v, Controller)
        is_controller_class = isinstance(v, type) and issubclass(v, Controller)

        if is_controller_instance or is_controller_class:
            # Recursively search controller's children for matching views
            views.extend(_get_views_recursive(v, name, request, **kwargs))
        else:
            # For views, check if view has the menu name
            if name not in getattr(v, 'menus', []):
                continue

            # Clone with any model from parent controller
            clone_kwargs = {'request': request, **kwargs}
            if hasattr(v, 'controller') and v.controller and hasattr(v.controller, 'model'):
                if not hasattr(v, 'model') or v.model is None:
                    clone_kwargs['model'] = v.controller.model

            view = v.clone(**clone_kwargs)()

            # has_perm can be a bool attribute or a callable/property
            has_permission = view.has_perm() if callable(view.has_perm) else view.has_perm
            if has_permission:
                views.append(view)

    return views


def get_menu(controller, name, request, **kwargs):
    """
    Return allowed view objects which have ``name`` in their ``menus``.

    Recursively searches through all controllers to find matching views.

    Returns a flat list of view instances.
    """
    return _get_views_recursive(controller, name, request, **kwargs)
