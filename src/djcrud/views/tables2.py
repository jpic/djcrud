"""
Tables2 support for djcrud views using django-tables2.

Moved from mixins.py. Uses table_fields getter and generates Table
dynamically with model and fields (no longer relies on UserTable or Meta in subclasses).
"""

import django_tables2 as tables
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.module_loading import import_string
from django_tables2 import RequestConfig
from djcrud import attribute
from djcrud.mvc import View  # base for Tables2Mixin (avoids circular import with views/__init__.py)


class ActionsColumn(tables.Column):
    """
    Shared django-tables2 column for object actions.

    Uses the frontend-specific djcrud/_actions_column.html template
    (provided by djcrud_bulma and djcrud_bootstrap) to render buttons
    for the object menu. The template receives `actions` (from get_menu)
    and the view (via table._djcrud_view).
    """

    empty_values = ()  # Always render column
    template_name = "djcrud/_actions_column.html"
    exclude_from_export = True

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("verbose_name", "Actions")
        kwargs.setdefault("orderable", False)  # Ensure column cannot be sorted
        super().__init__(*args, **kwargs)

    def render(self, record, table):
        """Provide context for the template (actions list + view reference)."""
        view = getattr(table, "_djcrud_view", None)
        if not view or not view._controller:
            return ""

        from djcrud.menu import get_menu
        actions = get_menu(
            view._controller, "object", view.request, object=record
        )
        if not actions:
            return ""

        # Render the frontend-specific template with context
        # (table._djcrud_view provides full view context for templates)
        context = {
            "actions": actions,
            "view": view,
            "record": record,
        }
        return render_to_string(self.template_name, context, request=view.request)


class Tables2Mixin(View):
    """
    Add django-tables2 support to ListView.

    We never define a get_context_data method (the base mvc.View provides one that injects
    `view=self` and `site_controller=root_controller` for templates). Templates can access all
    attributes and methods of the view object (e.g. view.table, view.table_fields, view.main_menu).

    Uses self.table_fields (getter) and dynamically creates Table with
    model=self.model and fields=self.table_fields. Subclasses should not
    override with a hardcoded *Table class anymore.
    """
    table_pagination = {'per_page': 25}
    table_template_name = None
    # table_attrs removed: classes now hardcoded in frontend table templates (bulma.html + bootstrap5.html)
    # (consistent with philosophy of preferring templates over Python/settings for frontend differences)

    def get_table_template_name(self):
        """Frontend-specific table template (set by AppConfig.ready() in djcrud_bulma or djcrud_bootstrap)."""
        return (
            self.table_template_name
            or getattr(
                settings,
                'DJCRUD_TABLES2_TEMPLATE',
                'django_tables2/bootstrap5.html',
            )
        )


    @attribute.getter
    def table_fields(self):
        """Return list of fields for the table: 'id' + first 3 model fields.

        If 'id' is already in the first fields, it avoids duplication.
        Uses model's _meta.get_fields() for reliable field ordering.
        """
        if not self.model:
            return ['id']

        try:
            # Get all concrete fields in declaration/ Meta order
            all_fields = [
                f.name for f in self.model_meta.get_fields()
                if f.concrete and not f.is_relation  # avoid relations for basic tables
            ]
            # Ensure 'id' or 'pk' is first if present
            pk_field = self.model_meta.pk.name if self.model_meta.pk else 'id'
            fields = [pk_field]

            # Add up to first 3 other fields (avoiding pk duplicate)
            for f in all_fields:
                if f not in fields and len(fields) < 4:  # id + 3 others = 4 max
                    fields.append(f)
                    if len(fields) == 4:
                        break

            return fields
        except (AttributeError, TypeError):
            # Fallback for non-model or errors
            return ['id']

    @attribute.getter
    def table_class(self):
        """Return a django-tables2 Table class configured for this model and fields.

        Must return a Table (not a UserTable or similar hardcoded class).
        Uses the table_fields getter and adds Actions column if object_menu exists.
        """
        if not self.model:
            # Fallback generic table
            table_template_name = self.get_table_template_name()

            class FallbackTable(tables.Table):
                class Meta:
                    template_name = table_template_name

            return FallbackTable

        # Check if we need to add actions column
        # Look for any views with 'object' in their tags
        add_actions = False
        if self._controller:
            for v in self._controller.views:
                if hasattr(v, 'tags') and 'object' in getattr(v, 'tags', []):
                    add_actions = True
                    break

        # Build fields list (data fields + actions if needed)
        fields_list = list(self.table_fields)
        if add_actions and 'actions' not in fields_list:
            fields_list.append('actions')

        # Create Meta class first to avoid closure issues
        table_template_name = self.get_table_template_name()

        class TableMeta:
            model = self.model
            fields = fields_list
            template_name = table_template_name

        # Create the table class
        class DynamicTable(tables.Table):
            Meta = TableMeta

        # Make ID/PK column link to detail view if model has get_absolute_url
        # Check if instances of this model will have get_absolute_url method
        try:
            # Try to check if the model class or instances have get_absolute_url
            has_get_absolute_url = (
                hasattr(self.model, 'get_absolute_url') or
                'get_absolute_url' in dir(self.model)
            )
        except (AttributeError, TypeError):
            has_get_absolute_url = False

        if has_get_absolute_url:
            pk_field = self.model._meta.pk.name if self.model._meta.pk else 'id'
            if pk_field in fields_list:
                # Use a custom column that calls get_absolute_url on each record
                from django.utils.html import format_html

                class PKLinkColumn(tables.Column):
                    def render(self, value, record):
                        if hasattr(record, 'get_absolute_url'):
                            return format_html('<a href="{}">{}</a>', record.get_absolute_url(), value)
                        return value

                DynamicTable.base_columns[pk_field] = PKLinkColumn()

        if add_actions:
            DynamicTable.base_columns['actions'] = ActionsColumn()

        return DynamicTable

    @attribute.cached
    def table(self):
        """Return the configured table instance for templates.

        Templates access this via {{ view.table }}. Calls get_table() internally.
        """
        return self.get_table()

    def get_table(self, **kwargs):
        """Create and configure the table instance.

        Called from templates via {{ view.table }} (or directly if mixin order
        puts Tables2Mixin before the base view's get_context_data from mvc.View).
        """
        table_class = self.table_class  # uses the getter
        queryset = self.get_queryset()
        table = table_class(queryset, **kwargs)

        # Store reference to view so ActionsColumn can access it
        table._djcrud_view = self

        # Configure pagination
        RequestConfig(
            self.request,
            paginate=self.table_pagination
        ).configure(table)

        return table
