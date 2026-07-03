import functools

from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext as _, ngettext
from django.views import generic

from ..model import ModelMixin
from .. import tags
from ..router import Router as DjcrudRouter
from .filter import FilterMixin
from .object import ObjectMixin
from .pagination import PaginationMixin
from .search import SearchMixin
from .template import TemplateViewMixin
from .tables2 import Tables2Mixin


class ListMixin:
    """List view behaviour: navigation tag, empty-state text, list actions.

    Attributes:
        default_template_name (str): Template for the list page.
        tags (list[str]): Menu discovery tags. Default ``['navigation']``.
        urlpath (str): URL segment for this view. Default ``''`` (list root).
        permission_shortcode (str): Django permission prefix for list access.
            Default ``'view'``.
        icon (str): Bootstrap Icons name; defaults to the model router ``icon``.
        color (str): Bulma color for the navigation icon; defaults to the model
            router ``color``.
        pagination_target (str): Unpoly target for paginated list updates.
        filter_target (str): Unpoly target for filter form submissions.
    """

    default_template_name = "djcrud/list.html"
    tags = [tags.NAVIGATION]
    urlpath = ""
    permission_shortcode = "view"

    @property
    def title(self):
        """Page heading from the model's ``verbose_name_plural``."""
        return self.model._meta.verbose_name_plural.capitalize()

    @property
    def icon(self):
        """Bootstrap Icons name; falls back to the model router ``icon``."""
        return getattr(self.router.model_router, "icon", None)

    @property
    def color(self):
        """Bulma color for the navigation icon; falls back to the model router."""
        return getattr(self.router.model_router, "color", None)

    def breadcrumbs(self):
        """List views have no parent breadcrumbs."""
        return []

    @functools.cached_property
    def list_actions(self):
        """Bulk-action views for the list action bar.

        These are collected by walking LIST_ACTION-tagged routes (no
        permission check at all; the bar offers the configured actions).
        Per-object allowed actions are propagated via ``data-list-actions``
        attributes on row checkboxes (always with ``object=``); the
        ``<list-action-bar>`` JS uses those to filter which buttons are
        enabled for the current selection. Execution time checks still apply.
        """
        actions = []

        def collect(router):
            for route in router.routes:
                if isinstance(route, DjcrudRouter):
                    collect(route)
                    continue
                if tags.LIST_ACTION in getattr(route, "tags", []):
                    view = type(route)(request=self.request)
                    actions.append(view)

        collect(self.router)
        return actions

    @property
    def empty_list_message(self):
        return _("No %(verbose_name)s found matching the query") % {
            "verbose_name": self.model_meta.verbose_name_plural,
        }

    @property
    def list_action_count_label_one(self):
        """Selection count label when exactly one row is selected."""
        return ngettext(
            "%(total_count)s selected",
            "All %(total_count)s selected",
            1,
        ) % {"total_count": 1}

    @property
    def list_action_count_label_other(self):
        """Selection count label template when multiple rows are selected."""
        return ngettext(
            "%(total_count)s selected",
            "All %(total_count)s selected",
            2,
        ) % {"total_count": "__COUNT__"}


class ListView(
    ListMixin,
    SearchMixin,
    FilterMixin,
    PaginationMixin,
    Tables2Mixin,
    TemplateViewMixin,
    ModelMixin,
    generic.ListView,
):
    pagination_target = "[up-list]"
    filter_target = "[up-list]"

    def get_queryset(self):
        qs = super().get_queryset()
        if self.filter_fields and self.filterset is not None:
            qs = self.filterset.qs
        return self.search_filter(qs)

    def get_filter_field_names(self):
        """Filter bar field names: search input plus :attr:`filter_fields`."""
        names = list(self.filter_fields or [])
        if self.search_fields and self.search_param not in names:
            names.insert(0, self.search_param)
        return names

    def _uses_default_filter_form(self):
        return "filter_form_class" not in type(self).__dict__

    def _build_composed_filter_form_class(self):
        field_names = self.get_filter_field_names()
        if not field_names:
            return None

        form_fields = {}

        for name in field_names:
            if name == self.search_param:
                form_fields[name] = self.search_form_field()
            elif self.filterset is not None:
                form_fields[name] = self.filterset.form.fields[name]

        def __init__(form_self, *args, view=None, **kwargs):
            forms.Form.__init__(form_self, *args, **kwargs)
            form_self.helper = FormHelper()
            form_self.helper.form_method = "get"
            form_self.helper.form_tag = False
            form_self.helper.disable_csrf = True
            form_self.helper.form_show_labels = True
            if view is not None:
                page_kwarg = getattr(view, "page_kwarg", "page")
                for key, value in view.request.GET.items():
                    if key in form_self.fields or key == page_kwarg:
                        continue
                    form_self.fields[key] = forms.CharField(
                        widget=forms.HiddenInput(),
                        initial=value,
                    )

        form_fields["__init__"] = __init__
        return type(
            f"{self.model.__name__}FilterForm",
            (forms.Form,),
            form_fields,
        )

    @functools.cached_property
    def filter_form(self):
        if (
            "filter_form_class" in type(self).__dict__
            and type(self).filter_form_class is not None
        ):
            return type(self).filter_form_class(self.request.GET)

        form_class = self._build_composed_filter_form_class()
        if form_class is None:
            return None
        return form_class(self.request.GET, view=self)

    @property
    def has_active_filters(self):
        form = self.filter_form
        if form is None:
            return False
        return any(
            form.data.get(name)
            for name, field in form.fields.items()
            if not isinstance(field.widget, forms.HiddenInput)
        )

    def clear_filter_url(self):
        qs = self.request.GET.copy()
        form = self.filter_form
        if form is not None:
            for name, field in form.fields.items():
                if not isinstance(field.widget, forms.HiddenInput):
                    qs.pop(name, None)
        page_kwarg = getattr(self, "page_kwarg", "page")
        qs.pop(page_kwarg, None)
        path = self.request.path
        return f"{path}?{qs.urlencode()}" if qs else path


class DetailListMixin:
    """List rows of a related model on an object detail page.

    Set :attr:`list_model` when the listed rows are not the enclosing
    :class:`~djcrud.ModelRouter` model (e.g. log lines on a process detail).
    """

    list_model = None

    @property
    def model(self):
        list_model = getattr(type(self), "list_model", None)
        if list_model is not None:
            return list_model
        return super().model


class DetailListView(DetailListMixin, ObjectMixin, ListView):
    """List of related rows shown on an object detail page."""

    default_template_name = "djcrud/detaillist.html"
    tags = [tags.OBJECT]

    @property
    def title(self):
        return super(ListMixin, self).title
