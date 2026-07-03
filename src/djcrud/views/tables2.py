import functools

import django_tables2
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .log import ADDITION, CHANGE, DELETION, format_logentry_message

from .. import tags


class ActionsColumn(django_tables2.Column):
    empty_values = ()
    template_name = "djcrud/_actions_column.html"
    exclude_from_export = True

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("verbose_name", _("Actions"))
        kwargs.setdefault("orderable", False)
        kwargs.setdefault(
            "attrs",
            {
                "th": {"class": "has-text-right"},
                "td": {"class": "has-text-right"},
            },
        )
        super().__init__(*args, **kwargs)

    def render(self, record, table):
        actions = table.view.router.get_tagged_views(
            tags.OBJECT,
            request=table.view.request,
            object=record,
        )
        context = {
            "actions": actions,
            "view": table.view,
            "record": record,
        }
        return render_to_string(self.template_name, context, request=table.view.request)


class CheckboxColumn(django_tables2.Column):
    """Selection checkbox column for the list action bar.

    Only rendered for rows where the current user has at least one permitted
    ``list_action`` (via ``router.get_tagged_views(tags.LIST_ACTION, object=record)``).

    Each checkbox receives ``data-pk`` plus ``data-list-actions="codename,..."``
    listing exactly which list actions are allowed for that row. The
    ``<list-action-bar>`` component uses these attributes to show only the
    actions permitted for the entire current selection.
    """

    empty_values = ()
    template_name = "djcrud/_checkbox_column.html"
    exclude_from_export = True

    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "verbose_name", mark_safe(render_to_string("djcrud/_checkbox_header.html"))
        )
        kwargs.setdefault("orderable", False)
        super().__init__(*args, **kwargs)

    def render(self, record, table):
        actions = table.view.router.get_tagged_views(
            tags.LIST_ACTION,
            request=table.view.request,
            object=record,
        )
        if not actions:
            return ""
        return render_to_string(
            self.template_name,
            {
                "record": record,
                "allowed_actions": [a.codename for a in actions],
            },
            request=table.view.request,
        )


def _logentry_field_verbose_name(field_name):
    from django.contrib.admin.models import LogEntry

    return LogEntry._meta.get_field(field_name).verbose_name


class LogActionColumn(django_tables2.Column):
    colors = {
        ADDITION: "success",
        CHANGE: "warning",
        DELETION: "danger",
    }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "verbose_name",
            _logentry_field_verbose_name("action_flag"),
        )
        kwargs.setdefault("orderable", True)
        super().__init__(*args, **kwargs)

    def render(self, value, record=None):
        if record is None:
            return format_html('<span class="tag is-light">{}</span>', value)
        return format_html(
            '<span class="tag is-{}">{}</span>',
            self.colors.get(record.action_flag, "light"),
            record.get_action_flag_display(),
        )


class LogMessageColumn(django_tables2.Column):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "verbose_name",
            _logentry_field_verbose_name("change_message"),
        )
        kwargs.setdefault("orderable", False)
        super().__init__(*args, **kwargs)

    def render(self, value):
        return format_logentry_message(value)


class Tables2Mixin:
    """django-tables2 integration for list views.

    Attributes:
        table_template (str): Partial template wrapping the rendered table.
        table_attributes (dict): Extra attributes on the generated
            ``Table`` subclass.
    """

    table_template = "djcrud/_tables2.html"

    def _declared_table_fields(self):
        for cls in type(self).__mro__:
            if "table_fields" in cls.__dict__:
                value = cls.__dict__["table_fields"]
                if isinstance(value, list):
                    return list(value)
                break
        return None

    def _auto_table_fields(self):
        all_fields = [
            f.name
            for f in self.model_meta.get_fields()
            if f.concrete and not f.is_relation
        ]
        pk_field = self.model_meta.pk.name if self.model_meta.pk else "id"
        fields = [pk_field]

        for f in all_fields:
            if f not in fields and len(fields) < 4:
                fields.append(f)
                if len(fields) == 4:
                    break

        if self.add_actions:
            fields.append("actions")

        return fields

    @functools.cached_property
    def table_fields(self):
        """Column names from clone or auto-detected model fields."""
        if declared := self._declared_table_fields():
            return declared
        return self._auto_table_fields()

    @functools.cached_property
    def resolved_table_fields(self):
        fields = list(self.table_fields)
        if self.add_checkbox and "checkbox" not in fields:
            fields.insert(0, "checkbox")
        return fields

    @functools.cached_property
    def table_meta(self):
        return type(
            "Meta",
            tuple(),
            dict(
                model=self.model,
                fields=self.resolved_table_fields,
                template_name=self.table_template,
            ),
        )

    @functools.cached_property
    def table_class(self):
        attributes = getattr(self, "table_attributes", {})
        if "Meta" not in attributes:
            attributes["Meta"] = self.table_meta

        if "actions" in attributes["Meta"].fields and "actions" not in attributes:
            attributes["actions"] = ActionsColumn()

        if "checkbox" in attributes["Meta"].fields and "checkbox" not in attributes:
            attributes["checkbox"] = CheckboxColumn()

        cls = type(
            f"{self.model.__name__}Table",
            (django_tables2.Table,),
            attributes,
        )
        return cls

    @functools.cached_property
    def table(self):
        """Rendered django-tables2 ``Table`` for the current object list."""
        table = self.table_class(self.object_list)

        table.view = self

        django_tables2.RequestConfig(self.request).configure(table)

        return table

    @functools.cached_property
    def add_actions(self):
        """Whether to add an per-row actions column."""
        return any(self.router._iter_tagged_routes(tags.OBJECT))

    @functools.cached_property
    def add_checkbox(self):
        """Whether to add list-action selection checkboxes.

        When true, a ``CheckboxColumn`` is inserted. Checkboxes are only
        emitted for rows that have at least one allowed list action (computed
        per-row via ``get_tagged_views(..., object=record)``), and carry
        ``data-list-actions`` so the bar can filter actions client-side.
        """
        return any(self.router._iter_tagged_routes(tags.LIST_ACTION))

    def sort_url(self, column):
        """URL toggling sort order for *column*."""
        return self.querystring(
            **{
                self.table.prefixed_order_by_field: column.order_by_alias.next,
            }
        )
