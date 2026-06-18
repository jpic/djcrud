from djcrud.mvc import Controller


def _get_views_recursive(controller, tag, request, exclude_current=None, **kwargs):
    """
    Recursively find all views matching the tag.

    Returns a flat list of view instances only (no controller submenus).

    Args:
        controller: The controller to search
        tag: Tag to filter by
        request: The current request
        exclude_current: View instance to exclude from results (usually the current view)
        **kwargs: Additional arguments to pass to view.clone()
    """
    views = []

    for v in controller.views:
        # Check if it's a controller (instance or class)
        is_controller_instance = isinstance(v, Controller)
        is_controller_class = isinstance(v, type) and issubclass(v, Controller)

        if is_controller_instance or is_controller_class:
            # Recursively search controller's children for matching views
            views.extend(_get_views_recursive(v, tag, request, exclude_current=exclude_current, **kwargs))
        else:
            # For views, check if view has the tag
            if tag not in getattr(v, 'tags', []):
                continue

            # Clone with any model from parent controller
            clone_kwargs = {'request': request, **kwargs}
            if hasattr(v, 'controller') and v.controller and hasattr(v.controller, 'model'):
                if not hasattr(v, 'model') or v.model is None:
                    clone_kwargs['model'] = v.controller.model

            view = v.clone(**clone_kwargs)()

            # Skip if this is the current view (exclude link to current page)
            if exclude_current is not None:
                # Compare by class name (urlname might not be unique across controllers)
                if view.__class__.__name__ == exclude_current.__class__.__name__:
                    # Also check if they're in the same controller to be sure
                    if getattr(view, '_controller', None) == getattr(exclude_current, '_controller', None):
                        continue

            # has_perm can be a bool attribute or a callable/property
            has_permission = view.has_perm() if callable(view.has_perm) else view.has_perm
            if has_permission:
                views.append(view)

    return views


def get_menu(controller, tag, request, exclude_current=None, **kwargs):
    """
    Return allowed view objects which have ``tag`` in their ``tags``.

    Recursively searches through all controllers to find matching views.

    Returns a flat list of view instances.

    Args:
        controller: The controller to search
        tag: Tag to filter by ('main', 'model', 'object', etc.)
        request: The current request
        exclude_current: Optional view instance to exclude (prevents showing link to current page)
        **kwargs: Additional arguments to pass to view.clone()
    """
    return _get_views_recursive(controller, tag, request, exclude_current=exclude_current, **kwargs)
