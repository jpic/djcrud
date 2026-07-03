# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**djcrud** is a Python/Django MVC framework that provides a thin abstraction layer over Django, enabling faster development through convention over configuration. It removes repetitive wiring while keeping Django's models, permissions, and generic views intact.

- **Language:** Python 3.8+
- **Framework:** Django 5.1+
- **Philosophy:** Structure is code, not configuration; sane defaults with surgical overrides

## Common Development Commands

### Running Tests

```bash
# Fast Python tests (parallel)
pytest -m "not splinter" -n auto

# Browser tests (serial, requires Firefox + geckodriver)
pytest -m splinter -n 0 --splinter-headless

# Single test file
pytest tests/test_routing_example.py -v

# JavaScript tests (Vitest with happy-dom)
npm test

# Tutorial validation
pytest -m tutorial -n 0

# Full test suite
tox
```

**Important Test Markers:**
- `splinter` - Browser tests; must use `-n 0` (serial execution)
- `docs_screenshot` - Generates PNG screenshots for documentation
- `tutorial` - Validates literalinclude paths in docs
- `django_db` - Tests requiring database access

### Development Setup

```bash
# Development install with all extras
pip install --pre -e ".[dev,docs]"

# JavaScript tools (optional, for JS unit tests)
npm ci
```

Note: The `--pre` flag is required for pre-release dependency versions (django-autocomplete-light>=5.1).

### Running the Example Project

```bash
# From repository root
python manage.py migrate
python manage.py runserver

# Login at http://localhost:8000/auth/login/
# Username: su
# Password: su
```

The example project in `src/djcrud_example/` includes tutorial apps (routing_example, security_example, views_example, drf_example, spa_example).

### Documentation

```bash
# Build Sphinx documentation
make -C docs html

# Regenerate screenshots for documentation
pytest tests/test_docs_screenshots.py -n0 --splinter-headless
```

### Code Quality

```bash
# Format code (line length: 88)
black .

# Lint code
ruff check .
```

## Core Architecture

### Route Hierarchy Pattern

Routers nest views in code rather than urls.py configuration. Structure: **Site → Routers → Views**

```python
# Example: ItemRouter contains ListView, DetailView, CreateView, etc.
class ItemRouter(djcrud.ModelRouter):
    model = Item

djcrud.site.routes.append(ItemRouter)
```

**Key files:** `src/djcrud/route.py`, `src/djcrud/router.py`

### Registry Pattern

Routes are managed by an ordered registry allowing surgical overrides by codename:

```python
class ItemRouter(djcrud.ModelRouter):
    model = Item
    routes = djcrud.ModelRouter.routes + [
        djcrud.generic.ListView.clone(filter_fields=[...]),  # Override default ListView
    ]
```

**Key file:** `src/djcrud/registry.py`

### Clonable Pattern

Views and routers use `.clone()` for runtime specialization without defining new module-level classes:

```python
MyView.clone(
    permission_shortcode='custom',
)
```

Opt models into site search with ``djcrud.add_search(Item)`` in ``djcrud.py``.

**Key file:** `src/djcrud/clonable.py`

### Mixin Composition

Views are built from composable mixins providing focused features:


- **FilterMixin** - QuerySet filtering with django-filter
- **SearchMixin** - Full-text search
- **PaginationMixin** - Pagination with django-tables2
- **ObjectMixin** - Single object views (Detail, Update, Delete)
- **FormMixin** - Form handling with crispy-forms
- **ListActionMixin** - Bulk actions on list views

**Key directory:** `src/djcrud/views/`

### Permission Model

Three-tier permission checking: **View → Router → Django backend**

CRUD operations map to Django permissions:
- `add_<model>` - Create permission
- `change_<model>` - Update permission
- `delete_<model>` - Delete permission
- `view_<model>` - Read permission

Permissions are checked before dispatch.

**Key file:** `src/djcrud/view.py`

### ModelRouter Pattern

A **ModelRouter** automatically generates CRUD routes for a Django model:

```python
class ItemRouter(djcrud.ModelRouter):
    model = Item
    icon = 'inbox'      # Bootstrap Icons name
    color = 'primary'   # Bulma color

    def get_queryset(self, view):
        """Override to scope data per user"""
        return self.model.objects.filter(owner=view.request.user)
```

Routes generated: ListView, DetailView, CreateView, UpdateView, DeleteView, DeleteObjectsView (bulk delete)

**Key files:** `src/djcrud/__init__.py`, `src/djcrud/model.py`

### Template API Pattern

Views are exposed directly to templates - no custom `get_context_data()` needed:

```html
{{ view.title }}
{{ view.breadcrumbs }}
{{ view.model_meta.verbose_name_plural }}
```

**Key file:** `src/djcrud/views/template.py`

### Autodiscovery Pattern

Like Django admin, djcrud uses autodiscovery:

```python
# In urls.py
urlpatterns = djcrud.site.build().urlpatterns

# In each app's djcrud.py
class MyRouter(djcrud.ModelRouter):
    model = MyModel

djcrud.site.routes.append(MyRouter)
```

The `site.build()` call imports all `djcrud.py` modules from installed apps.

**Key file:** `src/djcrud/__init__.py` - Site class with `autodiscover()` and `build()`

### DRF REST API (optional)

Install `djcrud[drf]` for the `djcrud_drf` package:
- `ModelApiRouter` + `ModelViewSet` on `/api/<model>/` (separate from HTML URLs)
- `ModelPermission` reuses `ViewPermissionBackend`
- OpenAPI 3 via `drf-spectacular` at `/api/schema/` and `/api/docs/`

**Key package:** `src/djcrud_drf/`

## Project Structure

```
src/djcrud/              Core framework
src/djcrud_bulma/        Bulma CSS template pack with static assets
src/djcrud_auth/         Authentication router (login, logout, password)
src/djcrud_api/          Bearer token auth and login
src/djcrud_drf/          Optional DRF API layer
src/djcrud_dal/          Django-autocomplete-light integration
src/djcrud_dal_topbar/   Site search in navbar
src/djcrud_history/      Audit logging with LogEntry models
src/djcrud_debug/        Route introspection (debug only, superuser)
src/djcrud_example/      Example Django project with tutorial apps
tests/                  Test suite with conftest.py fixtures
docs/                   Sphinx documentation
```

## Philosophy

These principles guide djcrud's design (from `docs/philosophy.rst`):

- **Structure is code, not configuration** - Routers and views nested in Python, not urls.py
- **Sane defaults, surgical overrides** - Works out of the box; customize via `clone()` and registry
- **View is the template API** - View object exposed to templates directly
- **Security and data scope in one place** - Permissions and queryset filtering in router
- **Menus introspected, not hardcoded** - Views carry tags; navigation built from `get_tagged_views()`
- **Composition over monoliths** - Generic views are stacks of small mixins
- **Django all the way down** - Uses Django's `user.has_perm()`, generic views, standard urlpatterns

## JavaScript Architecture

- **Custom elements** with light DOM (no Shadow DOM)
- **ES modules**, no bundler
- **Unpoly compilers** for progressive enhancement
- Listen for `up:fragment:inserted` for Unpoly compatibility
- Config via HTML attributes and `data-*` hooks

**JavaScript files:** `src/djcrud_bulma/static/djcrud_bulma/js/`

## Important Dependencies

**Core:**
- django-tables2 (table rendering)
- django-crispy-forms (form layout)
- django-filter (QuerySet filtering)
- django-autocomplete-light (autocomplete widgets)
- djhacker (model patching)

**Install order matters:** `dal` and `dal_alight` must come **before** `django.contrib.admin` in INSTALLED_APPS

**Frontend:**
- Unpoly.js (AJAX navigation)
- Bootstrap Icons
- Bulma CSS (with djcrud_bulma template pack)

## Extension Packages

- **djcrud_bulma** - Bulma CSS template pack with HTML templates and static assets
- **djcrud_auth** - Authentication views (login, logout, password change)
- **djcrud_api** - Bearer token auth and login
- **djcrud_drf** - Optional DRF REST API (reuses permission backends)
- **djcrud_dal** - Zero-config autocomplete for relation fields
- **djcrud_dal_topbar** - Site search widget in navbar
- **djcrud_debug** - Debug routing introspection (superuser only)
- **djcrud_history** - Audit logging and global log-entry browser
