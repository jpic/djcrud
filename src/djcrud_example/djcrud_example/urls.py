"""
URL configuration for djcrud_example project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

from djcrud import mvc
from djcrud.views.template import TemplateView
from djcrud_auth.crud import AuthController

site = mvc.Controller(
    views=[
        TemplateView.clone(
            icon='home',
            template_name='crudlfap/home.html',
            menus=['main'],
            title_heading='',
            urlname='home',
            urlpath='',
            has_perm=True,  # allow non-authenticated
        ),
        AuthController,
    ]
)

urlpatterns = [
    path("admin/", admin.site.urls),
] + site.urlpatterns
