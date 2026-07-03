import djcrud
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt

from djcrud.view import View

from .login import login_with_credentials
from .models import Token


@method_decorator(csrf_exempt, name="dispatch")
class ApiLoginView(View):
    """Exchange username/password for a short-lived Bearer token."""

    urlpath = "login/"

    def has_permission(self):
        return True

    def post(self, request, *args, **kwargs):
        body, status = login_with_credentials(request)
        return JsonResponse(body, status=status)


class TokenCreateView(djcrud.generic.CreateView):
    """Create a named API token via HTML form (raw key shown once)."""

    fields = ["name", "expires"]

    def form_valid(self, form):
        token, raw_key = Token.generate(
            user=self.request.user,
            name=form.cleaned_data["name"],
            expires=form.cleaned_data.get("expires"),
        )
        self.object = token
        messages.success(
            self.request,
            _("Token created: %(key)s — copy it now, it will not be shown again.")
            % {"key": raw_key},
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return self.router.find_route("list").reverse()


class TokenRouter(djcrud.ModelRouter):
    model = Token
    icon = "key"

    routes = [
        djcrud.generic.ListView,
        djcrud.generic.DetailView,
        TokenCreateView,
        djcrud.generic.DeleteView,
    ]

    def get_queryset(self, *, user, model, action, perm, obj=None):
        qs = super().get_queryset(
            user=user, model=model, action=action, perm=perm, obj=obj
        )
        if user.is_superuser:
            return qs
        return qs.filter(user=user)


def _api_router_routes():
    from .login import uses_drf_login

    routes = [TokenRouter]
    if not uses_drf_login():
        routes.insert(0, ApiLoginView.clone(urlname="login", urlpath="login/"))
    return routes


class ApiRouter(djcrud.Router):
    pass


ApiRouter._declaration = _api_router_routes()