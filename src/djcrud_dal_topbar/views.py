from collections import OrderedDict

from dal_alight_queryset_sequence.views import AlightQuerySetSequenceView
from django import http
from django.utils.html import format_html
from queryset_sequence import QuerySetSequence

from djcrud.view import ViewMixin

from .lookup import (
    apply_search,
    find_detail_url,
    get_list_queryset,
    iter_searchable_list_views,
)


class SiteSearchView(ViewMixin, AlightQuerySetSequenceView):
    """Site-wide autocomplete across permitted model-router list views."""

    urlpath = "search/"
    tags = []

    @property
    def codename(self):
        return "search"

    mixup = True
    paginate_by = 10

    def has_permission(self):
        return self.request.user.is_authenticated

    def get_queryset(self):
        if not self.q:
            return QuerySetSequence()
        querysets = []
        for list_view in iter_searchable_list_views(self.request):
            qs = get_list_queryset(list_view)
            qs = apply_search(qs, list_view.search_fields, self.q)
            querysets.append(qs)
        if not querysets:
            return QuerySetSequence()
        return self.mixup_querysets(QuerySetSequence(*querysets))

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
