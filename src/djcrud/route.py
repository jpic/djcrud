from django.urls import reverse


class Route:
    """Base routing node: URL names, paths, and reverse lookups.

    Routers and views subclass ``Route``. Each node contributes a
    :attr:`codename` segment to the nested URL namespace.
    """

    @property
    def title(self):
        """Human-readable label, usually derived from the class name."""
        return type(self).__name__

    @property
    def codename(self):
        """URL namespace segment derived from the class name (lowercase)."""
        return type(self).__name__.replace(" ", "_").lower()

    def __str__(self):
        return self.title

    @property
    def urlpath(self):
        """Path segment appended under the parent router."""
        return self.codename + "/"

    @property
    def urlname(self):
        """Short URL name used as the final component of :attr:`urlfullname`."""
        return self.codename

    @property
    def urlpatterns(self):
        """Django URL patterns for this node and its children."""
        raise NotImplementedError("Use Router or View classes")

    @property
    def urlfullname(self):
        """Fully qualified URL name (``parent:child:view``)."""
        name = self.urlname
        current = self
        while parent := getattr(current, "router", None):
            name = f"{parent.urlname}:{name}"
            current = parent
        return name

    @property
    def url(self):
        """Resolved URL path for this route (no arguments)."""
        return self.reverse()

    def reverse(self, *args, **kwargs):
        """Reverse :attr:`urlfullname` with positional or keyword arguments."""
        return reverse(self.urlfullname, args=args, kwargs=kwargs)
