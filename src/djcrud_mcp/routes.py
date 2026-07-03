"""MCP profile routes under ``/api/`` (mounted by :data:`djcrud_drf.site`)."""

from django.urls import path

from djcrud_mcp.views import McpProfileDetailView, McpProfileListView, McpViewsetListView


def api_urlpatterns():
    """URL patterns relative to the ``/api/`` prefix."""
    return [
        path("mcp/profiles/", McpProfileListView.as_view(), name="mcp-profiles"),
        path(
            "mcp/profiles/<str:key>/",
            McpProfileDetailView.as_view(),
            name="mcp-profile-detail",
        ),
        path("mcp/viewsets/", McpViewsetListView.as_view(), name="mcp-viewsets"),
    ]