import djcrud
from django.conf import settings
from django.urls import reverse_lazy

from .views import AuthRouter

djcrud.site.routes.append(AuthRouter)
settings.LOGIN_URL = reverse_lazy("site:auth:login")
