import functools

import django_filters
from django import forms
from django.db import models
from django.utils.translation import gettext as _


class FilterMixin:
    """django-filter FilterSet for explicit model field filters on list views.

    Attributes:
        filter_fields (list[str] | None): Model field names passed to the
            dynamic FilterSet ``Meta.fields``. ``None`` means no field filters.
        filter_form_class (type | None): When set on a subclass, replaces the
            composed filter form entirely (see :class:`~djcrud.views.list.ListView`).
        filter_target (str): Unpoly ``up-target`` for the filter form.
    """

    filter_fields = None
    filter_form_class = None
    filter_target = "[up-list]"

    @property
    def filter_submit_label(self):
        """Label for the filter form submit button."""
        return _("Apply")

    @functools.cached_property
    def filterset_class(self):
        return self.get_filterset_class()

    @functools.cached_property
    def filterset(self):
        if not self.filter_fields:
            return None
        filterset = self.filterset_class(**self.get_filterset_kwargs())
        self._sync_filter_widgets(filterset)
        self._prune_empty_fk_choices(filterset)
        return filterset

    def _sync_filter_widgets(self, filterset):
        """Use model ``formfield()`` widgets (e.g. djhacker/DAL) on filter fields."""
        for name, form_field in filterset.form.fields.items():
            try:
                model_field = self.model._meta.get_field(name)
            except Exception:
                continue
            if not isinstance(
                model_field,
                (models.ForeignKey, models.OneToOneField, models.ManyToManyField),
            ):
                continue
            patched = model_field.formfield()
            form_field.widget = patched.widget
            if getattr(patched, "queryset", None) is not None:
                form_field.queryset = patched.queryset

    def get_filterset_kwargs(self):
        return {
            "data": self.request.GET.copy(),
            "request": self.request,
            "queryset": super(FilterMixin, self).get_queryset(),
        }

    def get_filterset_meta_filter_overrides(self):
        return {
            models.CharField: {
                "filter_class": django_filters.CharFilter,
                "extra": lambda f: {
                    "lookup_expr": "icontains",
                },
            },
        }

    def get_filterset_form_class(self):
        return forms.Form

    def get_filterset_meta_attributes(self):
        return dict(
            model=self.model,
            fields=self.filter_fields,
            filter_overrides=self.get_filterset_meta_filter_overrides(),
            form=self.get_filterset_form_class(),
        )

    def get_filterset_meta_class(self):
        return type("Meta", (), self.get_filterset_meta_attributes())

    def get_filterset_extra_class_attributes(self):
        extra = {}
        for field_name in self.filter_fields:
            try:
                field = self.model._meta.get_field(field_name)
            except Exception:
                continue
            choices = getattr(field, "choices", None)
            if choices is None:
                continue
            extra[field_name] = django_filters.MultipleChoiceFilter(
                choices=choices,
            )
        return extra

    def get_filterset_class_attributes(self):
        attrs = dict(Meta=self.get_filterset_meta_class())
        attrs.update(self.get_filterset_extra_class_attributes())
        return attrs

    def get_filterset_class(self):
        return type(
            f"{self.model.__name__}FilterSet",
            (django_filters.FilterSet,),
            self.get_filterset_class_attributes(),
        )

    def _prune_empty_fk_choices(self, filterset):
        """Hide FK choices that would return no rows (crudlfap pattern)."""
        for name, field in filterset.form.fields.items():
            try:
                mf = self.model._meta.get_field(name)
            except Exception:
                continue
            if not isinstance(mf, models.ForeignKey):
                continue
            field.queryset = field.queryset.annotate(
                c=models.Count(mf.related_query_name()),
            ).filter(c__gt=0)

    @property
    def filter_attributes(self):
        """HTML attributes for the filter ``<form>`` tag."""
        return {
            "up-submit": True,
            "up-target": self.filter_target,
            "up-history": True,
        }
