"""
djcrud mixins for adding functionality to views.
"""

import django_tables2 as tables
from django_tables2 import RequestConfig


class Tables2Mixin:
    """
    Add django-tables2 support to ListView.

    Adds 'table' to context with a configured django-tables2 table instance.
    Subclasses can override table_class or define it as a @cached property.
    """
    table_class = None
    table_pagination = {'per_page': 25}

    def get_table_class(self):
        """Get or auto-generate the table class."""
        if self.table_class:
            return self.table_class

        # Auto-generate table from model
        class AutoTable(tables.Table):
            class Meta:
                model = self.model
                template_name = 'django_tables2/bootstrap5.html'
                attrs = {'class': 'table table-striped table-hover'}

        return AutoTable

    def get_table(self, **kwargs):
        """Create and configure the table instance."""
        table_class = self.get_table_class()
        queryset = self.get_queryset()
        table = table_class(queryset, **kwargs)

        # Configure pagination
        RequestConfig(
            self.request,
            paginate=self.table_pagination
        ).configure(table)

        return table

    def get_context_data(self, **kwargs):
        """Add table to context."""
        context = super().get_context_data(**kwargs)
        context['table'] = self.get_table()
        return context
