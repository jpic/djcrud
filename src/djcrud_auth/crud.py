from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from djcrud import crud, mvc
from djcrud_auth.views import LoginView, LogoutView


def get_custom_user_creation_form():
    """Return UserCreationForm for the configured AUTH_USER_MODEL.

    Django's default forms are hardcoded to auth.User, so we create
    a new form class with type() that uses settings.AUTH_USER_MODEL instead.
    """
    User = get_user_model()
    return type(
        'CustomUserCreationForm',
        (UserCreationForm,),
        {'Meta': type('Meta', (), {'model': User, 'fields': UserCreationForm.Meta.fields})}
    )


def get_custom_user_change_form():
    """Return UserChangeForm for the configured AUTH_USER_MODEL.

    Django's default forms are hardcoded to auth.User, so we create
    a new form class with type() that uses settings.AUTH_USER_MODEL instead.
    """
    User = get_user_model()
    return type(
        'CustomUserChangeForm',
        (UserChangeForm,),
        {'Meta': type('Meta', (), {'model': User, 'fields': '__all__'})}
    )

# Create User controller by copying the defaults from ModelController.
# We explicitly list the views (instead of relying on ModelController.defaults)
# so we can clone CreateView/UpdateView with our custom forms that use
# settings.AUTH_USER_MODEL. This is the idiomatic djcrud way when the
# generic ModelForm is not sufficient for a model like User (password hashing).
UserController = crud.ModelController.clone(
    model=get_user_model(),  # Uses settings.AUTH_USER_MODEL
    urlpath='user',
    urlname='user',
    views=[
        crud.UserListView.clone(table_fields=['id', 'username', 'email', 'is_active']),
        crud.UserDetailView,
        crud.UserCreateView.clone(form_class=get_custom_user_creation_form()),
        crud.UserUpdateView.clone(form_class=get_custom_user_change_form()),
    ],
)


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
