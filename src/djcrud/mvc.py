from djcrud import attribute
from django.views import generic
from django.urls import path, reverse, reverse_lazy


class Clonable:
    @classmethod
    def clone(cls, *mixins, **attributes):
        """Return a subclass with the given attributes.

        If a model is found, it will prefix the class name with the model.
        """
        name = cls.__name__
        model = attributes.get('model', getattr(cls, 'model', None))
        if model and model.__name__ not in cls.__name__:
            name = '{}{}'.format(model.__name__, cls.__name__)
        return type(name, (cls,) + mixins, attributes)


class Controller(Clonable):
    def __init__(self, views):
        self.views = views

    @attribute.getter
    def urlpatterns(self):
        result = []
        for view in self.views:
            results += view.urlpatterns
        return result


class View(Clonable, generic.View):
    @attribute.getter
    def urlpath(self):
        # TODO: this should be slugified view class name without the
        # View suffix
        return type(self).__name__

    @attribute.getter
    def urlname(self):
        # TODO: this should be a slugified view class name without the View suffix
        return type(self).__name__

    @attribute.getter
    def urlpatterns(self):
        return [
            path(cls.urlpath, cls.as_view(), name=cls.urlname)
        ]
