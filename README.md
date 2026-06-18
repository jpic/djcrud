# djcrud

**Declarative Django CRUD — frontend agnostic and minimalist.**

`djcrud` lets you build complete admin-like interfaces with almost zero boilerplate using simple `Controller` and `View` classes. The core is completely decoupled from UI frameworks; install `djcrud-bootstrap` (or build your own) for Bootstrap 5 templates, CSS, and components.

```bash
pip install djcrud djcrud-bootstrap
```

[![Tests](https://img.shields.io/badge/tests-117%20passing-brightgreen)](tests/)
[![Django](https://img.shields.io/badge/Django-5.1%2B-092E20)](https://www.djangoproject.com/)

## Why djcrud?

- **View-centric templates**: Everything lives on the `view` object in context (`{{ view.title }}`, `{{ view.table }}`). No manual `get_context_data()` or custom template tags.
- **`{% eval %}` template tag**: Call any Python function/method with args/kwargs directly in templates. Skip the boilerplate of `get_context_data()` and custom template tags entirely.
- **Powerful descriptors**: `@attribute.getter` / `@attribute.cached` work on both classes *and* instances (the heart of the framework).
- **Clone instead of subclass**: `MyView.clone(icon='star', tags=['main'])` — clean, flexible configuration.
- **Secure by default**: Permissions must be explicitly enabled.
- **Swap frontends easily**: Core has zero HTML/CSS. Use Bootstrap today, Tailwind tomorrow.
- **Well tested**: 117 passing tests with real integration examples.

## Quick Start

1. **Install**:

```bash
pip install djcrud djcrud-bootstrap django-tables2 django-crispy-forms crispy-bootstrap5
```

2. **settings.py** (see full example in `djcrud_example/settings.py`):

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_tables2",
    "crispy_forms",
    "crispy_bootstrap5",  # for djcrud_bootstrap (optional with bulma)
    "djcrud",             # Core framework (no templates)
    "djcrud_bulma",       # or "djcrud_bootstrap" (or both); installs crispy-bulma for CRISPY_TEMPLATE_PACK="bulma"
    # "myapp",            # Your models + CRUD controllers
]

# Frontend is **auto-detected** by the installed frontend's AppConfig.ready()
# (sets DJCRUD_FRONTEND, CRISPY_TEMPLATE_PACK="bulma", CRISPY_ALLOWED_TEMPLATE_PACKS, etc.).
# Uses crispy-bulma package templates exclusively (no custom bulma/ overrides or duplication).
# Install with `pip install djcrud[bulma]` or `djcrud[bootstrap]`.
```

3. **urls.py**:

```python
from django.contrib import admin
from django.urls import path

from djcrud import mvc
from djcrud.views.template import TemplateView
# from myapp.crud import ProductController

site = mvc.Controller(
    views=[
        TemplateView.clone(
            icon="house",
            template_name="djcrud/home.html",
            title="My App",
            title_heading="Welcome to My App",
            tags=["main"],
            urlname="home",
            urlpath="",
            has_perm=True,  # Public home page
        ),
        # ProductController,  # Add your model controllers here
    ]
)

urlpatterns = [
    path("admin/", admin.site.urls),
] + site.urlpatterns
```

4. **Add a model** (`myapp/crud.py`):

```python
from django.db import models
from djcrud import mvc
from djcrud.views import ListView
from djcrud.views.tables2 import Tables2Mixin

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # ... your fields

class ProductListView(Tables2Mixin, ListView):
    tags = ["main"]   # Appears in sidebar
    # title, icon, table automatically provided

ProductController = mvc.Controller.clone(model=Product, views=[ProductListView])
```

Add `ProductController` to your root `site.views` list. You instantly get list/create/update/detail views, tables, menus, permissions, and Bootstrap styling.

Run:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to see it in action. See `djcrud_example/` for a complete working demo (including auth).

## Key Concepts

### The `attribute` Module
The heart of `djcrud`. Descriptors that work on **both classes and instances**.

```python
from djcrud import attribute

class MyView:
    cls = attribute.cls()          # Always the class

    @attribute.getter
    def title(self):
        if self.model:
            return self.model._meta.verbose_name_plural.capitalize()
        return "List"

    @attribute.cached
    def icon(self):
        return "list"
```

### MVC Pattern
- **`mvc.Controller`**: Groups views/controllers, handles URL namespacing and menu hierarchy.
- **`mvc.View`**: Base for list/create/update/detail. Provides `url()`, `has_perm`, `root_controller`, etc.
- **`mvc.Controller.clone(model=MyModel, views=[MyListView, ...])`**: One-liner for full CRUD on any model.
- **Tags**: Declare `tags = ['main', 'model']` on views to categorize them. Use `controller.get_tagged_views()` to retrieve them.
- **Tables**: Mix in `Tables2Mixin` for automatic django-tables2 support (`table_fields` + dynamic `Table` class).

### The `{% eval %}` Template Tag

The `{% eval %}` tag lets you call any Python function/method with arguments directly in templates, just like Jinja2:

```django
{% load djcrud_tags %}

{# Call a method with positional and keyword arguments #}
{% eval view.controller.get_tagged_views 'model' request exclude_current=view as model_menu %}

{% for action in model_menu %}
    <a href="{{ action.url }}">{{ action.title }}</a>
{% endfor %}
```

**Why this matters:**

Traditional Django forces you to write boilerplate:
- Custom template tags for every function call
- Override `get_context_data()` to inject values
- Template tag libraries that duplicate view logic

With `{% eval %}`, you:
- **Keep logic in views** where it belongs (Python, not template syntax)
- **Call methods directly** with the exact arguments you need
- **Eliminate boilerplate** - no custom tags, no `get_context_data()` overrides
- **Use generic, reusable functions** instead of template-specific code

**Template example** (Bootstrap frontend):

```html
{% load djcrud_tags %}

<h1>
    {% if view.icon %}<i class="bi bi-{{ view.icon }}"></i>{% endif %}
    {{ view.title }}
</h1>

{# Get action buttons for this model #}
{% if view.controller %}
    {% eval view.controller.get_tagged_views 'model' request exclude_current=view as model_menu %}
    {% for action in model_menu %}
        <a href="{{ action.url }}" class="btn btn-primary">
            {% if action.icon %}<i class="bi bi-{{ action.icon }}"></i>{% endif %}
            {{ action.title }}
        </a>
    {% endfor %}
{% endif %}

{% render_table view.table %}
```

## Installation & Setup

See the Quick Start above and `djcrud_example/settings.py` for a complete configuration. Key points:
- Add `djcrud` + **one** frontend (`djcrud_bulma` or `djcrud_bootstrap`).
- Frontend is auto-detected (sets `DJCRUD_FRONTEND`, crispy/tables2 config, etc.) via `AppConfig.ready()`. No manual setting needed.
- No special middleware or context processors are required. `mvc.View.get_context_data` injects `view` (with `view.main_menu`, `view.root_controller`, etc.) and `site_controller` (alias for root_controller) into templates.

Full test suite: `tox` (Python 3.14 + Django 5.1+, tests both `djcrud_bulma` and `djcrud_bootstrap` frontends; all 117 tests pass).

## Philosophical Lessons

This project taught several hard-won lessons about sustainable Django development:

- **Templates over Python duplication**: Repeated frontend logic (actions column, confirm dialogs, table classes) belongs in templates. A single shared `ActionsColumn` + `djcrud/_actions_column.html` (and `confirm.html`/`delete.html`) eliminated duplicate Python code between `bulma`/`bootstrap` while keeping styling idiomatic. The `render_to_string()` + `partialdef content` pattern with Unpoly/Django 6 partials proved far cleaner than subclassing columns or settings.

- **Minimal settings and auto-detection**: Settings like `DJCRUD_ACTIONS_COLUMN`, `DJCRUD_TABLES2_ATTRS` became unnecessary. `AppConfig.ready()` + frontend-specific templates handle everything. Less configuration = less maintenance.

- **View-centric design wins**: Everything on `{{ view }}` (`view.title`, `view.model_fields`, `view.table`) makes templates declarative and eliminates `get_context_data()` boilerplate. The `{% eval %}` template tag lets you call any view method or controller method directly from templates with arguments, eliminating the need for custom template tags entirely. The `@attribute.getter`/`cached` descriptors (the true heart of djcrud) make this possible without magic. Keep your logic in Python (views/controllers), not in template tag libraries.

- **Clone over subclass**: `Controller.clone()` and `View.clone(...)` provide flexible configuration without deep inheritance hierarchies. This pattern scales beautifully.

- **Test everything, including the frontend**: The tox matrix, `pytest.mark.bulma`/`bootstrap`, and integration tests caught template rendering, Unpoly modal partials, and table attrs issues early. "It works on my machine" is not enough.

- **Delete more than you add**: Removing custom template tags (replaced with `{% eval %}`), `DJCRUD_*` settings, duplicated column classes, middleware, deprecated files (no backward compatibility needed), and comments about old approaches kept the codebase small and focused. The `{% eval %}` tag alone eliminated the need for `get_model_fields`, `get_menu`, and other custom template tags - one generic tag handles all function calls. The right amount of complexity is exactly what the task requires—no speculative abstractions.

These principles turned what could have been a sprawling admin framework into something lightweight, extensible, and a joy to extend.

## Documentation & Architecture

- `tests/` — Real-world usage patterns and integration tests.
- `djcrud_example/` — Fully working demo project.

**djcrud** — Simple, declarative Django CRUD that stays out of your way.
