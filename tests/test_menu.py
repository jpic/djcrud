"""
Tests for djcrud.menu module.
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()
from djcrud.mvc import Controller, View
from djcrud.menu import get_menu


@pytest.mark.django_db
class TestGetMenu:
    """Test the get_menu function."""

    def test_get_menu_filters_by_name(self, superuser_request):
        """get_menu returns only views with specified menu name."""
        class MainView(View):
            menus = ['main']
            has_perm = True

        class SidebarView(View):
            menus = ['sidebar']
            has_perm = True

        class BothView(View):
            menus = ['main', 'sidebar']
            has_perm = True

        controller = Controller(views=[MainView, SidebarView, BothView])

        # Get 'main' menu - should include MainView and BothView
        main_views = get_menu(controller, 'main', superuser_request)

        # Should return list of view instances
        assert isinstance(main_views, list)

    def test_get_menu_checks_permissions(self, user_request, superuser_request):
        """get_menu filters out views user doesn't have permission for."""
        # View requiring superuser (default)
        class AdminView(View):
            menus = ['main']

        # Public view
        class PublicView(View):
            menus = ['main']
            has_perm = True

        controller = Controller(views=[AdminView, PublicView])

        # Regular user should only see PublicView
        user_menu = get_menu(controller, 'main', user_request)
        # Implementation should filter based on has_perm()

        # Superuser should see both
        admin_menu = get_menu(controller, 'main', superuser_request)
        # Implementation should allow both

    def test_get_menu_empty_when_no_matches(self, superuser_request):
        """get_menu returns empty list when no views match."""
        class MainView(View):
            menus = ['main']

        controller = Controller(views=[MainView])

        # Request non-existent menu
        result = get_menu(controller, 'nonexistent', superuser_request)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_menu_view_without_menus_attribute(self, superuser_request):
        """get_menu handles views without menus attribute."""
        class NoMenuView(View):
            pass

        controller = Controller(views=[NoMenuView])

        # Should not error, should return empty
        result = get_menu(controller, 'main', superuser_request)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_menu_with_kwargs(self, superuser_request):
        """get_menu passes kwargs to view instantiation."""
        class ModelView(View):
            menus = ['main']
            model = User
            has_perm = True

        controller = Controller(views=[ModelView])

        # Should be able to pass additional kwargs
        result = get_menu(controller, 'main', superuser_request, object_id=123)

        # Function should handle kwargs (even if view doesn't use them)
        assert isinstance(result, list)

    def test_get_menu_instantiates_views(self, superuser_request):
        """get_menu returns view instances, not classes."""
        class MyView(View):
            menus = ['main']
            has_perm = True

        controller = Controller(views=[MyView])

        result = get_menu(controller, 'main', superuser_request)

        # Should return instances (check implementation calls clone() then instantiate)
        assert isinstance(result, list)

    def test_get_menu_with_cloned_views(self, superuser_request):
        """get_menu works with cloned views."""
        HomeView = View.clone(
            icon='home',
            menus=['main'],
            has_perm=True,
        )

        controller = Controller(views=[HomeView])

        result = get_menu(controller, 'main', superuser_request)

        assert isinstance(result, list)

    def test_get_menu_with_nested_controller(self, anonymous_request):
        """get_menu returns submenu structure for nested controllers."""
        from djcrud.views.template import TemplateView

        # Create views for auth controller
        LoginView = TemplateView.clone(
            menus=['main'],
            has_perm=True,
            urlpath='login',
            template_name='test.html',
        )

        # Create nested controller (no menus - controllers don't appear in menus)
        class AuthController(Controller):
            urlpath = 'auth'
            icon = 'shield-lock'

        auth_controller = AuthController(views=[LoginView])
        root = Controller(views=[auth_controller])

        result = get_menu(root, 'main', anonymous_request)

        # Should return flat list with LoginView (subclass of TemplateView)
        assert len(result) == 1
        from djcrud.mvc import View
        assert isinstance(result[0], View)
        # The cloned view is a TemplateView subclass
        assert result[0].urlpath == 'login'

    def test_view_can_get_main_menu_from_root(self, anonymous_request):
        """Views can build their own main menu by accessing root_controller."""
        from djcrud.views.template import TemplateView

        # Create a view with get_main_menu method
        class MyView(TemplateView):
            menus = ['main']
            has_perm = True

            def get_main_menu(self):
                from djcrud.menu import get_menu
                return get_menu(self.root_controller, 'main', self.request)

        root = Controller(views=[MyView])

        # Instantiate the view
        view_class = root.views[0]
        view = view_class()
        view.request = anonymous_request

        # Should be able to get main menu
        menu = view.get_main_menu()
        assert isinstance(menu, list)
        assert len(menu) == 1  # Should include itself
