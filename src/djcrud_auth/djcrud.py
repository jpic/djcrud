import djcrud
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse_lazy

from .views import AuthRouter

User = get_user_model()

djcrud.add_search(User)
djcrud.add_search(Group)
djcrud.site.routes.append(AuthRouter)
settings.LOGIN_URL = reverse_lazy("site:auth:login")
