# djcrud test suite

Tests for the djcrud framework and tutorial example apps in `src/djcrud_example/`.

## Running tests

```bash
# Fast Python tests (parallel)
pytest -m "not splinter" -n auto

# Browser tests (serial; requires Firefox + geckodriver)
pytest -m splinter -n 0 --splinter-headless

# Tutorial doc integrity (literalinclude paths)
pytest -m tutorial -n 0

# Full suite
tox
```

## Key markers

| Marker | Purpose |
|--------|---------|
| `splinter` | Browser tests — always use `-n 0` |
| `tutorial` | Validates tutorial example apps referenced from docs |
| `docs_screenshot` | Captures PNGs into `docs/_static/screenshots/` |
| `django_db` | Tests requiring database access |

## Example apps

Tutorial chapters map to example apps:

| App | Tutorial chapter |
|-----|------------------|
| `routing_example` | `docs/tutorial/routing.rst` |
| `security_example` | `docs/tutorial/permission.rst` |
| `views_example` | `docs/tutorial/views.rst` |
| `drf_example` | `docs/tutorial/drf.rst`, `docs/tutorial/agents.rst` (`article_viewset.py`) |
| `spa_example` | `docs/tutorial/spa.rst` |

## Shared fixtures

`conftest.py` provides:

- `_autodiscover_routes` (autouse) — calls `djcrud.site.build()` before each test
- `admin_user` — superuser (`admin` / `password`)
- `browser_login` — Splinter login helper
- `routing_bulk_items` — seeded `Item` rows for browser tests
- `many_users` — paginated user list for filter/browser tests

See `docs/contributing.rst` for the full development guide.