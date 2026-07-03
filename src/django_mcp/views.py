from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from django_mcp.site import site
from django_mcp.viewsets import api_path_for, discover_viewsets, model_name_for


class McpProfileListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        del request
        return Response(
            {
                "profiles": site.list_keys(),
                "default": site.default_key(),
            }
        )


class McpProfileDetailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, key: str):
        del request
        profile = site.get_profile(key)
        return Response(profile.to_dict())


class McpViewsetListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
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