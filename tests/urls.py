"""
URL configuration for tests.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include('djcrud_auth.urls')),
    path("", include('djcrud_auth.urls')),  # Include auth at root too for home page
]
