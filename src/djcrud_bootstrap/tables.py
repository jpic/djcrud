"""
Bootstrap-specific django-tables2 customizations.

The shared ActionsColumn (in djcrud.views.tables2) now uses the
djcrud/_actions_column.html template provided here.
"""

from djcrud.views.tables2 import ActionsColumn

__all__ = ["ActionsColumn"]
