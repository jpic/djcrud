import djcrud
from djcrud.views import generic

from .models import Router, URL
from .routing_debug import DebugListMixin


class RouterListView(DebugListMixin, generic.ListView):
    search_fields = ("app", "model", "codename")
    table_fields = ("app", "model", "codename", "urlpath")


class URLListView(DebugListMixin, generic.ListView):
    search_fields = (
        "urlfullname",
        "fullurlpath",
        "view_class",
        "router__app",
    )
    table_fields = ("router", "view_class", "fullurlpath", "urlfullname")


class RoutingDebugRouter(djcrud.Router):
    codename = "debug"
    icon = "bug"
    color = "warning"
    routes = [
        djcrud.ModelRouter.clone(
            model=Router,
            icon="diagram-3",
            routes=[
                RouterListView,
                generic.DetailView,
            ],
        ),
        djcrud.ModelRouter.clone(
            model=URL,
            icon="signpost-split",
            routes=[
                URLListView,
                generic.DetailView,
            ],
        ),
    ]
