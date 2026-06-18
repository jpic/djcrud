"""
Tests for djcrud.mvc module - Controller and View classes.
"""

import pytest
from django.contrib.auth.models import User, Group
from django.urls import path, reverse, resolve
from djcrud.mvc import Controller, View


@pytest.mark.django_db
class TestController:
    """Test the Controller class."""

    def test_controller_init_with_views(self):
        """Controller initializes with a views list and clones them."""
        class TestView(View):
            urlpath = 'test'

        controller = Controller(views=[TestView])

        # Views are cloned, so they won't be the exact same class
        assert len(controller.views) == 1
        assert issubclass(controller.views[0], View)
        # But they should have the controller reference set
        assert controller.views[0].controller == controller

    def test_controller_urlpatterns_property_exists(self):
        """Controller has urlpatterns property."""
        controller = Controller(views=[])

        # Should have the property/method
        assert hasattr(controller, 'urlpatterns')

    def test_controller_urlpatterns_empty_views(self):
        """Controller with empty views returns empty urlpatterns."""
        controller = Controller(views=[])

        # Should return a list (even if empty or buggy implementation)
        result = controller.urlpatterns
        assert isinstance(result, list)

    def test_controller_can_be_cloned(self):
        """Controller inherits from Clonable."""
        controller = Controller(views=[])

        ClonedController = Controller.clone(urlpath='custom')

        assert ClonedController is not Controller
        assert issubclass(ClonedController, Controller)
        assert ClonedController.urlpath == 'custom'

    def test_controller_urlpatterns_can_be_used_in_path(self):
        """Controller.urlpatterns can be concatenated with Django urlpatterns."""
        from djcrud.views.template import TemplateView

        class TestController(Controller):
            urlpath = 'test'
            views = [
                TemplateView.clone(urlpath='page', urlname='page', template_name='test.html'),
            ]

        # This should work - controller returns patterns ready to use
        urlpatterns = [] + TestController.urlpatterns
        assert len(urlpatterns) == 1

    def test_site_controller_returns_flat_patterns(self):
        """Root controller (empty urlpath) returns child patterns directly."""
        from djcrud.views.template import TemplateView

        site = Controller(
            views=[
                TemplateView.clone(urlpath='home', urlname='home', template_name='test.html'),
                TemplateView.clone(urlpath='about', urlname='about', template_name='test.html'),
            ]
        )

        # Root controller (urlpath='') should return children directly
        patterns = site.urlpatterns
        # Should have 2 patterns (one for each view)
        assert len(patterns) == 2

    def test_controller_sets_parent_reference_on_views(self):
        """Controller sets itself as parent on child views."""
        class TestView(View):
            urlpath = 'test'

        controller = Controller(views=[TestView])
        cloned_view = controller.views[0]

        assert cloned_view.controller == controller

    def test_view_can_access_root_controller(self):
        """Views can access the root controller through their controller."""
        class TestView(View):
            urlpath = 'test'

        # Create nested controller structure
        sub_controller = Controller(views=[TestView])
        root = Controller(views=[sub_controller])

        # The sub_controller should have parent_controller set
        assert sub_controller.parent_controller == root

        # The view should be able to access root controller
        cloned_view = sub_controller.views[0]
        assert cloned_view.root_controller == root


@pytest.mark.django_db
class TestView:
    """Test the View class."""

    def test_view_inherits_from_django_view(self):
        """View inherits from django.views.generic.View."""
        from django.views.generic import View as DjangoView

        assert issubclass(View, DjangoView)

    def test_view_has_urlpath_property(self):
        """View has urlpath property with default implementation."""
        class MyCustomView(View):
            pass

        # Should return class name by default (based on mvc.py implementation)
        assert MyCustomView.urlpath == 'MyCustomView'

    def test_view_has_urlname_property(self):
        """View has urlname property with default implementation."""
        class MyCustomView(View):
            pass

        # Should return class name by default (based on mvc.py implementation)
        assert MyCustomView.urlname == 'MyCustomView'

    def test_view_urlpath_can_be_overridden(self):
        """View urlpath can be overridden as class attribute."""
        class MyView(View):
            urlpath = 'custom-path'

        assert MyView.urlpath == 'custom-path'

    def test_view_urlname_can_be_overridden(self):
        """View urlname can be overridden as class attribute."""
        class MyView(View):
            urlname = 'custom_name'

        assert MyView.urlname == 'custom_name'

    def test_view_has_urlpatterns_property(self):
        """View has urlpatterns property."""
        class MyView(View):
            urlpath = 'test'
            urlname = 'test_view'

        # Should return a list of URL patterns
        patterns = MyView.urlpatterns
        assert isinstance(patterns, list)

    def test_view_can_be_cloned(self):
        """View can be cloned with custom attributes."""
        class BaseView(View):
            template_name = 'base.html'

        ClonedView = BaseView.clone(
            template_name='custom.html',
            urlpath='custom',
            icon='home'
        )

        assert ClonedView.template_name == 'custom.html'
        assert ClonedView.urlpath == 'custom'
        assert ClonedView.icon == 'home'

    def test_view_clone_with_model(self):
        """View can be cloned with a model."""
        class ListView(View):
            pass

        UserListView = ListView.clone(model=User)

        assert UserListView.model is User
        assert UserListView.__name__ == 'UserListView'

    def test_view_has_perm_property(self):
        """View has has_perm property for permission checking."""
        class MyView(View):
            pass

        # Should have has_perm
        assert hasattr(MyView, 'has_perm')

    def test_view_has_perm_default_secure(self, anonymous_request):
        """View.has_perm is secure by default (requires superuser)."""
        class MyView(View):
            pass

        # Create instance with anonymous request
        view = MyView()
        view.request = anonymous_request

        # Should deny access by default
        result = view.has_perm
        assert result is False

    def test_view_has_perm_with_regular_user(self, user_request):
        """View.has_perm denies regular authenticated users."""
        class MyView(View):
            pass

        view = MyView()
        view.request = user_request

        # Should deny regular user (not superuser)
        result = view.has_perm
        assert result is False

    def test_view_has_perm_with_superuser(self, superuser_request):
        """View.has_perm allows superusers."""
        class MyView(View):
            pass

        view = MyView()
        view.request = superuser_request

        # Should allow superuser
        result = view.has_perm
        assert result is True

    def test_view_has_perm_can_be_overridden(self, anonymous_request):
        """View.has_perm can be overridden to allow public access."""
        class PublicView(View):
            has_perm = True

        view = PublicView()
        view.request = anonymous_request

        # Should allow access even for anonymous
        assert view.has_perm is True

    def test_view_has_perm_can_be_overridden_via_clone(self, anonymous_request):
        """View.has_perm can be overridden via clone()."""
        class MyView(View):
            pass

        PublicView = MyView.clone(has_perm=True)

        view = PublicView()
        view.request = anonymous_request

        assert view.has_perm is True

    def test_view_as_view_works(self):
        """View.as_view() works like Django's CBV."""
        class MyView(View):
            def get(self, request):
                from django.http import HttpResponse
                return HttpResponse('test')

        view_func = MyView.as_view()
        assert callable(view_func)

    def test_view_urlpatterns_can_be_used_in_path(self):
        """View.urlpatterns can be concatenated with Django urlpatterns."""
        class TestView(View):
            urlpath = 'test'
            urlname = 'test'

        # This should work without errors
        urlpatterns = [] + TestView.urlpatterns
        assert len(urlpatterns) == 1

    def test_view_urlpatterns_have_trailing_slash(self):
        """View urlpatterns add trailing slash to non-empty urlpath."""
        class TestView(View):
            urlpath = 'test'
            urlname = 'test'

        patterns = TestView.urlpatterns
        assert len(patterns) == 1
        assert str(patterns[0].pattern) == 'test/'

    def test_view_empty_urlpath_no_trailing_slash(self):
        """Empty urlpath should not add trailing slash."""
        class HomeView(View):
            urlpath = ''
            urlname = 'home'

        patterns = HomeView.urlpatterns
        assert len(patterns) == 1
        assert str(patterns[0].pattern) == ''
