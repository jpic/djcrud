"""
Integration tests for djcrud based on the example project structure.

These tests validate the full controller hierarchy and URL routing
as demonstrated in djcrud_example and djcrud_auth.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()
from django.urls import path, reverse, resolve
from djcrud.mvc import Controller, View


@pytest.mark.django_db
class TestControllerHierarchy:
    """Test nested controller structure like in djcrud_auth."""

    def test_simple_controller_with_single_view(self):
        """Controller with a single view generates urlpatterns."""
        class HomeView(View):
            urlpath = ''
            urlname = 'home'

        site = Controller(views=[HomeView])

        # Should have urlpatterns
        assert hasattr(site, 'urlpatterns')
        patterns = site.urlpatterns
        assert isinstance(patterns, list)

    def test_controller_with_multiple_views(self):
        """Controller with multiple views at different paths."""
        class ListView(View):
            urlpath = ''
            urlname = 'list'

        class CreateView(View):
            urlpath = 'create'
            urlname = 'create'

        controller = Controller(views=[ListView, CreateView])

        patterns = controller.urlpatterns
        assert isinstance(patterns, list)

    def test_nested_controller_structure(self):
        """Nested controllers like AuthController > UserController."""
        # Simulate UserController
        class UserListView(View):
            urlpath = ''
            urlname = 'user_list'
            model = User

        class UserCreateView(View):
            urlpath = 'create'
            urlname = 'user_create'
            model = User

        UserController = Controller.clone(
            urlpath='user',
            model=User,
            views=[UserListView, UserCreateView]
        )

        # Simulate AuthController
        AuthController = Controller.clone(
            urlpath='auth',
            views=[UserController]
        )

        # Site controller
        site = Controller(views=[AuthController])

        # Should generate nested URL structure
        patterns = site.urlpatterns
        assert isinstance(patterns, list)

    def test_cloned_view_in_controller(self):
        """Controller can contain cloned views (like TemplateView.clone())."""
        class TemplateView(View):
            template_name = 'base.html'

        HomeView = TemplateView.clone(
            icon='home',
            template_name='home.html',
            urlname='home',
            urlpath='',
            has_perm=True
        )

        site = Controller(views=[HomeView])

        # Should work with cloned view
        assert hasattr(site, 'urlpatterns')
        assert HomeView.icon == 'home'
        assert HomeView.template_name == 'home.html'
        assert HomeView.has_perm is True


@pytest.mark.django_db
class TestViewWithModel:
    """Test views that are bound to Django models."""

    def test_view_with_user_model(self):
        """View can be associated with User model."""
        class UserListView(View):
            model = User
            urlpath = ''

        assert UserListView.model is User

    def test_view_clone_with_model_naming(self):
        """Cloning a view with model prefixes class name."""
        class ListView(View):
            pass

        UserListView = ListView.clone(model=User)
        GroupListView = ListView.clone(model=Group)

        assert UserListView.__name__ == 'UserListView'
        assert GroupListView.__name__ == 'GroupListView'
        assert UserListView.model is User
        assert GroupListView.model is Group


@pytest.mark.django_db
class TestPermissionSystem:
    """Test the permission system across controllers and views."""

    def test_view_default_requires_superuser(self, user_request):
        """By default, views require superuser (secure by default)."""
        class ProtectedView(View):
            pass

        view = ProtectedView()
        view.request = user_request

        # Regular user denied
        assert view.has_perm is False

    def test_view_allows_superuser(self, superuser_request):
        """Superusers can access views by default."""
        class ProtectedView(View):
            pass

        view = ProtectedView()
        view.request = superuser_request

        # Superuser allowed
        assert view.has_perm is True

    def test_public_view_allows_anonymous(self, anonymous_request):
        """Views can be made public with has_perm=True."""
        PublicView = View.clone(
            urlpath='public',
            has_perm=True
        )

        view = PublicView()
        view.request = anonymous_request

        # Anonymous allowed
        assert view.has_perm is True

    def test_mixed_permission_views_in_controller(self, anonymous_request, superuser_request):
        """Controller can contain views with different permission levels."""
        PublicView = View.clone(urlpath='public', has_perm=True)
        ProtectedView = View.clone(urlpath='admin')

        controller = Controller(views=[PublicView, ProtectedView])

        # Public view allows anonymous
        public = PublicView()
        public.request = anonymous_request
        assert public.has_perm is True

        # Protected view denies anonymous
        protected = ProtectedView()
        protected.request = anonymous_request
        assert protected.has_perm is False

        # Protected view allows superuser
        protected.request = superuser_request
        assert protected.has_perm is True


@pytest.mark.django_db
class TestMenuSystem:
    """Test menu registration and filtering."""

    def test_view_with_menus_attribute(self):
        """Views can declare which menus they belong to."""
        class MainView(View):
            menus = ['main', 'sidebar']

        assert MainView.menus == ['main', 'sidebar']

    def test_view_clone_with_menus(self):
        """Views can be cloned with menus."""
        HomeView = View.clone(
            urlpath='',
            menus=['main', 'footer']
        )

        assert HomeView.menus == ['main', 'footer']

    def test_get_menu_function_exists(self):
        """djcrud.menu.get_menu function exists."""
        from djcrud import menu

        assert hasattr(menu, 'get_menu')
        assert callable(menu.get_menu)


@pytest.mark.django_db
class TestRealWorldExample:
    """Test the actual structure from djcrud_example."""

    def test_site_controller_structure(self):
        """Replicate the site structure from djcrud_example/urls.py."""
        # Simulate TemplateView
        class TemplateView(View):
            template_name = 'base.html'

        # Simulate UserListView and UserCreateView
        class UserListView(View):
            model = User
            urlpath = ''
            menus = ['main', 'model']

        class UserCreateView(View):
            model = User
            urlpath = 'create'

        # Build UserController
        UserController = Controller.clone(
            urlpath='user',
            model=User,
            views=[UserListView, UserCreateView]
        )

        # Build AuthController
        AuthController = Controller.clone(
            urlpath='auth',
            views=[UserController]
        )

        # Build site
        site = Controller(
            views=[
                TemplateView.clone(
                    icon='home',
                    template_name='home.html',
                    menus=['main'],
                    urlname='home',
                    urlpath='',
                    has_perm=True,
                ),
                AuthController,
            ]
        )

        # Validate structure
        assert len(site.views) == 2
        assert site.views[0].icon == 'home'
        assert site.views[0].has_perm is True
        assert hasattr(site, 'urlpatterns')
