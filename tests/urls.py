"""
URL configuration for tests.
"""

from django.contrib import admin
from django.urls import path

# Empty urlpatterns for basic tests
# Tests will create their own controllers and test urlpatterns generation
urlpatterns = [
    path("admin/", admin.site.urls),
]
