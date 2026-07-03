from django.utils.functional import cached_property

from djcrud.media import ModuleMedia, SpaShellMedia

from .template import TemplateView


class SPAView(TemplateView):
    """Full-screen SPA shell with server-rendered sidebar navigation.

    Subclass and extend :class:`Media` to load your client bundle. The reference
    template is ``djcrud/base_spa.html`` (set ``unpoly_target = 'body'`` so menu
    links full-reload across shells).

    Attributes:
        default_template_name (str): ``base_spa.html`` under ``djcrud/``.
        unpoly_target (str): ``'body'`` — cross-shell navigation uses plain links.
        tags (list[str]): ``['navigation']`` — appears in the sidebar menu.
        mount_selector (str): CSS selector for the client mount node (default
            ``'#app'``). Override :meth:`get_mount_element` for custom HTML.
    """

    default_template_name = "base_spa.html"
    unpoly_target = "body"
    tags = ["navigation"]
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
        """Merged :class:`~djcrud.media.ModuleMedia` for this view (shell + subclass)."""
        return ModuleMedia(media=getattr(type(self), "Media", SpaShellMedia))

    def get_mount_element(self):
        """HTML for the client framework mount point inside ``[up-main]``."""
        selector = self.mount_selector.lstrip("#")
        return f'<div id="{selector}"></div>'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["mount_element"] = self.get_mount_element()
        return context