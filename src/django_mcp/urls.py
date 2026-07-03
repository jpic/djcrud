from django.urls import path

from django_mcp.views import McpProfileDetailView, McpProfileListView, McpViewsetListView

urlpatterns = [
    path("api/mcp/profiles/", McpProfileListView.as_view(), name="mcp-profiles"),
    path(
        "api/mcp/profiles/<str:key>/",
        McpProfileDetailView.as_view(),
        name="mcp-profile-detail",
    ),
    path("api/mcp/viewsets/", McpViewsetListView.as_view(), name="mcp-viewsets"),
]