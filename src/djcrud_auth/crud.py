from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from djcrud import mvc
from djcrud.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from djcrud import attribute

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

# Create User controller. We explicitly list the views so we can clone
# Create/Update with custom forms for AUTH_USER_MODEL.
UserController = mvc.Controller.clone(
    model=get_user_model(),
    urlpath='user',
    urlname='user',
    icon='person',
    views=[
        ListView.clone(
            table_fields=['id', 'username', 'email', 'is_active'],
            urlpath='',
            urlname='list',
            icon='person',  # ensure ListView uses person icon (overrides default 'list')
        ),
        DetailView,
        CreateView.clone(form_class=get_custom_user_creation_form()),
        UpdateView.clone(form_class=get_custom_user_change_form()),
        DeleteView,
    ],
)


class AuthController(mvc.Controller):
    name = 'Authentication'
    urlpath = 'auth'
    icon = 'shield-lock'
    views = [
        LoginView,
        LogoutView,
        UserController,
        # TODO: GroupController,
    ]
