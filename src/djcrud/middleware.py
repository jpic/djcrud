"""
Middleware for djcrud.
"""


class SiteControllerMiddleware:
    """
    Middleware that adds the site controller to the request.

    This allows views to access the site controller for building menus.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.site_controller = None

    def __call__(self, request):
        # Add site controller to request
        request.site_controller = self.site_controller

        response = self.get_response(request)
        return response

    @classmethod
    def set_site_controller(cls, controller):
        """Set the site controller for this middleware."""
        cls._site_controller = controller
