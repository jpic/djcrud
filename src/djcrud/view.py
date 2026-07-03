from django.apps import apps
from django.utils.translation import gettext as _
from django.views import generic
from django.urls import path

from .clonable import Clonable
from .permission import PermissionMixin, call_with_context
from .permissions import has_permission
from .errors import forbidden_response
from .redirect import FULL_PAGE_LINK_ATTRIBUTES
from .route import Route

SPA_TEMPLATE_SUFFIX = "base_spa.html"


def uses_spa_shell(view):
    """Return whether *view* renders a template ending with ``base_spa.html``."""
    for attr in ("template_name", "default_template_name"):
        name = getattr(view, attr, None)
        if isinstance(name, str) and name.endswith(SPA_TEMPLATE_SUFFIX):
            return True
    return False


class ViewMixin(PermissionMixin, Clonable, Route):
    """Base behaviour for every djcrud view: permissions, URLs, Unpoly defaults.

    Subclasses and clones inherit :attr:`permission_shortcode` from the class
    body when set; otherwise it falls back to the view :attr:`urlname`.

    Set :attr:`unpoly_target` to ``'body'`` when the page shell differs from
    the default layout (for example SPA views using a template named
    ``*base_spa.html``). Cross-shell navigation uses plain links
    (:data:`~djcrud.redirect.FULL_PAGE_LINK_ATTRIBUTES`) so scripts such as
    Svelte components load correctly.
    """

    unpoly_target = None

    def setup(self, request, *args, **kwargs):
        """Track the active view on the request for cross-shell link wiring."""
        super().setup(request, *args, **kwargs)
        request._djcrud_view = self

    @property
    def unpoly(self):
        """Unpoly request headers exposed to templates as ``view.unpoly.mode``, etc."""
        request = getattr(self, "request", None)
        if request is None:
            return {
                "mode": "",
                "target": "",
                "layer": "",
                "fail_mode": "",
                "fail_target": "",
            }
        headers = request.headers
        return {
            "mode": headers.get("X-Up-Mode", ""),
            "target": headers.get("X-Up-Target", ""),
            "layer": headers.get("X-Up-Layer", ""),
            "fail_mode": headers.get("X-Up-Fail-Mode", ""),
            "fail_target": headers.get("X-Up-Fail-Target", ""),
        }

    @property
    def urlpatterns(self):
        """Single Django URL pattern dispatching to this view class."""
        view_func = type(self).as_view()
        return [path(self.urlpath, view_func, name=self.urlname)]

    @property
    def title(self):
        """Human-readable label with the ``View`` suffix removed."""
        return super().title.replace("View", "")

    @property
    def breadcrumb_title(self):
        """Breadcrumb label; defaults to :attr:`title`."""
        return self.title

    @property
    def color(self):
        """Bulma button/icon color; override on model-backed views."""
        return None

    @property
    def codename(self):
        """URL segment with the ``view`` suffix removed from the class name."""
        return super().codename.replace("view", "")

    def dispatch(self, request, *args, **kwargs):
        """Redirect anonymous users to login; return 403 when permission denied."""
        if not self.has_permission():
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login

                return redirect_to_login(request.get_full_path())
            return forbidden_response(request, view=self)
        return super().dispatch(request, *args, **kwargs)

    @property
    def permission_shortcode(self):
        """Django permission prefix (``add``, ``change``, ``view``, …)."""
        for cls in type(self).__mro__:
            value = cls.__dict__.get("permission_shortcode")
            if isinstance(value, str):
                return value
        return self.urlname

    def _permission_model(self):
        router = getattr(self, "router", None)
        if router is None:
            return None
        model_router = router.model_router
        return getattr(type(model_router), "model", None)

    @property
    def permission_codename(self):
        """Permission codename, e.g. ``view_document``."""
        model = self._permission_model()
        if not model:
            return self.permission_shortcode
        return f"{self.permission_shortcode}_{model._meta.model_name}"

    @property
    def permission_fullcode(self):
        """Fully qualified permission string, e.g. ``myapp.view_document``."""
        model = self._permission_model()
        if not model:
            return self.permission_codename
        return f"{model._meta.app_label}.{self.permission_codename}"

    def has_permission(self):
        """Return whether the current user may access this view."""
        ctx = self.permission_context()
        router = getattr(self, "router", None)
        if router is not None:
            return call_with_context(router.has_permission, ctx)
        return has_permission(**ctx)

    def breadcrumbs(self, with_self=True):
        """Return breadcrumb trail; override in object views."""
        return []

    def unpoly_link_attributes(self, target_view, context=None):
        """Return Unpoly attrs for navigating from this page to *target_view*."""
        if uses_spa_shell(self):
            return dict(FULL_PAGE_LINK_ATTRIBUTES)
        if uses_spa_shell(self) != uses_spa_shell(target_view):
            return dict(FULL_PAGE_LINK_ATTRIBUTES)
        source_target = getattr(self, "unpoly_target", None)
        dest_target = getattr(target_view, "unpoly_target", None)
        if source_target != dest_target:
            return dict(FULL_PAGE_LINK_ATTRIBUTES)
        fn = getattr(target_view, "unpoly_attributes", None)
        if fn is None:
            return {}
        return fn(context)

    def unpoly_attributes(self, context=None):
        """HTML attributes for Unpoly navigation on this view."""
        return {
            "up-follow": True,
            "up-target": "[up-main]",
        }

    def querystring(self, **params):
        """Current GET query string with *params* merged in."""
        qs = self.request.GET.copy()
        for key, value in params.items():
            qs[key] = value
        return "?" + qs.urlencode()


class View(ViewMixin, generic.View):
    """Minimal djcrud view for custom non-generic handlers."""

    pass