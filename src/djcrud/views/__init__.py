"""
djcrud view classes (frontend-agnostic).

These views provide context for templates but don't specify which templates to use.
Frontend apps (like djcrud_bootstrap) provide the actual templates.
"""

from django.views import generic
from djcrud.mvc import View
from djcrud import attribute


class ListView(View, generic.ListView):
    """
    List view for displaying model instances.

    Template: djcrud/list.html (provided by frontend app)

    Context variables:
        - object_list: QuerySet of model instances
        - table: django-tables2 table instance (if Tables2Mixin used)
        - title: Page title from get_title()
        - icon: Icon name from icon attribute
        - model_menu: List of actions (views with 'model' in menus)
        - main_menu: Sidebar menu items (views with 'main' in menus)
    """
    template_name = 'djcrud/list.html'
    paginate_by = 25

    @attribute.getter
    def model(self):
        """Get model from controller if not set directly on view."""
        # Check if model is set on the class
        if hasattr(self.__class__, '_model') and self.__class__._model is not None:
            return self.__class__._model
        # Try to get from controller
        controller = self._controller or self.controller
        if controller and hasattr(controller, 'model'):
            return controller.model
        return None

    @attribute.getter
    def title(self):
        """Return page title."""
        if self.model:
            return self.model._meta.verbose_name_plural.capitalize()
        return 'List'

    def get_context_data(self, **kwargs):
        """Add view to context - templates access everything via view."""
        context = super().get_context_data(**kwargs)
        context['view'] = self
        return context

    @attribute.cached
    def icon(self):
        """Icon for this view."""
        return 'list'

    @attribute.cached
    def model_menu(self):
        """Get actions for this model (views with 'model' in menus)."""
        from djcrud.menu import get_menu
        if not self._controller:
            return []
        return get_menu(self._controller, 'model', self.request)

    @attribute.cached
    def main_menu(self):
        """Get main navigation menu."""
        from djcrud.menu import get_menu
        if not self.root_controller:
            return []
        return get_menu(self.root_controller, 'main', self.request)


class DetailView(View, generic.DetailView):
    """
    Detail view for displaying a single model instance.

    Template: djcrud/detail.html (provided by frontend app)

    Context variables:
        - object: The model instance
        - title: Page title from get_title()
        - icon: Icon name from icon attribute
        - object_menu: List of actions (views with 'object' in menus)
        - main_menu: Sidebar menu items (views with 'main' in menus)
    """
    template_name = 'djcrud/detail.html'

    @attribute.getter
    def model(self):
        """Get model from controller if not set directly on view."""
        # Check if model is set on the class
        if hasattr(self.__class__, '_model') and self.__class__._model is not None:
            return self.__class__._model
        # Try to get from controller
        controller = self._controller or self.controller
        if controller and hasattr(controller, 'model'):
            return controller.model
        return None

    @attribute.getter
    def title(self):
        """Return page title."""
        return str(self.object)

    def get_context_data(self, **kwargs):
        """Add view to context - templates access everything via view."""
        context = super().get_context_data(**kwargs)
        context['view'] = self
        return context

    @attribute.cached
    def icon(self):
        """Icon for this view."""
        return 'eye'

    @attribute.cached
    def object_menu(self):
        """Get actions for this object (views with 'object' in menus)."""
        from djcrud.menu import get_menu
        if not self._controller:
            return []
        return get_menu(self._controller, 'object', self.request, object=self.object)

    @attribute.cached
    def main_menu(self):
        """Get main navigation menu."""
        from djcrud.menu import get_menu
        if not self.root_controller:
            return []
        return get_menu(self.root_controller, 'main', self.request)


class CreateView(View, generic.CreateView):
    """
    Create view for creating new model instances.

    Template: djcrud/modelform.html (extends form.html with model menu)
    """
    template_name = 'djcrud/modelform.html'

    @attribute.getter
    def model(self):
        """Get model from controller if not set directly on view."""
        # Check if model is set on the class
        if hasattr(self.__class__, '_model') and self.__class__._model is not None:
            return self.__class__._model
        # Try to get from controller
        controller = self._controller or self.controller
        if controller and hasattr(controller, 'model'):
            return controller.model
        return None

    @attribute.getter
    def title(self):
        """Return page title."""
        if self.model:
            return f"Create {self.model._meta.verbose_name.capitalize()}"
        return "Create"

    def get_context_data(self, **kwargs):
        """Add view to context - templates access everything via view."""
        context = super().get_context_data(**kwargs)
        context['view'] = self
        return context

    @attribute.cached
    def icon(self):
        """Icon for this view."""
        return 'plus-circle'

    @attribute.cached
    def cancel_url(self):
        """Return URL to go back to."""
        # TODO: Implement proper back URL
        return '/'

    @attribute.cached
    def main_menu(self):
        """Get main navigation menu."""
        from djcrud.menu import get_menu
        if not self.root_controller:
            return []
        return get_menu(self.root_controller, 'main', self.request)

    @attribute.cached
    def model_menu(self):
        """Get actions for this model (views with 'model' in menus)."""
        from djcrud.menu import get_menu
        if not self._controller:
            return []
        return get_menu(self._controller, 'model', self.request)


class UpdateView(View, generic.UpdateView):
    """
    Update view for editing model instances.

    Template: djcrud/modelform.html (extends form.html with object menu)
    """
    template_name = 'djcrud/modelform.html'

    @attribute.getter
    def model(self):
        """Get model from controller if not set directly on view."""
        # Check if model is set on the class
        if hasattr(self.__class__, '_model') and self.__class__._model is not None:
            return self.__class__._model
        # Try to get from controller
        controller = self._controller or self.controller
        if controller and hasattr(controller, 'model'):
            return controller.model
        return None

    def get_title(self):
        """Return page title."""
        if hasattr(self, 'title'):
            return self.title() if callable(self.title) else self.title
        if self.model:
            return f"Edit {self.model._meta.verbose_name.capitalize()}"
        return "Edit"

    def get_context_data(self, **kwargs):
        """Add view to context - templates access everything via view."""
        context = super().get_context_data(**kwargs)
        context['view'] = self
        return context

    @attribute.cached
    def icon(self):
        """Icon for this view."""
        return 'pencil'

    @attribute.cached
    def cancel_url(self):
        """Return URL to go back to."""
        # TODO: Implement proper back URL
        return '/'

    @attribute.cached
    def main_menu(self):
        """Get main navigation menu."""
        from djcrud.menu import get_menu
        if not self.root_controller:
            return []
        return get_menu(self.root_controller, 'main', self.request)

    @attribute.cached
    def object_menu(self):
        """Get actions for this object (views with 'object' in menus)."""
        # TODO: This needs the controller context
        return []
