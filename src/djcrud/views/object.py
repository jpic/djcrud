from django.http import Http404
from django.utils.translation import gettext as _
from django.views import generic

from .. import tags
from .template import TemplateViewMixin


class ObjectMixin:
    """Resolve ``self.object`` from the URL primary key and build breadcrumbs.

    Object-bound views use ``urlpath`` ``'<pk>/{codename}/'`` by default.
    """

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.object = self.get_object()

    def get_object(self, queryset=None):
        if obj := getattr(self, "object", None):
            return obj
        if queryset is None:
            queryset = self.get_object_queryset()
        pk = self.kwargs.get("pk")
        try:
            return queryset.get(pk=pk)
        except Exception as exc:
            model = getattr(queryset, "model", None)
            does_not_exist = getattr(model, "DoesNotExist", None)
            if does_not_exist is not None and isinstance(exc, does_not_exist):
                meta = getattr(model, "_meta", None)
                verbose_name = getattr(meta, "verbose_name", "object")
                raise Http404(
                    _("No %(verbose_name)s found matching the query")
                    % {
                        "verbose_name": verbose_name,
                    }
                ) from exc
            raise

    @property
    def url(self):
        # object bound on the view instance
        if obj := getattr(self, "object", None):
            return self.reverse(obj.pk)
        # pk bound from URL kwargs during dispatch
        if pk := getattr(self, "kwargs", {}).get("pk"):
            return self.reverse(pk)
        return super().url

    @property
    def urlpath(self):
        return f"<pk>/{self.codename}/"

    @property
    def breadcrumb_title(self):
        return self.title

    def breadcrumbs(self, with_self=True):
        crumbs = []
        list_route = self.router.find_route("list")
        if list_route:
            list_view = type(list_route)(request=self.request)
            if list_view.has_permission():
                crumbs.append(list_view)

        detail_route = self.router.find_route("detail")
        if detail_route:
            detail_view = type(detail_route)(request=self.request, object=self.object)
            if detail_view.has_permission():
                crumbs.append(detail_view)

        if with_self:
            crumbs.append(self)
        return crumbs


class ObjectTemplateView(ObjectMixin, TemplateViewMixin, generic.TemplateView):
    tags = [tags.OBJECT]
