"""Explicit constants for the well-known tags used with Router.get_tagged_views().

These define the contracts for introspected menus (sidebar, model actions,
per-object actions, list action bar, topbar).

Using the constants makes the "menus introspected, not hardcoded" mechanism
robust and self-documenting.
"""

NAVIGATION = "navigation"
MODEL = "model"
OBJECT = "object"
LIST_ACTION = "list_action"
TOPBAR = "topbar"
