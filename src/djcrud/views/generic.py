"""Generic CRUD views for djcrud.

Inherit from djcrud.mvc.View + django.views.generic.
Provide model, model_meta, title, icon, tags, model_fields, table via attributes/getters.
"""
from django.views import generic
from djcrud.mvc import View
from djcrud import attribute
from djcrud.views.unpoly import UnpolyMixin
from djcrud.views.tables2 import Tables2Mixin


class ListView(UnpolyMixin, Tables2Mixin, View, generic.ListView):
    tags = ['main']
    template_name = 'djcrud/list.html'
    paginate_by = 25
    urlpath = ''
    urlname = 'list'
    icon = 'list'
    color = 'primary'  # blue

    @attribute.getter
    def model(self):
        if hasattr(self.__class__, '_model') and self.__class__._model is not None:
            return self.__class__._model
        controller = self._controller or getattr(self, 'controller', None)
        if controller and hasattr(controller, 'model'):
            return controller.model
        return None

    @attribute.getter
    def model_meta(self):
        return self.model._meta

    @attribute.getter
    def title(self):
        model = self.model
        if model:
            return model._meta.verbose_name_plural.capitalize()
        return 'List'

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

    def get_form_class(self):
        if hasattr(self, 'form_class') and self.form_class is not None:
            if hasattr(self, 'fields'):
                self.fields = None
            return self.form_class
        return super().get_form_class()


class DetailView(UnpolyMixin, View, generic.DetailView):
    tags = ['object']
    template_name = 'djcrud/detail.html'
    urlpath = '<int:pk>/'
    urlname = 'detail'

    @attribute.getter
    def model(self):
        if hasattr(self.__class__, '_model') and self.__class__._model is not None:
            return self.__class__._model
        controller = self._controller or getattr(self, 'controller', None)
        if controller and hasattr(controller, 'model'):
            return controller.model
        return None

    @attribute.getter
    def model_meta(self):
        return self.model._meta

    @attribute.getter
    def title(self):
        return str(self.object)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

    def get_form_class(self):
        if hasattr(self, 'form_class') and self.form_class is not None:
            if hasattr(self, 'fields'):
                self.fields = None
            return self.form_class
        return super().get_form_class()

    icon = 'eye'
    color = 'primary'  # blue

    @attribute.getter
    def model_fields(self):
        obj = getattr(self, 'object', None)
        if not obj:
            return []

        fields = []
        meta = self.model_meta

        for field in meta.get_fields():
            if field.auto_created and not field.concrete:
                continue

            try:
                value = getattr(obj, field.name)

                if value is None:
                    value = '-'
                elif hasattr(value, 'all'):
                    try:
                        value = ', '.join(str(v) for v in value.all())
                    except Exception:
                        value = str(value)
                else:
                    value = str(value)

                fields.append({
                    'label': field.verbose_name.capitalize() if hasattr(field, 'verbose_name') else field.name,
                    'value': value,
                })
            except (AttributeError, ValueError):
                continue

        return fields


class CreateView(UnpolyMixin, View, generic.CreateView):
    tags = ['model']
    template_name = 'djcrud/modelform.html'
    action = 'click->modal#open'
    urlpath = 'create'
    urlname = 'create'

    @attribute.getter
    def model(self):
        if hasattr(self.__class__, '_model') and self.__class__._model is not None:
            return self.__class__._model
        controller = self._controller or getattr(self, 'controller', None)
        if controller and hasattr(controller, 'model'):
            return controller.model
        return None

    @attribute.getter
    def model_meta(self):
        return self.model._meta

    @attribute.getter
    def title(self):
        model = self.model
        if model:
            return f"Create {model._meta.verbose_name.capitalize()}"
        return "Create"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

    def get_form_class(self):
        if hasattr(self, 'form_class') and self.form_class is not None:
            if hasattr(self, 'fields'):
                self.fields = None
            return self.form_class
        return super().get_form_class()

    icon = 'plus-circle'
    color = 'success'  # green

    cancel_url = '/'

    def get_success_url(self):
        if hasattr(self, 'object') and self.object and hasattr(self.object, 'get_absolute_url'):
            return self.object.get_absolute_url()
        return self.cancel_url or '/'


class UpdateView(UnpolyMixin, View, generic.UpdateView):
    tags = ['object']
    template_name = 'djcrud/modelform.html'
    action = 'click->modal#open'
    urlpath = '<int:pk>/edit/'
    urlname = 'edit'

    @attribute.getter
    def model(self):
        if hasattr(self.__class__, '_model') and self.__class__._model is not None:
            return self.__class__._model
        controller = self._controller or getattr(self, 'controller', None)
        if controller and hasattr(controller, 'model'):
            return controller.model
        return None

    @attribute.getter
    def model_meta(self):
        return self.model._meta

    @attribute.getter
    def title(self):
        model = self.model
        if model:
            return f"Edit {model._meta.verbose_name.capitalize()}"
        return "Edit"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

    def get_form_class(self):
        if hasattr(self, 'form_class') and self.form_class is not None:
            if hasattr(self, 'fields'):
                self.fields = None
            return self.form_class
        return super().get_form_class()

    icon = 'pencil'
    color = 'warning'  # orange

    cancel_url = '/'

    def get_success_url(self):
        if hasattr(self, 'object') and self.object and hasattr(self.object, 'get_absolute_url'):
            return self.object.get_absolute_url()
        return self.cancel_url or '/'


class DeleteView(UnpolyMixin, View, generic.DeleteView):
    tags = ['object']
    template_name = 'djcrud/delete.html'
    action = 'click->modal#open'
    partial_name = 'content'
    urlpath = '<int:pk>/delete/'
    urlname = 'delete'


    @attribute.getter
    def model(self):
        if hasattr(self.__class__, '_model') and self.__class__._model is not None:
            return self.__class__._model
        controller = self._controller or getattr(self, 'controller', None)
        if controller and hasattr(controller, 'model'):
            return controller.model
        return None

    @attribute.getter
    def model_meta(self):
        return self.model._meta

    @attribute.getter
    def title(self):
        model = self.model
        if model:
            return f"Delete {model._meta.verbose_name.capitalize()}"
        return "Delete"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

    icon = 'trash'
    color = 'danger'  # red
    cancel_url = '/'

    def get_success_url(self):
        if self._controller:
            for view in self._controller.views:
                if hasattr(view, '__name__') and 'List' in view.__name__:
                    try:
                        temp_view = view.clone(request=self.request)()
                        return temp_view.url
                    except:
                        pass
        return '/'


__all__ = ['ListView', 'DetailView', 'CreateView', 'UpdateView', 'DeleteView']
