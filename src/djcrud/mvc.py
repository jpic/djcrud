from djcrud import attribute
from django.views import generic
from django.urls import path, include, reverse, reverse_lazy
from django.utils.text import slugify


class ControllerViewsList(list):
    """
    A list subclass that automatically clones views when they're added.

    This ensures that every view/controller in the list has proper parent
    references set.
    """

    def __init__(self, controller, items=None):
        """Initialize with parent controller reference."""
        self.controller = controller
        super().__init__()
        if items:
            self.extend(items)

    def _clone_and_set_parent(self, item):
        """Clone an item and set its parent controller reference."""
        # If it's a controller instance, use it directly and set its parent
        if isinstance(item, Controller):
            item.parent_controller = self.controller
            return item
        # If it's a controller class, instantiate it with parent set
        elif isinstance(item, type) and issubclass(item, Controller):
            # Instantiate the controller with its parent
            instance = item(views=item.views, parent=self.controller)
            return instance
        else:
            # It's a view class - clone it
            kwargs = {}

            # If controller has a model and view doesn't, pass it to clone
            if hasattr(self.controller, 'model') and self.controller.model:
                if not hasattr(item, 'model') or item.model is None:
                    kwargs['model'] = self.controller.model

            cloned = item.clone(**kwargs) if hasattr(item, 'clone') else item

            # Set parent controller reference
            cloned.controller = self.controller

            return cloned

    def append(self, item):
        """Append a view/controller, cloning it first."""
        cloned = self._clone_and_set_parent(item)
        super().append(cloned)

    def insert(self, index, item):
        """Insert a view/controller, cloning it first."""
        cloned = self._clone_and_set_parent(item)
        super().insert(index, cloned)

    def extend(self, items):
        """Extend with multiple views/controllers, cloning each."""
        for item in items:
            self.append(item)

    def __setitem__(self, index, item):
        """Set an item by index, cloning it first."""
        cloned = self._clone_and_set_parent(item)
        super().__setitem__(index, cloned)

    def __add__(self, other):
        """Return a new regular list when using + operator."""
        # Return a regular list, not a ControllerViewsList
        # This prevents issues with Django internals
        return list(self) + list(other)


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
    cls = attribute.cls()
    urlpath = ''  # Default to empty string (root controller)

    def __init__(self, views, parent=None):
        # Use custom list that auto-clones on mutation
        self.views = ControllerViewsList(self, views)

        # Set parent controller for this controller
        self.parent_controller = parent

    @attribute.getter
    def root_controller(self):
        """Get the root controller by traversing up the hierarchy."""
        controller = self
        while hasattr(controller, 'parent_controller') and controller.parent_controller:
            controller = controller.parent_controller
        return controller

    @attribute.getter
    def urlname(self):
        """Return URL namespace for this controller.

        Slugifies the class name (minus 'Controller' suffix). For ModelController
        with a model, it will use the model's name (via Clonable naming).
        This enables 'auth:user:list' style names as expected in tests and README.
        """
        name = self.cls.__name__.replace('Controller', '')
        return slugify(name).lower()

    @attribute.getter
    def urlpatterns(self):
        """
        Return URL patterns for this controller.

        If controller has a urlpath, wrap children in include() with namespace.
        Otherwise, return children directly (root controller).
        """
        # Build child patterns
        child_patterns = []
        views = self.views if isinstance(self, Controller) else getattr(self, 'views', [])

        for view in views:
            # All views/controllers are classes, get their urlpatterns
            child_patterns += view.urlpatterns

        # Get urlpath (handle both class and instance access)
        urlpath = self.urlpath if isinstance(self, Controller) else getattr(self, 'urlpath', '')

        if urlpath:
            # Non-root controller: wrap in namespace. Ensure trailing / for directory-like paths.
            urlpath_for_include = urlpath if urlpath.endswith('/') else urlpath + '/'
            return [
                path(
                    urlpath_for_include,
                    include((child_patterns, self.urlname))
                )
            ]
        else:
            # Root controller: return children directly
            return child_patterns


class View(Clonable, generic.View):
    cls = attribute.cls()
    controller = None  # Set by Controller.__init__
    _controller = None  # Passed via as_view()
    _root_controller = None  # Passed via as_view()

    def __init__(self, **kwargs):
        # Extract our custom kwargs before passing to parent
        self._controller = kwargs.pop('_controller', None) or self.controller
        self._root_controller = kwargs.pop('_root_controller', None)
        super().__init__(**kwargs)

    @attribute.getter
    def urlpath(self):
        """Return URL path for this view.

        Slugifies the class name (minus 'View' suffix). This produces clean paths
        like 'mycustom' for MyCustomView. Combined with explicit urlpath overrides
        in clone(), enables flexible URL structures.
        """
        name = self.cls.__name__.replace('View', '')
        return slugify(name).lower()

    @attribute.getter
    def urlname(self):
        """Return URL name for this view.

        Slugifies the class name (minus 'View' suffix). This produces clean names
        like 'list', 'create', 'detail', 'edit' (instead of full class name).
        Combined with controller urlname, enables reverse('auth:user:list').
        See tests/test_url_consistency.py and README for examples.
        """
        name = self.cls.__name__.replace('View', '').replace('List', 'list').replace('Create', 'create').replace('Detail', 'detail').replace('Update', 'edit')
        return slugify(name).lower()

    @attribute.getter
    def urlpatterns(self):
        # Add trailing slash if urlpath is not empty. Avoid double-slash for paths that already end with /
        urlpath = self.urlpath
        if not urlpath.endswith('/') and urlpath:
            urlpath += '/'

        # Compute root controller by traversing from controller attribute
        root = None
        if self.controller:
            controller = self.controller
            while hasattr(controller, 'parent_controller') and controller.parent_controller:
                controller = controller.parent_controller
            root = controller

        # Pass controller reference through as_view's initkwargs
        # This makes root_controller available to view instances
        view_func = self.as_view(
            _controller=self.controller,
            _root_controller=root,
        )

        return [
            path(urlpath, view_func, name=self.urlname)
        ]

    @attribute.getter
    def has_perm(self):
        try:
            # secure by default: implement has_perm yourself
            return self.request.user.is_superuser
        except AttributeError:
            return False

    @attribute.getter
    def root_controller(self):
        """Get the root controller by traversing up from this view's controller."""
        # Use the injected root_controller if available (from as_view)
        if self._root_controller:
            return self._root_controller

        # Fall back to traversing from controller
        controller = self._controller or self.controller
        if not controller:
            return None
        return controller.root_controller

    @attribute.cached
    def url(self):
        """Get the URL for this view."""
        from django.urls import reverse
        # Build the namespace from controller hierarchy
        namespaces = []
        # Try instance attributes first, then class attributes
        controller = self._controller or self.controller or getattr(self.__class__, 'controller', None)
        while controller:
            if hasattr(controller, 'urlname') and controller.urlname:
                namespaces.insert(0, controller.urlname)
            controller = getattr(controller, 'parent_controller', None)

        # Build the full URL name
        if namespaces:
            full_name = ':'.join(namespaces) + ':' + self.urlname
        else:
            full_name = self.urlname

        # For views that need a pk (DetailView, UpdateView, etc.), pass it from self.object
        kwargs = {}
        if hasattr(self, 'object') and self.object is not None:
            # Object has a pk, pass it to reverse
            if hasattr(self.object, 'pk'):
                kwargs['pk'] = self.object.pk

        return reverse(full_name, kwargs=kwargs) if kwargs else reverse(full_name)

    @attribute.getter
    def title(self):
        """Get the title for this view."""
        return self.cls.__name__
