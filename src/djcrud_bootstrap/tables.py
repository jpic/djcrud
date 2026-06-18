"""
Bootstrap-specific django-tables2 customizations.
"""

import django_tables2 as tables
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class ActionsColumn(tables.Column):
    """
    Renders action buttons for object menu items.

    Automatically renders buttons for all views with 'object' in menus.
    Uses Unpoly to open forms in modals.
    """

    empty_values = ()  # Always render, even if value is None
    orderable = False

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('verbose_name', 'Actions')
        super().__init__(*args, **kwargs)

    def render(self, record, table):
        """
        Render action buttons for this record.

        Gets object_menu from the view and renders buttons.
        """
        # Get view from table (set in Tables2Mixin.get_table)
        view = getattr(table, '_djcrud_view', None)
        if not view or not view._controller:
            return ''

        # Get object menu for this specific record
        from djcrud.menu import get_menu
        actions = get_menu(view._controller, 'object', view.request, object=record)

        if not actions:
            return ''

        # Render buttons
        buttons = []
        for action in actions:
            # Determine if this action should open in modal
            is_modal_action = any(
                keyword in action.__class__.__name__.lower()
                for keyword in ['create', 'update', 'delete', 'edit']
            )

            if is_modal_action:
                # Unpoly attributes for modal
                btn_class = 'danger' if 'delete' in action.__class__.__name__.lower() else 'primary'
                button_html = format_html(
                    '<a href="{}" class="btn btn-sm btn-outline-{}" '
                    'up-layer="new modal" up-size="medium">'
                    '<i class="bi bi-{}"></i> {}</a>',
                    action.url,
                    btn_class,
                    action.icon if hasattr(action, 'icon') else 'pencil',
                    action.title
                )
            else:
                # Regular link
                button_html = format_html(
                    '<a href="{}" class="btn btn-sm btn-outline-primary">'
                    '<i class="bi bi-{}"></i> {}</a>',
                    action.url,
                    action.icon if hasattr(action, 'icon') else 'eye',
                    action.title
                )

            buttons.append(button_html)

        # Join the SafeStrings and wrap in a div
        # mark_safe is needed because we're joining already-safe strings
        return mark_safe(f'<div class="btn-group btn-group-sm">{" ".join(buttons)}</div>')


__all__ = ['ActionsColumn']
