"""
Unpoly integration for djcrud views.

Provides mixins for handling Unpoly modal overlays and progressive enhancement.

Unpoly automatically extracts matching elements from responses, so we don't need
to render partial templates - just return the full HTML and Unpoly will extract
the target element (e.g., [up-main]) from the response.
"""


class UnpolyModalMixin:
    """
    Mixin to handle Unpoly modal (overlay) responses.

    - On successful form submission: sets X-Up-Location header (closes modal + reloads page)
    - On form errors: re-render form in modal (keeps modal open)

    Usage:
        class MyCreateView(UnpolyModalMixin, CreateView):
            # Form will open in modal, close on success
            pass
    """

    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to set X-Up-Location on successful responses.

        For Unpoly modal/overlay requests, successful form submissions should
        return X-Up-Location header to close the modal and reload the page.
        """
        response = super().dispatch(request, *args, **kwargs)

        # For successful responses in Unpoly modal mode, set X-Up-Location
        up_mode = request.headers.get('X-Up-Mode', '')
        if up_mode in ('modal', 'drawer', 'popup', 'cover'):
            # Only set X-Up-Location for successful redirects (status 302)
            # or successful responses (status 200 after form/delete)
            if response.status_code in (200, 302):
                # Build the reload URL: current path + query string
                url = request.path_info
                if request.GET:
                    url += '?' + request.GET.urlencode()
                response['X-Up-Location'] = url

        return response


__all__ = ['UnpolyModalMixin']
