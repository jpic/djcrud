from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from djcrud_drf.viewsets import RegistryViewSet

from djcrud_mcp.site import site
from djcrud_mcp.viewsets import api_path_for, discover_viewsets, model_name_for


class McpProfileViewSet(RegistryViewSet):
    registry_prefix = "mcp/profiles"
    registry_basename = "mcp-profile"
    permission_classes = [AllowAny]
    authentication_classes = []

    def list(self, request):
        del request
        return Response(
            {
                "profiles": site.list_keys(),
                "default": site.default_key(),
            }
        )

    def retrieve(self, request, pk=None):
        del request
        return Response(site.get_profile(pk).to_dict())


class McpViewsetCatalogViewSet(RegistryViewSet):
    registry_prefix = "mcp/viewsets"
    registry_basename = "mcp-viewset"
    permission_classes = [AllowAny]
    authentication_classes = []

    def list(self, request):
        del request
        viewsets = discover_viewsets()
        return Response(
            {
                "viewsets": [
                    {
                        "model": model_name_for(viewset),
                        "prefix": api_path_for(viewset),
                    }
                    for viewset in viewsets
                ]
            }
        )