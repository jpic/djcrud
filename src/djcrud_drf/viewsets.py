from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from djcrud.permissions import get_queryset, has_permission
from djcrud.clonable import Clonable
from djcrud.permission import PermissionMixin
from djcrud.route import Route

from .serializers import serializer_for_model

ACTION_SHORTCODES = {
    "list": "view",
    "retrieve": "view",
    "create": "add",
    "update": "change",
    "partial_update": "change",
    "destroy": "delete",
}

OBJECT_ACTIONS = frozenset({"retrieve", "update", "partial_update", "destroy"})


def action_shortcode(action):
    """Map DRF action to permission shortcode; custom actions use the method name."""
    return ACTION_SHORTCODES.get(action, action)


class ModelViewSet(PermissionMixin, viewsets.ModelViewSet):
    """Default CRUD ViewSet wired to the :mod:`djcrud.permissions` registry."""

    model = None
    permission_classes = [IsAuthenticated]
    _built_router = None

    @classmethod
    def build_router(cls):
        router_model = cls.model
        api_path = router_model.__name__.lower()

        class BuiltRouter(Clonable, Route):
            urlpath = api_path
            model = router_model

            @property
            def codename(self):
                return router_model.__name__.lower()

            def build(self):
                return self

        return BuiltRouter().build()

    def _permission_model(self):
        return self.model

    @property
    def permission_shortcode(self):
        return action_shortcode(self.action)

    @property
    def permission_codename(self):
        return f"{self.permission_shortcode}_{self.model._meta.model_name}"

    @property
    def permission_fullcode(self):
        return f"{self.model._meta.app_label}.{self.permission_codename}"

    def get_queryset(self):
        return get_queryset(**self.permission_context())

    def get_serializer_class(self):
        return serializer_for_model(self.model)

    def check_permissions(self, request):
        super().check_permissions(request)
        gate_action = action_shortcode(self.action)
        if self.action in OBJECT_ACTIONS:
            gate_action = "view"
        ctx = self.permission_context()
        ctx["action"] = gate_action
        ctx["perm"] = (
            f"{self.model._meta.app_label}."
            f"{gate_action}_{self.model._meta.model_name}"
        )
        ctx["obj"] = None
        if not has_permission(**ctx):
            self.permission_denied(request)

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if not has_permission(**self.permission_context(obj=obj)):
            self.permission_denied(request)