"""
Tables2 support for djcrud views using django-tables2.

Moved from mixins.py. Uses table_fields getter and generates Table
dynamically with model and fields (no longer relies on UserTable or Meta in subclasses).
"""

import django_tables2 as tables
from django_tables2 import RequestConfig
from djcrud import attribute
from djcrud.mvc import View  # base for Tables2Mixin (avoids circular import with views/__init__.py)


class Tables2Mixin(View):
    """
    Add django-tables2 support to ListView.

    We never define a get_context_data method, because our view returns
    the view object in the context. As such, the templates can access all
    attributes and methods of the view object (e.g. view.table, view.table_fields).

    Uses self.table_fields (getter) and dynamically creates Table with
    model=self.model and fields=self.table_fields. Subclasses should not
    override with a hardcoded *Table class anymore.
    """
    table_pagination = {'per_page': 25}

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
            class FallbackTable(tables.Table):
                class Meta:
                    template_name = 'django_tables2/bootstrap5.html'
                    attrs = {'class': 'table table-striped table-hover'}

            return FallbackTable

        # Check if we need to add actions column
        # Look for any views with 'object' in their menus
        add_actions = False
        if self._controller:
            for v in self._controller.views:
                if hasattr(v, 'menus') and 'object' in getattr(v, 'menus', []):
                    add_actions = True
                    break

        # Build fields list (data fields + actions if needed)
        fields_list = list(self.table_fields)
        if add_actions and 'actions' not in fields_list:
            fields_list.append('actions')

        # Create Meta class first to avoid closure issues
        class TableMeta:
            model = self.model
            fields = fields_list
            template_name = 'django_tables2/bootstrap5.html'
            attrs = {'class': 'table table-striped table-hover'}

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

        # Dynamically add actions column if needed
        if add_actions:
            try:
                from djcrud_bootstrap.tables import ActionsColumn
                DynamicTable.base_columns['actions'] = ActionsColumn()
            except ImportError:
                # djcrud_bootstrap not installed, skip actions column
                pass

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
        puts Tables2Mixin before the base view's get_context_data).
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
