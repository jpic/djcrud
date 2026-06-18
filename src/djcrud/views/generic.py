"""
Generic CRUD views for djcrud (frontend-agnostic).

These inherit from djcrud.mvc.View + the corresponding django.views.generic
class. They add:
- model / model_meta getters (from controller or _model)
- title, icon, menu getters via @attribute
- get_context_data to put 'view' in template context
- get_form_class override to safely support both fields='__all__' (default for
  generic ModelForm) and custom form_class= (e.g. UserCreationForm in djcrud_auth)

Usage (in yourapp/crud.py):
    from djcrud.views.generic import ListView, CreateView
    from djcrud.views.tables2 import Tables2Mixin

    class ProductListView(Tables2Mixin, ListView):
        menus = ['main']

    ProductController = crud.ModelController.clone(model=Product)
"""

from django.views import generic
from djcrud.mvc import View
from djcrud import attribute
from djcrud.views.unpoly import UnpolyModalMixin
# Tables2Mixin (and model_meta convenience) available via from djcrud.views.tables2
# or imported explicitly. Templates use {{ view.model_meta }} to avoid _meta.


class ListView(View, generic.ListView):
    """
    List view for displaying model instances.

    Template: djcrud/list.html (provided by frontend app)

    Context variables:
        - object_list: QuerySet of model instances
        - table: django-tables2 table instance (if Tables2Mixin used)
        - title: Page title (from title getter)
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
    def model_meta(self):
        """Convenience getter for model._meta (Django templates disallow
        leading-underscore attributes like _meta).
        """
        return self.model._meta

    @attribute.getter
    def title(self):
        """Return page title."""
        model = self.model
        if model:
            return model._meta.verbose_name_plural.capitalize()
        return 'List'

    def get_context_data(self, **kwargs):
        """Add view to context - templates access everything via view.

        We override get_form_class to avoid the 'fields' + 'form_class' conflict
        when a custom form_class (e.g. UserCreationForm) is provided via .clone().
        """
        context = super().get_context_data(**kwargs)
        context['view'] = self
        return context

    def get_form_class(self):
        """Return the form class, clearing fields if a custom form_class is set.

        This is the clean way to support both generic ModelForm (with fields='__all__')
        and specialized forms like UserCreationForm in djcrud_auth.
        """
        if hasattr(self, 'form_class') and self.form_class is not None:
            # Clear fields to avoid ImproperlyConfigured when both are present
            if hasattr(self, 'fields'):
                self.fields = None
            return self.form_class
        return super().get_form_class()

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
        return get_menu(self._controller, 'model', self.request, exclude_current=self)

    @attribute.cached
    def main_menu(self):
        """Get main navigation menu."""
        from djcrud.menu import get_menu
        if not self.root_controller:
            return []
        return get_menu(self.root_controller, 'main', self.request, exclude_current=self)


class DetailView(View, generic.DetailView):
    """
    Detail view for displaying a single model instance.

    Template: djcrud/detail.html (provided by frontend app)

    Context variables:
        - object: The model instance
        - title: Page title (from title getter)
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
    def model_meta(self):
        """Convenience getter for model._meta (Django templates disallow
        leading-underscore attributes like _meta).
        """
        return self.model._meta

    @attribute.getter
    def title(self):
        """Return page title."""
        return str(self.object)

    def get_context_data(self, **kwargs):
        """Add view to context - templates access everything via view.

        We override get_form_class to avoid the 'fields' + 'form_class' conflict
        when a custom form_class (e.g. UserCreationForm) is provided via .clone().
        """
        context = super().get_context_data(**kwargs)
        context['view'] = self
        return context

    def get_form_class(self):
        """Return the form class, clearing fields if a custom form_class is set.

        This is the clean way to support both generic ModelForm (with fields='__all__')
        and specialized forms like UserCreationForm in djcrud_auth.
        """
        if hasattr(self, 'form_class') and self.form_class is not None:
            # Clear fields to avoid ImproperlyConfigured when both are present
            if hasattr(self, 'fields'):
                self.fields = None
            return self.form_class
        return super().get_form_class()

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
        return get_menu(self._controller, 'object', self.request, exclude_current=self, object=self.object)

    @attribute.cached
    def main_menu(self):
        """Get main navigation menu."""
        from djcrud.menu import get_menu
        if not self.root_controller:
            return []
        return get_menu(self.root_controller, 'main', self.request, exclude_current=self)


class CreateView(UnpolyModalMixin, View, generic.CreateView):
    """
    Create view for creating new model instances.

    Template: djcrud/modelform.html (extends form.html with model menu)
    """
    template_name = 'djcrud/modelform.html'
    action = 'click->modal#open'

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
    def model_meta(self):
        """Convenience getter for model._meta (Django templates disallow
        leading-underscore attributes like _meta).
        """
        return self.model._meta

    @attribute.getter
    def title(self):
        """Return page title."""
        model = self.model
        if model:
            return f"Create {model._meta.verbose_name.capitalize()}"
        return "Create"

    def get_context_data(self, **kwargs):
        """Add view to context - templates access everything via view.

        We override get_form_class to avoid the 'fields' + 'form_class' conflict
        when a custom form_class (e.g. UserCreationForm) is provided via .clone().
        """
        context = super().get_context_data(**kwargs)
        context['view'] = self
        return context

    def get_form_class(self):
        """Return the form class, clearing fields if a custom form_class is set.

        This is the clean way to support both generic ModelForm (with fields='__all__')
        and specialized forms like UserCreationForm in djcrud_auth.
        """
        if hasattr(self, 'form_class') and self.form_class is not None:
            # Clear fields to avoid ImproperlyConfigured when both are present
            if hasattr(self, 'fields'):
                self.fields = None
            return self.form_class
        return super().get_form_class()

    @attribute.cached
    def icon(self):
        """Icon for this view."""
        return 'plus-circle'

    # fields = '__all__' should be set on concrete subclasses (or via
    # ModelController) instead of here. This prevents "Specifying both 'fields'
    # and 'form_class' is not permitted" when cloning with a custom form_class.
    @attribute.cached
    def cancel_url(self):
        """Return URL to go back to."""
        # TODO: Implement proper back URL
        return '/'

    def get_success_url(self):
        """After successful create/update, redirect to the *detail* view of the new object.

        Per user: "success url must be object detail view". Simply calls
        object.get_absolute_url() (provided by the custom User model in djcrud_auth
        or by get_absolute_url on other models). Falls back to cancel_url.
        See tests/test_url_consistency.py for how namespaces ('auth:user:detail')
        and view.url() work.
        """
        if hasattr(self, 'object') and self.object and hasattr(self.object, 'get_absolute_url'):
            return self.object.get_absolute_url()
        # Final fallback
        return self.cancel_url or '/'

    @attribute.cached
    def main_menu(self):
        """Get main navigation menu."""
        from djcrud.menu import get_menu
        if not self.root_controller:
            return []
        return get_menu(self.root_controller, 'main', self.request, exclude_current=self)

    @attribute.cached
    def model_menu(self):
        """Get actions for this model (views with 'model' in menus)."""
        from djcrud.menu import get_menu
        if not self._controller:
            return []
        return get_menu(self._controller, 'model', self.request, exclude_current=self)


class UpdateView(UnpolyModalMixin, View, generic.UpdateView):
    """
    Update view for editing model instances.

    Template: djcrud/modelform.html (extends form.html with object menu)
    """
    template_name = 'djcrud/modelform.html'
    action = 'click->modal#open'

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
    def model_meta(self):
        """Convenience getter for model._meta (Django templates disallow
        leading-underscore attributes like _meta).
        """
        return self.model._meta

    @attribute.getter
    def title(self):
        """Return page title for update form.

        Uses the same pattern as ListView/CreateView. The title() @getter
        does all the work (per philosophy). This replaces the previous
        get_title() method.
        """
        model = self.model
        if model:
            return f"Edit {model._meta.verbose_name.capitalize()}"
        return "Edit"

    def get_context_data(self, **kwargs):
        """Add view to context - templates access everything via view.

        We override get_form_class to avoid the 'fields' + 'form_class' conflict
        when a custom form_class (e.g. UserCreationForm) is provided via .clone().
        """
        context = super().get_context_data(**kwargs)
        context['view'] = self
        return context

    def get_form_class(self):
        """Return the form class, clearing fields if a custom form_class is set.

        This is the clean way to support both generic ModelForm (with fields='__all__')
        and specialized forms like UserCreationForm in djcrud_auth.
        """
        if hasattr(self, 'form_class') and self.form_class is not None:
            # Clear fields to avoid ImproperlyConfigured when both are present
            if hasattr(self, 'fields'):
                self.fields = None
            return self.form_class
        return super().get_form_class()

    @attribute.cached
    def icon(self):
        """Icon for this view."""
        return 'pencil'

    # fields = '__all__' should be set on concrete subclasses (or via
    # ModelController) instead of here. This prevents "Specifying both 'fields'
    # and 'form_class' is not permitted" when cloning with a custom form_class.
    @attribute.cached
    def cancel_url(self):
        """Return URL to go back to."""
        # TODO: Implement proper back URL
        return '/'

    def get_success_url(self):
        """After successful create/update, redirect to the *detail* view of the new object.

        Per user: "success url must be object detail view". Simply calls
        object.get_absolute_url() (provided by the custom User model in djcrud_auth
        or by get_absolute_url on other models). Falls back to cancel_url.
        See tests/test_url_consistency.py for how namespaces ('auth:user:detail')
        and view.url() work.
        """
        if hasattr(self, 'object') and self.object and hasattr(self.object, 'get_absolute_url'):
            return self.object.get_absolute_url()
        # Final fallback
        return self.cancel_url or '/'

    @attribute.cached
    def main_menu(self):
        """Get main navigation menu."""
        from djcrud.menu import get_menu
        if not self.root_controller:
            return []
        return get_menu(self.root_controller, 'main', self.request, exclude_current=self)

    @attribute.cached
    def object_menu(self):
        """Get actions for this object (views with 'object' in menus)."""
        # TODO: This needs the controller context
        return []


class DeleteView(UnpolyModalMixin, View, generic.DeleteView):
    """
    Delete view for removing model instances.

    Template: djcrud/delete_confirm.html (provided by frontend app)

    Context variables:
        - object: The model instance to delete
        - title: Page title (from title getter)
        - icon: Icon name from icon attribute
        - main_menu: Sidebar menu items (views with 'main' in menus)
    """
    template_name = 'djcrud/delete_confirm.html'
    action = 'click->modal#open'

    @attribute.getter
    def model(self):
        """Get model from controller if not set directly on view."""
        if hasattr(self.__class__, '_model') and self.__class__._model is not None:
            return self.__class__._model
        controller = self._controller or self.controller
        if controller and hasattr(controller, 'model'):
            return controller.model
        return None

    @attribute.getter
    def model_meta(self):
        """Convenience getter for model._meta."""
        return self.model._meta

    @attribute.getter
    def title(self):
        """Return page title for delete confirmation."""
        model = self.model
        if model:
            return f"Delete {model._meta.verbose_name.capitalize()}"
        return "Delete"

    def get_context_data(self, **kwargs):
        """Add view to context - templates access everything via view."""
        context = super().get_context_data(**kwargs)
        context['view'] = self
        return context

    @attribute.cached
    def icon(self):
        """Icon for this view."""
        return 'trash'

    @attribute.cached
    def cancel_url(self):
        """Return URL to go back to (object detail page)."""
        if hasattr(self, 'object') and self.object and hasattr(self.object, 'get_absolute_url'):
            return self.object.get_absolute_url()
        return '/'

    def get_success_url(self):
        """After successful delete, redirect to list view.

        Uses the controller's list view URL if available.
        """
        # Try to get list view URL from controller
        if self._controller:
            for view in self._controller.views:
                # Check if it's a ListView (has 'main' or 'model' in menus typically)
                if hasattr(view, '__name__') and 'List' in view.__name__:
                    try:
                        # Create temp instance to get URL
                        temp_view = view.clone(request=self.request)()
                        return temp_view.url
                    except:
                        pass
        # Fallback to root
        return '/'

    @attribute.cached
    def main_menu(self):
        """Get main navigation menu."""
        from djcrud.menu import get_menu
        if not self.root_controller:
            return []
        return get_menu(self.root_controller, 'main', self.request, exclude_current=self)


__all__ = ['ListView', 'DetailView', 'CreateView', 'UpdateView', 'DeleteView']
