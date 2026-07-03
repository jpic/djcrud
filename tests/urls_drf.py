from django.contrib import admin
from django.urls import path

import djcrud
import djcrud_drf

from djcrud import handlers

try:
    from djcrud_mcp.django.urls import urlpatterns as mcp_urlpatterns
except ImportError:
    mcp_urlpatterns = []


urlpatterns = [
    path("admin/", admin.site.urls),
] + (
    djcrud.site.build().urlpatterns
    + djcrud_drf.site.build().urlpatterns
    + mcp_urlpatterns
)

handler400 = handlers.handler400
handler403 = handlers.handler403
handler404 = handlers.handler404
handler500 = handlers.handler500