import functools
import operator
from functools import reduce

from django import forms
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext as _


class SearchMixin:
    """Full-text search across CharField and TextField columns on list views.

    Attributes:
        search_param (str): GET parameter for the search input. Default
            ``'search'``.
    """

    search_param = "search"

    @functools.cached_property
    def search_fields(self):
        """CharField and TextField names searched by :attr:`search_param`."""
        return [
            f.name
            for f in self.model_meta.get_fields()
            if f.concrete
            and not f.is_relation
            and isinstance(f, (models.CharField, models.TextField))
        ]

    def search_form_field(self):
        """Optional CharField for the list filter sidebar."""
        return forms.CharField(
            label=_("Search"),
            required=False,
        )

    def search_filter(self, qs):
        """Apply :attr:`search_param` icontains OR across :attr:`search_fields`."""
        if not self.search_fields:
            return qs
        term = self.request.GET.get(self.search_param, "")
        if not term:
            return qs
        return qs.filter(
            reduce(
                operator.or_,
                [Q(**{f"{field}__icontains": term}) for field in self.search_fields],
            )
        ).distinct()
