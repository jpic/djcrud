class Clonable:
    """Mixin for declaring specialized subclasses at runtime.

    Routers and views use :meth:`clone` to override attributes without
    defining a new module-level class.
    """

    @classmethod
    def clone(cls, *mixins, **attributes):
        """Return a subclass with the given attributes.

        If a model is found, it will prefix the class name with the model.
        """
        name = cls.__name__
        return type(name, (cls,) + mixins, attributes)
