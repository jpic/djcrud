import logging

import djcrud
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.models import Group
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    SetPasswordForm,
    UserChangeForm,
    UserCreationForm,
)
from django.utils.translation import gettext as _
from django.views import generic

from djcrud.errors import not_found_response
from djcrud.model import ModelMixin
from djcrud.redirect import FULL_PAGE_LINK_ATTRIBUTES, full_page_redirect_home
from djcrud.views.form import FormMixin
from djcrud.views.object import ObjectMixin
from djcrud.views.template import TemplateViewMixin

logger = logging.getLogger(__name__)

User = get_user_model()


class LoginView(djcrud.generic.FormView):
    form_class = AuthenticationForm
    tags = ["topbar", "navigation"]
    icon = "box-arrow-in-right"

    @property
    def form_attributes(self):
        """HTML attributes for the login form; targets the full page body."""
        attrs = dict(FormMixin.form_attributes)
        attrs["up-target"] = "body"
        attrs["up-history"] = False
        return attrs

    @property
    def title(self):
        return _("Log in")

    def has_permission(self):
        """Show login only to anonymous users."""
        return not self.request.user.is_authenticated

    def get_form_valid_message(self):
        return _("Logged in as %(user)s") % {"user": self.form.get_user()}

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super().form_valid(form)


class LogoutView(djcrud.generic.FormView):
    tags = ["topbar", "navigation"]
    icon = "box-arrow-right"
    form_attributes = {
        "up-submit": False,
    }

    @property
    def title(self):
        return _("Log out")

    @property
    def message(self):
        return _("Are you sure you want to logout?")

    def has_permission(self):
        """Show logout only to authenticated users."""
        return self.request.user.is_authenticated

    def get_form_valid_message(self):
        return _("Logged out")

    def form_valid(self, form):
        logout(self.request)
        self.form = form
        self.message_success()
        return full_page_redirect_home(self.request)


class PasswordView(
    ObjectMixin,
    ModelMixin,
    FormMixin,
    TemplateViewMixin,
    generic.FormView,
):
    tags = ["object"]
    icon = "key"
    color = "link"
    action = "click->modal#open"
    default_template_name = "form.html"

    @property
    def codename(self):
        return "password"

    @property
    def title(self):
        if self.object == self.request.user:
            return _("Change password")
        return _("Set password")

    @property
    def submit_button_label(self):
        return _("Save")

    def get_form_class(self):
        if self.object == self.request.user:
            cls = PasswordChangeForm
        else:
            cls = SetPasswordForm
        return type(cls.__name__, (cls,), dict(instance=self.object))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.object
        return kwargs

    def get_success_url(self):
        detail_route = self.router.find_route("detail")
        if detail_route:
            return type(detail_route)(
                request=self.request,
                object=self.object,
            ).url
        list_route = self.router.find_route("list")
        if list_route:
            return type(list_route)(request=self.request).url
        return "/"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class BecomeUser(ObjectMixin, ModelMixin, djcrud.View):
    tags = ["object"]
    icon = "person-badge"
    color = "danger"

    @property
    def codename(self):
        return "su"

    @property
    def title(self):
        return _("Become user")

    def unpoly_attributes(self, context=None):
        return FULL_PAGE_LINK_ATTRIBUTES

    def get_object(self, queryset=None):
        try:
            user = super().get_object()
        except User.DoesNotExist:
            messages.error(
                self.request,
                _("Could not find user %(pk)s") % {"pk": self.kwargs["pk"]},
            )
            return None

        user.backend = "django.contrib.auth.backends.ModelBackend"
        return user

    def get(self, request, *args, **kwargs):
        if self.object is None:
            return full_page_redirect_home(request)

        logger.info("BecomeUser by %s", request.user)
        become_user_realname = str(request.user)
        become_user = request.session.get("become_user", request.user.pk)
        login(request, self.object)
        request.session.setdefault("become_user_realname", become_user_realname)
        request.session["become_user"] = become_user
        messages.info(
            request,
            _("Switched to user %(user)s") % {"user": request.user},
        )
        return full_page_redirect_home(request)


class Become(djcrud.View):
    tags = ["topbar", "navigation"]
    icon = "arrow-return-left"

    @property
    def codename(self):
        return "su"

    def has_permission(self):
        return "become_user" in self.request.session

    @property
    def title(self):
        realname = self.request.session.get("become_user_realname", "")
        return _("Back to your account (%(name)s)") % {"name": realname}

    def unpoly_attributes(self, context=None):
        return FULL_PAGE_LINK_ATTRIBUTES

    def dispatch(self, *args, **kwargs):
        if "become_user" not in self.request.session:
            return not_found_response(self.request, view=self)
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        logger.info("Become by %s", request.user)
        user = User.objects.get(pk=request.session["become_user"])
        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)
        messages.info(
            request,
            _("Switched back to your user %(user)s") % {"user": user},
        )
        request.session.pop("become_user", None)
        return full_page_redirect_home(request)


def get_custom_user_creation_form():
    """Return UserCreationForm for the configured AUTH_USER_MODEL.

    Django's default forms are hardcoded to auth.User, so we create
    a new form class with type() that uses settings.AUTH_USER_MODEL instead.
    """
    return type(
        "CustomUserCreationForm",
        (UserCreationForm,),
        {
            "Meta": type(
                "Meta", (), {"model": User, "fields": UserCreationForm.Meta.fields}
            )
        },
    )


def get_custom_user_change_form():
    """Return UserChangeForm for the configured AUTH_USER_MODEL.

    Django's default forms are hardcoded to auth.User, so we create
    a new form class with type() that uses settings.AUTH_USER_MODEL instead.
    """
    return type(
        "CustomUserChangeForm",
        (UserChangeForm,),
        {"Meta": type("Meta", (), {"model": User, "fields": "__all__"})},
    )


class GroupRouter(
    djcrud.ModelRouter.clone(
        model=Group,
        icon="collection",
        routes=djcrud.ModelRouter.routes
        + [
            djcrud.generic.ListView.clone(
                table_fields=["id", "name"],
                site_search=True,
            ),
        ],
    )
):
    """CRUD for auth groups; autocomplete endpoint used by User form filters."""

    def get_queryset(self, *, user, model, action, perm, obj=None):
        return super().get_queryset(
            user=user, model=model, action=action, perm=perm, obj=obj
        ).order_by("name")


class UserCreateView(djcrud.generic.CreateView):
    def get_form_class(self):
        return get_custom_user_creation_form()


class UserUpdateView(djcrud.generic.UpdateView):
    def get_form_class(self):
        return get_custom_user_change_form()


class AuthRouter(djcrud.Router):
    routes = [
        LoginView,
        LogoutView,
        Become,
        GroupRouter,
        djcrud.ModelRouter.clone(
            model=User,
            icon="people",
            routes=djcrud.ModelRouter.routes
            + [
                djcrud.generic.ListView.clone(
                    table_fields=[
                        "id",
                        "username",
                        "email",
                        "is_active",
                        "actions",
                    ],
                    filter_fields=["groups"],
                    site_search=True,
                ),
                UserCreateView,
                UserUpdateView,
                PasswordView,
                BecomeUser,
            ],
        ),
    ]
