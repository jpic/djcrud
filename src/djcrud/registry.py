class Registry:
    """Ordered, codename-keyed route list built from a router declaration.

    Registering a route with an existing :attr:`~djcrud.route.Route.codename`
    replaces the previous entry — this is how cloned views override defaults.
    """

    def __init__(self, router, routes=()):
        """Attach to *router* and register each declared *routes* entry."""
        self.router = router
        self._items = []
        self._by_codename = {}
        for route in routes:
            self.register(route)

    def register(self, route):
        """Clone *route* for ``self.router``, instantiate, and store by codename."""
        cls = route if isinstance(route, type) else type(route)
        cls = cls.clone(router=self.router)
        instance = cls()
        if instance.codename in self._by_codename:
            old = self._by_codename[instance.codename]
            self._items[self._items.index(old)] = instance
        else:
            self._items.append(instance)
        self._by_codename[instance.codename] = instance
        return instance

    def __setitem__(self, codename, route):
        """Replace (or add) the route registered under *codename*."""
        cls = route if isinstance(route, type) else type(route)
        cls = cls.clone(router=self.router)
        instance = cls()
        if codename in self._by_codename:
            old = self._by_codename[codename]
            self._items[self._items.index(old)] = instance
        else:
            self._items.append(instance)
        self._by_codename[codename] = instance

    def __getitem__(self, key):
        """Return a route by integer index or string codename."""
        if isinstance(key, int):
            return self._items[key]
        return self._by_codename[key]

    def __delitem__(self, codename):
        """Remove the route registered under *codename*."""
        instance = self._by_codename.pop(codename)
        self._items.remove(instance)

    def __iter__(self):
        """Iterate routes in registration order."""
        return iter(self._items)
