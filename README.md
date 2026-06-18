# djcrud

**Declarative Django CRUD — frontend agnostic and minimalist.**

`djcrud` lets you build complete admin-like interfaces with almost zero boilerplate using simple `Controller` and `View` classes. The core is completely decoupled from UI frameworks; install `djcrud-bootstrap` (or build your own) for Bootstrap 5 templates, CSS, and components.

```bash
pip install djcrud djcrud-bootstrap
```

[![Tests](https://img.shields.io/badge/tests-108%20passing-brightgreen)](tests/)
[![Django](https://img.shields.io/badge/Django-4.2%2B-092E20)](https://www.djangoproject.com/)

## Why djcrud?

- **View-centric templates**: Everything lives on the `view` object in context (`{{ view.title }}`, `{{ view.table }}`, `{{ view.main_menu }}`). No manual `get_context_data()`.
- **Powerful descriptors**: `@attribute.getter` / `@attribute.cached` work on both classes *and* instances (the heart of the framework).
- **Clone instead of subclass**: `MyView.clone(icon='star', menus=['main'])` — clean, flexible configuration.
- **Secure by default**: Permissions must be explicitly enabled.
- **Swap frontends easily**: Core has zero HTML/CSS. Use Bootstrap today, Tailwind tomorrow.
- **Well tested**: 108 passing tests with real integration examples.

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
    "crispy_bootstrap5",
    "djcrud",           # Core framework (no templates)
    "djcrud_bootstrap", # Provides djcrud/*.html templates + Bootstrap 5
    # "myapp",          # Your models + CRUD controllers
]

CRISPY_TEMPLATE_PACK = "bootstrap5"
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
            menus=["main"],
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
from djcrud import crud, views
from djcrud.views.tables2 import Tables2Mixin

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # ... your fields

class ProductListView(Tables2Mixin, views.ListView):
    menus = ["main"]   # Appears in sidebar
    # title, icon, table, model_menu automatically provided

ProductController = crud.ModelController.clone(model=Product)
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
- **`crud.ModelController.clone(model=MyModel)`**: One-liner for full CRUD on any model.
- **Menus**: Declare `menus = ['main', 'model']` on views. Sidebar + action buttons appear automatically.
- **Tables**: Mix in `Tables2Mixin` for automatic django-tables2 support (`table_fields` + dynamic `Table` class).

**Template example** (Bootstrap frontend):

```html
<h1>
    {% if view.icon %}<i class="bi bi-{{ view.icon }}"></i>{% endif %}
    {{ view.title }}
</h1>
{% if view.model_menu %}
    {% for action in view.model_menu %}
    <a href="{{ action.url }}">{{ action.title }}</a>
    {% endfor %}
{% endif %}
{% render_table view.table %}
```

## Installation & Setup

See the Quick Start above and `djcrud_example/settings.py` for a complete configuration. Key points:
- Add `djcrud` + a frontend (`djcrud_bootstrap` recommended).
- Configure crispy-forms for Bootstrap 5.
- No special middleware or context processors are required for basic usage (advanced menu features can use `djcrud.context_processors.djcrud_context`).

Full test suite: `pytest` (108 tests passing).

## Documentation & Architecture

- `tests/` — Real-world usage patterns and integration tests.
- `djcrud_example/` — Fully working demo project.

**djcrud** — Simple, declarative Django CRUD that stays out of your way.
