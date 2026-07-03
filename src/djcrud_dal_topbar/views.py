import functools
from collections import OrderedDict

import django_tables2
from dal_alight_queryset_sequence.views import AlightQuerySetSequenceView
from django import http
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.translation import gettext as _, gettext_lazy
from django.views import generic
from queryset_sequence import QuerySetSequence

from djcrud.view import ViewMixin
from djcrud.views.pagination import PaginationMixin
from djcrud.views.template import TemplateViewMixin

from .lookup import (
    build_site_search_queryset,
    find_detail_url,
    find_model_router,
    mixup_querysets,
)


class SearchActionsColumn(django_tables2.Column):
    empty_values = ()
    template_name = "djcrud/_actions_column.html"

    def render(self, record, table):
        obj = record["record"] if isinstance(record, dict) else record
        router = find_model_router(table.view.router.root, type(obj))
        if router is None:
            return ""
        actions = router.get_tagged_views(
            "object",
            request=table.view.request,
            object=obj,
        )
        return render_to_string(
            self.template_name,
            {"actions": actions, "view": table.view, "record": obj},
            request=table.view.request,
        )


class SearchResultsTable(django_tables2.Table):
    type = django_tables2.Column(
        accessor="type_label",
        verbose_name=gettext_lazy("Type"),
        orderable=False,
    )
    result = django_tables2.Column(
        accessor="result_label",
        verbose_name=gettext_lazy("Result"),
        orderable=False,
    )
    actions = SearchActionsColumn()

    class Meta:
        template_name = "djcrud/_tables2.html"
        fields = ("type", "result", "actions")
        attrs = {
            "class": "table is-striped is-hoverable is-fullwidth",
        }


class SearchView(PaginationMixin, TemplateViewMixin, generic.ListView):
    """Site-wide search results page with paginated table."""

    urlpath = "search/"
    default_template_name = "djcrud/search.html"
    tags = []
    paginate_by = 25
    pagination_target = "[up-main]"
    search_param = "q"
    context_object_name = "object_list"

    @property
    def title(self):
        return _("Search")

    @property
    def q(self):
        raw = self.request.GET.get(self.search_param, "")
        return raw.strip()

    @property
    def show_results(self):
        return bool(self.q)

    @property
    def empty_list_message(self):
        return _("No results found.")

    def has_permission(self):
        return self.request.user.is_authenticated

    def get_paginate_by(self, queryset):
        if not self.show_results:
            return None
        return super().get_paginate_by(queryset)

    def get_queryset(self):
        if not self.show_results:
            return QuerySetSequence()
        return build_site_search_queryset(self.request, self.q, mixup=False)

    def _table_row(self, record):
        model = type(record)
        detail_url = find_detail_url(model, record.pk)
        label = str(record)
        if detail_url:
            result_label = format_html('<a href="{}">{}</a>', detail_url, label)
        else:
            result_label = label
        return {
            "type_label": model._meta.verbose_name,
            "result_label": result_label,
            "record": record,
        }

    @functools.cached_property
    def table(self):
        rows = [self._table_row(record) for record in self.object_list]
        table = SearchResultsTable(rows)
        table.view = self
        django_tables2.RequestConfig(self.request, paginate=False).configure(table)
        return table


class SiteSearchView(ViewMixin, AlightQuerySetSequenceView):
    """Site-wide autocomplete across opted-in model-router list views."""

    urlpath = "search/autocomplete/"
    tags = []

    @property
    def codename(self):
        return "autocomplete"

    mixup = True
    paginate_by = 10

    def has_permission(self):
        return self.request.user.is_authenticated

    def get_queryset(self):
        qs = build_site_search_queryset(
            self.request,
            self.q,
            mixup=False,
            paginate_by=self.paginate_by,
        )
        if not self.q or not qs.get_querysets():
            return QuerySetSequence()
        if self.mixup:
            qs = mixup_querysets(qs, self.paginate_by)
        return qs

    def render_to_response(self, context):
        groups = OrderedDict()
        for result in context["object_list"]:
            groups.setdefault(type(result), []).append(result)

        html = []
        for model, results in groups.items():
            html.append(
                format_html(
                    '<div class="autocomplete-light-group djcrud-site-search-group">{}</div>',
                    model._meta.verbose_name,
                )
            )
            for result in results:
                detail_url = find_detail_url(model, result.pk)
                if not detail_url:
                    continue
                html.append(
                    format_html(
                        '<div data-value="{}" data-url="{}">{}</div>',
                        self.get_result_value(result),
                        detail_url,
                        str(result),
                    )
                )

        return http.HttpResponse(
            "".join(html),
            content_type="text/html; charset=utf-8",
        )
