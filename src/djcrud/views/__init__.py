"""
djcrud view classes (frontend-agnostic).

Re-exports generic CRUD views from .generic and other view helpers.
These views provide context for templates but don't specify which templates to use.
Frontend apps (like djcrud_bulma) provide the actual templates.

Usage:
    from djcrud.views import ListView, CreateView
    # or
    from djcrud.views.generic import ListView, CreateView
"""

from .generic import *
from .form import FormView
from .tables2 import Tables2Mixin
from .spa import SPAView
from .template import TemplateView