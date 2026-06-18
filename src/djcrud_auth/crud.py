from django.contrib.auth.models import User, Group

from djcrud import crud, mvc
from djcrud_auth.views import LoginView, LogoutView

# Create User controller using generic ModelController
# urlpath and urlname automatically set to 'user' from model
UserController = crud.ModelController.clone(model=User)


class AuthController(mvc.Controller):
    urlpath = 'auth'
    icon = 'shield-lock'
    views = [
        LoginView,
        LogoutView,
        # this lets UserController return its urls for its own views in /auth/user
        UserController,
        # TODO: GroupController,
    ]
