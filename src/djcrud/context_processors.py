"""
Context processors for djcrud.

Provides common context variables to all templates.
"""


def djcrud_context(request):
    """
    Add djcrud-specific context variables.

    This adds the site controller to the context so templates can build menus.
    """
    # Get the site controller from the URL resolver
    # This will be set by the URLconf
    site_controller = getattr(request, 'site_controller', None)

    return {
        'site_controller': site_controller,
    }
