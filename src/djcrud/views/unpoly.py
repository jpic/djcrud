"""
Unpoly integration for djcrud views.

Provides mixin for handling Unpoly requests, modals, and progressive enhancement.

Unpoly automatically extracts matching elements from responses, so we don't need
to render partial templates - just return the full HTML and Unpoly will extract
the target element (e.g., [up-main]) from the response.
"""


class UnpolyMixin:
    """
    Unpoly mixin that adds unpoly context data and handles modal responses.

    Makes Unpoly request headers available in templates as view.unpoly dict:
    - view.unpoly.mode (from X-Up-Mode header: 'modal', 'drawer', etc.)
    - view.unpoly.target (from X-Up-Target header)
    - view.unpoly.layer (from X-Up-Layer header)
    - view.unpoly.fail_mode (from X-Up-Fail-Mode header)
    - view.unpoly.fail_target (from X-Up-Fail-Target header)

    Templates can use this to conditionally render layout elements:
        {% if view.unpoly.mode == 'modal' %}
            <!-- Only render for modal requests -->
        {% endif %}

    For modal/overlay requests, automatically sets X-Up-Accept-Layer and
    X-Up-Location headers on successful form submissions to close the modal
    and navigate to the success URL.

    Usage:
        class MyListView(UnpolyMixin, ListView):
            # Will have unpoly context available
            pass

        class MyCreateView(UnpolyMixin, CreateView):
            # Form will open in modal, close on success
            pass
    """

    def get_next_url(self):
        """
        Get the next URL for redirect after successful form submission.

        Checks in order:
        1. POST data (persists through form resubmissions)
        2. GET parameter (from URL like ?next=/list/)
        3. HTTP Referer header (when opening form directly)
        4. Empty string (no next URL)

        Returns:
            str: The next URL or empty string
        """
        return (
            self.request.POST.get('next', '') or
            self.request.GET.get('next', '') or
            self.request.META.get('HTTP_REFERER', '')
        )

    def dispatch(self, request, *args, **kwargs):
        """
        Add Unpoly headers to view context and handle modal responses.

        For Unpoly modal/overlay requests:
        - On success (redirect): Sets X-Up-Accept-Layer to close overlay and
          X-Up-Location to navigate to the success URL
        - On form errors (200): Unpoly's default behavior keeps modal open
        """
        # Parse Unpoly headers into a dict (converting X-Up-Foo to lowercase)
        self.unpoly = {
            'mode': request.headers.get('X-Up-Mode', ''),
            'target': request.headers.get('X-Up-Target', ''),
            'layer': request.headers.get('X-Up-Layer', ''),
            'fail_mode': request.headers.get('X-Up-Fail-Mode', ''),
            'fail_target': request.headers.get('X-Up-Fail-Target', ''),
        }

        response = super().dispatch(request, *args, **kwargs)

        # Handle Unpoly modal/drawer/popup/cover mode
        if self.unpoly['mode'] in ('modal', 'drawer', 'popup', 'cover'):
            if response.status_code == 302:
                # Success - form submitted, redirect to the page that opened the modal
                # Get next URL using get_next_url method
                next_url = self.get_next_url()

                # Redirect to next URL instead of success_url
                if next_url:
                    response['Location'] = next_url

                # Use X-Up-Accept-Layer to close the modal/overlay
                response['X-Up-Accept-Layer'] = 'null'
                # Set X-Up-Location to navigate to the next URL
                response['X-Up-Location'] = response['Location']
            # For status 200 (form errors), Unpoly's default behavior keeps modal open

        return response


__all__ = ['UnpolyMixin']
