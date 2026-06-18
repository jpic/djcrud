"""
Tests for Controller.views list behavior.

The views list should automatically clone views when they're appended,
so that parent references are always set correctly.
"""

import pytest
from djcrud.mvc import Controller, View


@pytest.mark.django_db
class TestControllerViewsList:
    """Test that Controller.views behaves correctly when modified."""

    def test_views_list_clones_on_append(self):
        """Appending a view to controller.views should clone it and set parent."""
        class TestView(View):
            urlpath = 'test'

        controller = Controller(views=[])

        # Append a view
        controller.views.append(TestView)

        # Should have cloned the view
        assert len(controller.views) == 1
        cloned_view = controller.views[0]

        # Should be a subclass, not the exact same class
        assert issubclass(cloned_view, View)

        # Should have controller reference set
        assert cloned_view.controller == controller

    def test_views_list_clones_on_insert(self):
        """Inserting a view should clone it and set parent."""
        class TestView1(View):
            urlpath = 'test1'

        class TestView2(View):
            urlpath = 'test2'

        controller = Controller(views=[TestView1])

        # Insert at position 0
        controller.views.insert(0, TestView2)

        assert len(controller.views) == 2
        assert controller.views[0].controller == controller
        assert controller.views[1].controller == controller

    def test_views_list_clones_on_extend(self):
        """Extending views list should clone all new views."""
        class TestView1(View):
            urlpath = 'test1'

        class TestView2(View):
            urlpath = 'test2'

        class TestView3(View):
            urlpath = 'test3'

        controller = Controller(views=[TestView1])

        # Extend with multiple views
        controller.views.extend([TestView2, TestView3])

        assert len(controller.views) == 3
        assert all(v.controller == controller for v in controller.views)

    def test_views_list_supports_assignment(self):
        """Assigning to a position should clone the view."""
        class TestView1(View):
            urlpath = 'test1'

        class TestView2(View):
            urlpath = 'test2'

        controller = Controller(views=[TestView1])

        # Assign to position 0
        controller.views[0] = TestView2

        assert len(controller.views) == 1
        assert controller.views[0].controller == controller
        assert controller.views[0].urlpath == 'test2'

    def test_views_list_supports_plus_operator(self):
        """Using + operator should return a new list with cloned views."""
        class TestView1(View):
            urlpath = 'test1'

        class TestView2(View):
            urlpath = 'test2'

        controller = Controller(views=[TestView1])

        # Add another view using +
        new_list = controller.views + [TestView2]

        assert len(new_list) == 2
        # Original list unchanged
        assert len(controller.views) == 1

    def test_views_list_clones_controller_instances(self):
        """Appending a controller instance should set parent_controller."""
        sub_controller = Controller(views=[])
        controller = Controller(views=[])

        # Append controller instance
        controller.views.append(sub_controller)

        # Should set parent reference
        assert sub_controller.parent_controller == controller

    def test_root_controller_property(self):
        """Test root_controller property traverses to root."""
        class TestView(View):
            urlpath = 'test'

        sub_controller = Controller(views=[TestView])
        root = Controller(views=[sub_controller])

        # View should be able to get root
        view = sub_controller.views[0]
        assert view.root_controller == root

        # Sub controller should get root
        assert sub_controller.root_controller == root

        # Root should return itself
        assert root.root_controller == root
