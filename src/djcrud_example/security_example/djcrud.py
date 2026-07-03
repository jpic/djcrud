import djcrud

from .models import Document


def secured_document_change(user, *, obj, **ctx):
    if obj is not None:
        return user.is_authenticated and (
            user.is_superuser or obj.owner_id == user.pk
        )
    return user.is_authenticated


secured_document_delete = secured_document_change


def document_queryset(user, *, model, action, perm, obj, router, **kwargs):
    qs = model.objects.all()
    if action in ("change", "delete"):
        if not user.is_authenticated:
            return qs.none()
        if user.is_superuser:
            return qs
        return qs.filter(owner=user)
    return qs


class SecuredDocumentCreateView(djcrud.generic.CreateView):
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid()


class SecuredDocumentRouter(djcrud.ModelRouter):
    model = Document
    icon = "shield-lock"

    @property
    def codename(self):
        return "secured-document"

    routes = djcrud.ModelRouter.routes[:-1] + [
        SecuredDocumentCreateView,
    ]


djcrud.add_perm(
    Document,
    "view",
    check=lambda user, **ctx: True,
    router="secured-document",
)
djcrud.add_perm(
    Document,
    "add",
    check=djcrud.authenticated,
    router="secured-document",
)
djcrud.add_perm(
    Document,
    "change",
    check=secured_document_change,
    router="secured-document",
)
djcrud.add_perm(
    Document,
    "delete",
    check=secured_document_delete,
    router="secured-document",
)
djcrud.add_queryset(
    Document,
    scoper=document_queryset,
    router="secured-document",
)

djcrud.site.routes.append(SecuredDocumentRouter)