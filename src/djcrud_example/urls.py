from django.contrib import admin
from django.urls import path

import djcrud

urlpatterns = [
    path("admin/", admin.site.urls),
] + djcrud.site.build().urlpatterns

# Optional DRF API URLs (requires djcrud[drf] and INSTALLED_APPS entries):
# import djcrud_drf
# urlpatterns += djcrud_drf.site.build().urlpatterns

handler400 = "djcrud.handlers.handler400"
handler403 = "djcrud.handlers.handler403"
handler404 = "djcrud.handlers.handler404"
handler500 = "djcrud.handlers.handler500"
