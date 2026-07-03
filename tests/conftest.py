import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

import djcrud


def pytest_addoption(parser):
    parser.addoption(
        "--force",
        action="store_true",
        default=False,
        help="Force doc screenshot capture (skip freshness short-circuit)",
    )


def _doc_screenshots_up_to_date():
    from doc_screenshots import DOC_SCREENSHOTS, DOCS_SCREENSHOTS_DIR

    return all(
        (DOCS_SCREENSHOTS_DIR / f"{name}.png").is_file()
        and (DOCS_SCREENSHOTS_DIR / f"{name}.png").stat().st_size > 0
        for name in DOC_SCREENSHOTS
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--force"):
        return
    if not _doc_screenshots_up_to_date():
        return
    skip = pytest.mark.skip(
        reason="doc screenshots up to date (pass --force to regenerate)",
    )
    for item in items:
        if item.get_closest_marker("docs_screenshot"):
            item.add_marker(skip)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "drf: tests requiring djcrud_drf and djangorestframework",
    )


def _ensure_drf_schema_class(settings):
    """tests.urls imports djcrud_drf; set schema class before any urlconf loads."""
    try:
        pytest.importorskip("rest_framework")
        pytest.importorskip("drf_spectacular")
    except Exception:
        return
    settings.REST_FRAMEWORK = {
        "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    }


def _configure_drf(settings):
    _ensure_drf_schema_class(settings)

    installed = list(settings.INSTALLED_APPS)
    for app in ("rest_framework", "drf_spectacular", "djcrud_drf"):
        if app not in installed:
            installed.append(app)
    settings.INSTALLED_APPS = installed
    settings.ROOT_URLCONF = "tests.urls_drf"
    import djcrud_drf

    settings.SPECTACULAR_SETTINGS = djcrud_drf.spectacular_settings()
    djcrud_drf.site.build()


@pytest.fixture
def drf_settings(settings):
    _configure_drf(settings)
    return settings

User = get_user_model()


def grant_model_perm(user, model, action):
    """Grant a default Django model permission (add, change, delete, view)."""
    content_type = ContentType.objects.get_for_model(model)
    codename = f"{action}_{model._meta.model_name}"
    perm = Permission.objects.get(content_type=content_type, codename=codename)
    user.user_permissions.add(perm)


def _enable_bearer_middleware(settings):
    middleware = list(settings.MIDDLEWARE)
    if "djcrud_api.middleware.BearerCsrfMiddleware" not in middleware:
        csrf = middleware.index("django.middleware.csrf.CsrfViewMiddleware")
        middleware.insert(csrf, "djcrud_api.middleware.BearerCsrfMiddleware")
        auth = middleware.index(
            "django.contrib.auth.middleware.AuthenticationMiddleware"
        )
        middleware.insert(auth + 1, "djcrud_api.middleware.BearerUserMiddleware")
        settings.MIDDLEWARE = middleware


@pytest.fixture(autouse=True)
def _autodiscover_routes(settings, request):
    """Register per-app routes; mount API URLs unless the test sets its own urlconf."""
    _enable_bearer_middleware(settings)
    _ensure_drf_schema_class(settings)
    djcrud.site.build()
    if request.node.get_closest_marker("drf") is not None:
        _configure_drf(settings)
    elif request.node.get_closest_marker("urls") is None:
        settings.ROOT_URLCONF = "tests.urls"


@pytest.fixture
def routing_bulk_items(db):
    from djcrud_example.routing_example.models import Item

    return [Item.objects.create(name=f"item-{i}") for i in range(4)]


@pytest.fixture
def many_users(db):
    """Enough users to paginate and filter in browser tests."""
    return [
        User.objects.create_user(
            username=f"user{i}",
            email=f"user{i}@example.com",
            password="testpass123",
        )
        for i in range(50)
    ]


@pytest.fixture
def browser_login(browser, live_server):
    def login(username="admin", password="password"):
        browser.visit(f"{live_server.url}/auth/login/")
        browser.fill("username", username)
        browser.fill("password", password)
        browser.find_by_css('button[type="submit"]').first.click()
        assert browser.is_text_present("Log out", wait_time=5), "Login failed"

    return login