from django import forms
from django.apps import apps
from django.db import models

import djhacker
from dal import autocomplete

from .lookup import find_autocomplete_url

RELATION_FIELD_CLASSES = (
    models.ForeignKey,
    models.OneToOneField,
    models.ManyToManyField,
)


def _autocomplete_kwargs(model_field, **kwargs):
    field = model_field.field
    remote = field.remote_field
    if remote is None:
        return {}
    url_name = find_autocomplete_url(remote.model)
    if not url_name:
        return {}
    widget_attrs = {"class": "input"}
    if isinstance(field, models.ManyToManyField):
        return dict(
            form_class=forms.ModelMultipleChoiceField,
            widget=autocomplete.ModelAlightMultiple(url=url_name, attrs=widget_attrs),
            **kwargs,
        )
    return dict(
        form_class=forms.ModelChoiceField,
        widget=autocomplete.ModelAlight(url=url_name, attrs=widget_attrs),
        **kwargs,
    )


def patch_relation_formfields():
    """Call djhacker.formfield on every concrete relation field."""
    for model in apps.get_models():
        for field in model._meta.local_fields:
            if isinstance(field, RELATION_FIELD_CLASSES):
                djhacker.formfield(getattr(model, field.name))
        for field in model._meta.local_many_to_many:
            djhacker.formfield(getattr(model, field.name))


def register():
    for field_class in RELATION_FIELD_CLASSES:
        djhacker.register(field_class)(_autocomplete_kwargs)

    import djcrud

    original_build = djcrud.Site.build

    def build(self):
        result = original_build(self)
        patch_relation_formfields()
        return result

    djcrud.Site.build = build
