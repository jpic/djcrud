"""Debug test to check permission issues in E2E tests."""
import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

User = get_user_model()


@pytest.fixture
def admin_user(db):
    """Create an admin user for testing."""
    user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )
    print(f"Created user: {user.username}, is_superuser={user.is_superuser}, is_staff={user.is_staff}")
    return user


def test_user_is_superuser(admin_user):
    """Verify the admin user is actually a superuser."""
    assert admin_user.is_superuser
    assert admin_user.is_staff
    print(f"✓ User {admin_user.username} is superuser: {admin_user.is_superuser}")


def test_create_view_has_perm(admin_user, db):
    """Test that CreateView.has_perm returns True for superuser."""
    from djcrud_auth.crud import UserController
    from django.test import RequestFactory

    factory = RequestFactory()
    request = factory.get('/auth/user/create/')
    request.user = admin_user

    # Get the CreateView from UserController
    create_view = None
    for v in UserController.views:
        if hasattr(v, 'urlname') and v.urlname == 'create':
            create_view = v
            break

    assert create_view is not None, "CreateView not found in UserController"

    # Instantiate the view with request
    view_instance = create_view.clone(request=request)()
    view_instance.request = request
    view_instance._controller = UserController

    # Check has_perm
    has_perm = view_instance.has_perm() if callable(view_instance.has_perm) else view_instance.has_perm
    print(f"CreateView.has_perm() = {has_perm}")
    print(f"request.user = {request.user}")
    print(f"request.user.is_superuser = {request.user.is_superuser}")

    assert has_perm, "CreateView.has_perm should be True for superuser"


def test_get_tagged_views_returns_create(admin_user, db):
    """Test that get_tagged_views('model') returns CreateView for superuser."""
    from djcrud_example.urls import site
    from django.test import RequestFactory

    factory = RequestFactory()
    request = factory.get('/auth/user/')
    request.user = admin_user

    # Get UserController from the site hierarchy (not in isolation)
    auth_controller = None
    for v in site.views:
        if hasattr(v, 'urlpath') and v.urlpath == 'auth':
            auth_controller = v
            break

    assert auth_controller is not None, "AuthController should be in site.views"

    user_controller = None
    for v in auth_controller.views:
        if hasattr(v, 'urlpath') and v.urlpath == 'user':
            user_controller = v
            break

    assert user_controller is not None, "UserController should be in AuthController.views"

    # Get model-tagged views
    model_views = user_controller.get_tagged_views('model', request)

    print(f"Model-tagged views found: {len(model_views)}")
    for v in model_views:
        print(f"  - {v.__class__.__name__}: url={v.url}")

    assert len(model_views) > 0, "Should find at least CreateView with 'model' tag"

    # Check if CreateView is in the list
    has_create = any('Create' in v.__class__.__name__ for v in model_views)
    assert has_create, "CreateView should be in model-tagged views"
