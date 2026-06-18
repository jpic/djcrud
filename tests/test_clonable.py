"""
Tests for the Clonable mixin that enables .clone() pattern.
"""

import pytest
from django.contrib.auth.models import User, Group
from djcrud.mvc import Clonable, View


class TestClonable:
    """Test the Clonable mixin and clone() method."""

    def test_clone_creates_subclass(self):
        """clone() returns a new subclass, not the original class."""
        class MyView(Clonable):
            original = True

        ClonedView = MyView.clone()

        assert ClonedView is not MyView
        assert issubclass(ClonedView, MyView)
        assert ClonedView.original is True  # Inherits from parent

    def test_clone_with_attributes(self):
        """clone() can override attributes via kwargs."""
        class MyView(Clonable):
            template_name = 'default.html'
            urlpath = 'default'

        ClonedView = MyView.clone(
            template_name='custom.html',
            urlpath='custom',
            new_attr='new_value'
        )

        assert ClonedView.template_name == 'custom.html'
        assert ClonedView.urlpath == 'custom'
        assert ClonedView.new_attr == 'new_value'

        # Original unchanged
        assert MyView.template_name == 'default.html'
        assert MyView.urlpath == 'default'

    def test_clone_with_mixins(self):
        """clone() can add mixins as positional arguments."""
        class MixinA:
            mixin_a = True

        class MixinB:
            mixin_b = True

        class MyView(Clonable):
            base = True

        ClonedView = MyView.clone(MixinA, MixinB)

        assert issubclass(ClonedView, MyView)
        assert issubclass(ClonedView, MixinA)
        assert issubclass(ClonedView, MixinB)
        assert ClonedView.base is True
        assert ClonedView.mixin_a is True
        assert ClonedView.mixin_b is True

    def test_clone_naming_without_model(self):
        """clone() preserves class name when no model is provided."""
        class UserListView(Clonable):
            pass

        ClonedView = UserListView.clone(urlpath='custom')

        assert ClonedView.__name__ == 'UserListView'

    def test_clone_naming_with_model_not_in_name(self):
        """clone() prefixes model name when model provided and not in class name."""
        class ListView(Clonable):
            pass

        ClonedView = ListView.clone(model=User)

        assert ClonedView.__name__ == 'UserListView'
        assert ClonedView.model is User

    def test_clone_naming_with_model_already_in_name(self):
        """clone() doesn't duplicate model name if already present."""
        class UserListView(Clonable):
            pass

        ClonedView = UserListView.clone(model=User)

        # Should not become UserUserListView
        assert ClonedView.__name__ == 'UserListView'
        assert ClonedView.model is User

    def test_clone_model_from_parent_class(self):
        """clone() uses model from parent if not in kwargs."""
        class UserListView(Clonable):
            model = User

        # Clone with different model
        ClonedView = UserListView.clone(model=Group)
        assert ClonedView.__name__ == 'GroupUserListView'
        assert ClonedView.model is Group

    def test_clone_preserves_methods(self):
        """Cloned class inherits methods from parent."""
        class MyView(Clonable):
            def get_context(self):
                return {'key': 'value'}

        ClonedView = MyView.clone(extra='data')

        instance = ClonedView()
        assert instance.get_context() == {'key': 'value'}
        assert ClonedView.extra == 'data'

    def test_clone_callable_attributes(self):
        """clone() can accept callable attributes (lambdas, functions)."""
        class MyView(Clonable):
            pass

        def custom_method(self):
            return "custom"

        ClonedView = MyView.clone(
            get_data=lambda self: "lambda_data",
            custom=custom_method
        )

        instance = ClonedView()
        assert instance.get_data() == "lambda_data"
        assert instance.custom() == "custom"

    def test_clone_multiple_times(self):
        """Can clone multiple times creating different classes."""
        class BaseView(Clonable):
            base_attr = 'base'

        Clone1 = BaseView.clone(variant='one')
        Clone2 = BaseView.clone(variant='two')

        assert Clone1 is not Clone2
        assert Clone1.variant == 'one'
        assert Clone2.variant == 'two'
        assert Clone1.base_attr == 'base'
        assert Clone2.base_attr == 'base'

    def test_clone_chaining(self):
        """Can clone a cloned class."""
        class BaseView(Clonable):
            level = 0

        Clone1 = BaseView.clone(level=1)
        Clone2 = Clone1.clone(level=2)

        assert Clone2.level == 2
        assert issubclass(Clone2, Clone1)
        assert issubclass(Clone2, BaseView)
