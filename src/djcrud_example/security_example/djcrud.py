import djcrud
from djcrud.permissions import authenticated

from .models import Document

# all can view all
djcrud.permissions.add_perm(Document, "view", check=lambda user, **ctx: True)
# authenticated can add
djcrud.permissions.add_perm(Document, "add", check=authenticated)


# change/delete only your own
def secured_document_change(user, *, obj, **ctx):
    if obj is None:
        return False
    return user.is_superuser or obj.owner_id == user.pk


djcrud.permissions.add_perm(Document, "change,delete", check=secured_document_change)


def can_publish(user, *, obj, **ctx):
    if obj is None:
        return False
    return obj.owner_id == user.pk and not obj.published


djcrud.permissions.add_perm(Document, "publish", check=can_publish)


# drafts visible only to owner and superuser
def document_queryset(user, *, model, action, perm, obj, **kwargs):
    qs = model.objects.all()
    if user.is_superuser:
        return qs
    if not user.is_authenticated:
        return qs.filter(published=True)
    return qs.filter(published=True) | qs.filter(owner=user)


djcrud.permissions.add_queryset(Document, scoper=document_queryset)


class SecuredDocumentCreateView(djcrud.views.CreateView):
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class PublishView(djcrud.views.ObjectFormView):
    permission_shortcode = "publish"
    title = "Publish"
    icon = "send"
    color = "success"

    def form_valid(self, form):
        self.object.publish()
        return super().form_valid(form)


class SecuredDocumentRouter(djcrud.ModelRouter):
    model = Document
    icon = "shield-lock"

    routes = djcrud.ModelRouter.routes[:-1] + [
        SecuredDocumentCreateView,
        PublishView,
    ]


djcrud.site.routes.append(SecuredDocumentRouter)
