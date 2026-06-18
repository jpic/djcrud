"""
Unpoly integration for djcrud views.

Provides mixins for handling Unpoly modal overlays and progressive enhancement.
"""

from django.http import HttpResponse
from django.template.loader import get_template
from django.template import Context


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

    def _find_partialdef_node(self, nodelist, partial_name):
        """Recursively search for a partialdef node with the given name."""
        for node in nodelist:
            # Check if this node is a partialdef with the right name
            if hasattr(node, 'partial_name') and node.partial_name == partial_name:
                return node
            # Handle ExtendsNode - load parent template and search there
            if type(node).__name__ == 'ExtendsNode':
                # The ExtendsNode has the parent template name
                if hasattr(node, 'parent_name'):
                    parent_template_name = node.parent_name.resolve({})
                    parent_template = get_template(parent_template_name)
                    result = self._find_partialdef_node(parent_template.template.nodelist, partial_name)
                    if result:
                        return result
            # Recursively search child nodelists
            if hasattr(node, 'nodelist'):
                result = self._find_partialdef_node(node.nodelist, partial_name)
                if result:
                    return result
            # Check other nodelist attributes (e.g., nodelist_true, nodelist_false for if nodes)
            for attr in dir(node):
                if attr.startswith('nodelist_'):
                    child_nodelist = getattr(node, attr, None)
                    if child_nodelist:
                        result = self._find_partialdef_node(child_nodelist, partial_name)
                        if result:
                            return result
        return None

    def render_to_response(self, context, **response_kwargs):
        """
        Render response, using partial content for Unpoly modal requests.

        For Unpoly modal requests, renders just the partial block by finding
        and rendering the partial definition in the template.
        """
        if self.is_unpoly_modal():
            partial_name = getattr(self, 'partial_name', 'content')
            template_name = self.get_template_names()[0]

            # Load the template
            template = get_template(template_name)

            # Find the partialdef node recursively
            partial_node = self._find_partialdef_node(template.template.nodelist, partial_name)

            if partial_node:
                # Render just the partial node
                ctx = Context(context)
                ctx.update(context)
                ctx.update({'request': self.request})
                rendered = partial_node.nodelist.render(ctx)
                return HttpResponse(rendered, **response_kwargs)

        return super().render_to_response(context, **response_kwargs)

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
