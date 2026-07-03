import djcrud
from djcrud.router import Router as DjcrudRouter


def get_built_site():
    site = djcrud.site
    if not hasattr(site, "registry"):
        site.build()
    return site


def resolve_field(obj, path):
    for part in path.split("__"):
        obj = getattr(obj, part, None)
        if obj is None:
            return ""
    return obj


class RouteCollection(list):
    def filter(self, *args, **kwargs):
        qs = RouteCollection(self)
        for key, value in kwargs.items():
            qs = qs._apply_lookup(key, value)
        return qs

    def _apply_lookup(self, lookup, value):
        parts = lookup.split("__")
        if parts[-1] == "icontains":
            path = "__".join(parts[:-1])
            term = str(value).lower()
            return RouteCollection(
                item for item in self if term in str(resolve_field(item, path)).lower()
            )
        if len(parts) == 1:
            return RouteCollection(
                item for item in self if getattr(item, parts[0], None) == value
            )
        path = "__".join(parts)
        return RouteCollection(
            item for item in self if resolve_field(item, path) == value
        )

    def distinct(self):
        return self

    def get(self, **kwargs):
        if "pk" in kwargs:
            for item in self:
                if str(item.pk) == str(kwargs["pk"]):
                    return item
            raise self.model.DoesNotExist(
                f'Route matching query does not exist: pk={kwargs["pk"]!r}'
            )
        raise TypeError("RouteCollection.get() requires pk=...")

    @property
    def model(self):
        if not self:
            return None
        return type(self[0])


from djcrud.introspection import compute_fullurlpath


def router_pk(route, parent_pk=""):
    model = getattr(type(route), "model", None)
    if model is not None:
        return f"{model._meta.app_label}.{model.__name__}"
    codename = route.codename
    if parent_pk:
        return f"{parent_pk}.{codename}"
    return codename


def router_app_model(route):
    model = getattr(type(route), "model", None)
    if model is not None:
        return (
            str(model._meta.app_config.verbose_name),
            str(model._meta.verbose_name).capitalize(),
        )
    return "-", "-"


def walk_site(site):
    from .models import Router, URL

    routers = []
    router_map = {}

    def process_router(router, parent_pk=""):
        app, model_label = router_app_model(router)
        record = Router(
            pk=router_pk(router, parent_pk),
            app=app,
            model=model_label,
            codename=router.codename,
            urlpath=router.urlpath,
            urlname=router.urlname,
        )
        record.route = router
        routers.append(record)
        router_map[id(router)] = record

        for route in router.routes:
            if isinstance(route, DjcrudRouter):
                process_router(route, record.pk)

    urls = []

    def process_urls(router):
        parent = router_map.get(id(router))
        for route in router.routes:
            if isinstance(route, DjcrudRouter):
                process_urls(route)
                continue
            tags = ",".join(getattr(route, "tags", []))
            url = URL(
                pk=route.urlfullname,
                router=parent,
                urlpath=route.urlpath,
                fullurlpath=compute_fullurlpath(route),
                urlname=route.urlname,
                urlfullname=route.urlfullname,
                view_class=type(route).__name__,
                view_module=type(route).__module__,
                tags=tags,
            )
            url.route = route
            urls.append(url)

    process_router(site)
    process_urls(site)

    return {
        "routers": routers,
        "urls": urls,
    }


class DebugListMixin:
    def get_queryset(self):
        qs = self.model._default_manager.all()
        form = self.filter_form
        if form is None or not form.is_valid():
            return qs
        term = form.cleaned_data.get(self.search_param, "")
        if not term:
            return qs
        term = term.lower()

        def matches(obj):
            for field in self.search_fields:
                if term in str(resolve_field(obj, field)).lower():
                    return True
            return False

        return RouteCollection(item for item in qs if matches(item))
