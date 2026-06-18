"""
Unpoly integration for djcrud views.

Provides mixins for handling Unpoly modal overlays and progressive enhancement.
"""

from django.http import HttpResponse


class UnpolyModalMixin:
    """
    Mixin to handle Unpoly modal (overlay) responses.

    - On successful form submission: return with X-Up-Location header (closes modal + reloads page)
    - On form errors: re-render form in modal (keeps modal open)

    Usage:
        class MyCreateView(UnpolyModalMixin, CreateView):
            action = 'click->modal#open'
    """

    def is_unpoly_modal(self):
        """Check if the request is from an Unpoly modal/overlay."""
        return self.request.headers.get('X-Up-Mode') in ('modal', 'drawer', 'popup', 'cover')

    def get_template_names(self):
        """
        Return template name with #partial suffix for Unpoly modal requests.

        Django 6's partialdef supports rendering just a partial by appending
        #partial_name to the template name.

        By default, looks for a partial named 'content'. Override the
        partial_name attribute to use a different name.
        """
        templates = super().get_template_names()

        # Check for Unpoly modal request
        if self.is_unpoly_modal():
            # Use partial_name attribute if defined, otherwise default to 'content'
            partial_name = getattr(self, 'partial_name', 'content')
            return [f"{templates[0]}#{partial_name}"]

        return templates

    def form_valid(self, form):
        """
        On successful form submission, return with X-Up-Location for Unpoly modals.

        This tells Unpoly to:
        1. Close the modal/overlay
        2. Reload the page (to show updated data)
        """
        response = super().form_valid(form)

        # For Unpoly modal requests, use X-Up-Location to reload the page
        if self.is_unpoly_modal():
            # Get the current page URL to reload it
            # Use the referrer or just reload the root/list view
            http_response = HttpResponse(status=200)
            http_response['X-Up-Location'] = self.request.META.get('HTTP_REFERER', '/')
            return http_response

        return response

    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE for DeleteView - return with X-Up-Location for Unpoly modals.
        """
        response = super().delete(request, *args, **kwargs)

        # For Unpoly modal requests, use X-Up-Location to reload the page
        if self.is_unpoly_modal():
            http_response = HttpResponse(status=200)
            http_response['X-Up-Location'] = self.request.META.get('HTTP_REFERER', '/')
            return http_response

        return response


__all__ = ['UnpolyModalMixin']
