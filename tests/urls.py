from django.contrib import admin
from django.urls import include, path

import djcrud
import djcrud_drf

from djcrud_api.login import uses_drf_login

djcrud_drf.router.build()
_api_patterns = []
if uses_drf_login():
    from djcrud_api.drf_views import login_urlpattern

    _api_patterns.append(login_urlpattern())
for route in djcrud_drf.router.routes:
    _api_patterns += route.urlpatterns

urlpatterns = (
    [
        path("admin/", admin.site.urls),
    ]
    + djcrud.site.build().urlpatterns
    + [
        path(
            "api/",
            include((_api_patterns, "api"), namespace="api"),
        ),
    ]
)

handler400 = "djcrud.handlers.handler400"
handler403 = "djcrud.handlers.handler403"
handler404 = "djcrud.handlers.handler404"
handler500 = "djcrud.handlers.handler500"
