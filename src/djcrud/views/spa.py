from django.forms import Media
from django.utils.functional import cached_property

from djcrud.media import SpaShellMedia

from .template import TemplateView


class SPAView(TemplateView):
    """Full-screen SPA shell with server-rendered sidebar navigation.

    Subclass and extend :class:`Media` to load your client ES modules with
    :class:`~django.forms.widgets.Script` (``type="module"``).
    ``djcrud/base_spa.html`` is the default template (``unpoly_target = 'body'``
    so menu links full-reload across shells). Set :attr:`mount_element` to the
    HTML your client bundle attaches to; the template renders
    ``{{ view.mount_element|safe }}``.

    Attributes:
        default_template_name (str): ``base_spa.html`` under ``djcrud/``.
        unpoly_target (str): ``'body'`` — cross-shell navigation uses plain links.
        tags (list[str]): ``['navigation']`` — appears in the sidebar menu.
        mount_element (str): Bootstrap HTML inside ``[up-main]`` (default ``#app`` div).
    """

    default_template_name = "base_spa.html"
    unpoly_target = "body"
    tags = ["navigation"]
    mount_element = '<div id="app"></div>'

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