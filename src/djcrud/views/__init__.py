"""
djcrud view classes (frontend-agnostic).

Re-exports generic CRUD views from .generic and other view helpers.
These views provide context for templates but don't specify which templates to use.
Frontend apps (like djcrud_bootstrap) provide the actual templates.

Usage:
    from djcrud.views import ListView, CreateView
    # or
    from djcrud.views.generic import ListView, CreateView
"""

# The generic CRUD views live in .generic (per user request: "we don't want our
# generic crud views in views/__init__.py, we want them in djcrud/views/generic.py").
# We re-export * from .generic here so `from djcrud.views import ListView` (and
# the rest of the public API) continues to work without breaking existing code.
from .generic import *
from .form import FormView
from .tables2 import Tables2Mixin
from .template import TemplateView

