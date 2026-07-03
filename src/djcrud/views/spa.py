from django.forms import Media
from django.utils.functional import cached_property

from djcrud.media import SpaShellMedia

from .template import TemplateView


class SPAView(TemplateView):
    """Full-screen SPA shell with server-rendered sidebar navigation.

    Subclass and extend :class:`Media` to load your client ES modules with
    :class:`~django.forms.widgets.Script` (``type="module"``).
    ``djcrud/base_spa.html`` is the default template (``unpoly_target = 'body'``
    so menu links full-reload across shells). An empty ``#app`` mount node is
    rendered by default (:attr:`mount_selector`).

    Attributes:
        default_template_name (str): ``base_spa.html`` under ``djcrud/``.
        unpoly_target (str): ``'body'`` — cross-shell navigation uses plain links.
        tags (list[str]): ``['navigation']`` — appears in the sidebar menu.
        mount_selector (str): CSS selector for the client mount node (``'#app'``).
        mount_element (str | None): Optional initial HTML inside ``[up-main]``;
            overrides the default mount node when set.
    """

    default_template_name = "base_spa.html"
    unpoly_target = "body"
    tags = ["navigation"]
    mount_element = None
    mount_selector = "#app"

    class Media(SpaShellMedia):
        pass

    def has_permission(self):
        """Superuser-only until :func:`~djcrud.add_perm` grants access."""
        from djcrud.permissions import has_site_permission

        ctx = self.permission_context()
        return has_site_permission(
            user=ctx["user"],
            perm=ctx["perm"],
            action=ctx["action"],
            model=ctx["model"],
            obj=ctx["obj"],
            router=ctx["router"],
        )

    @cached_property
    def media(self):
        """Merged :class:`~django.forms.Media` for this view (shell + subclass)."""
        return Media(media=getattr(type(self), "Media", SpaShellMedia))

    def get_mount_element(self):
        """HTML rendered inside ``[up-main]`` before the client bundle runs."""
        if mount := getattr(type(self), "mount_element", None):
            return mount
        selector = self.mount_selector.lstrip("#")
        return f'<div id="{selector}"></div>'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["mount_element"] = self.get_mount_element()
        return context