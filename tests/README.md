# djcrud Test Suite

## Overview

This test suite validates the djcrud framework based on the **actual usage patterns** demonstrated in `djcrud_example` and `djcrud_auth`.

## Test Structure

```
tests/
├── settings.py           # Django test settings (SQLite in-memory)
├── urls.py              # Minimal URL configuration for tests
├── conftest.py          # Pytest fixtures (requests, users)
├── test_attribute.py    # Tests for @getter and @cached descriptors
├── test_clonable.py     # Tests for Clonable mixin and .clone()
├── test_mvc.py          # Tests for Controller and View classes
├── test_menu.py         # Tests for menu.get_menu() function
└── test_integration.py  # Integration tests of full controller hierarchy
```

## Test Files

### test_attribute.py
Tests the descriptor system (`djcrud.attribute`):
- `getter` - Non-caching dual class/instance property
- `cached` - Caching dual class/instance property
- Tests cover: class access, instance access, caching behavior, inheritance, metadata preservation

### test_clonable.py
Tests the `Clonable` mixin:
- `clone()` method creates subclasses dynamically
- Attribute override via kwargs
- Mixin injection via positional args
- Smart naming with model prefixes
- Method preservation and chaining

### test_mvc.py
Tests `Controller` and `View` classes:
- Controller initialization and urlpatterns generation
- View properties: `urlpath`, `urlname`, `urlpatterns`
- View cloning with attributes and models
- Permission system: `has_perm` (secure by default, requires superuser)
- Integration with Django's CBV system

### test_menu.py
Tests the menu system (`djcrud.menu.get_menu`):
- Filtering views by menu name
- Permission checking (`has_perm()`)
- View instantiation with request and kwargs
- Handling views with/without menus attribute

### test_integration.py
Full integration tests:
- Nested controller hierarchies (like `AuthController > UserController`)
- Multiple views in controllers
- Cloned views in controllers (like `TemplateView.clone()`)
- Model binding to views
- Permission system across hierarchy
- Real-world example replicating `djcrud_example/urls.py`

## Test Data

Uses Django's built-in models:
- `django.contrib.auth.models.User`
- `django.contrib.auth.models.Group`

No custom test models needed - everything uses real Django models.

## Fixtures (conftest.py)

- `rf` - Django RequestFactory
- `user` - Regular user (not staff, not superuser)
- `superuser` - Superuser for permission tests
- `anonymous_request` - Request with AnonymousUser
- `user_request` - Request with authenticated regular user
- `superuser_request` - Request with authenticated superuser

## Running Tests

```bash
# Install dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run specific test file
pytest tests/test_attribute.py

# Run with coverage
pytest --cov=djcrud --cov-report=html

# Run verbose
pytest -v

# Run specific test
pytest tests/test_mvc.py::TestView::test_view_has_perm_with_superuser
```

## Test Philosophy

1. **Use real Django models** - No artificial test models, use User/Group
2. **Test actual usage** - Based on `djcrud_example` and `djcrud_auth` patterns
3. **Test the public API** - Focus on how users will use the framework
4. **Secure by default** - Validate that default permissions are restrictive
5. **Integration over mocking** - Test real Django integration where possible

## Known Issues to Fix

Before tests can pass, these bugs need fixing in `src/djcrud/mvc.py`:

1. **Line 28**: `results` should be `result` (typo in Controller.urlpatterns)
2. **Line 47**: `cls` should be `self` (typo in View.urlpatterns)
3. **Line 54**: `request.is_superuser()` should be `request.user.is_superuser`

## Coverage Goals

- **attribute.py**: 100% (critical foundation)
- **mvc.py**: 95%+ (core framework)
- **menu.py**: 90%+
- **Integration**: 85%+ (key workflows)
