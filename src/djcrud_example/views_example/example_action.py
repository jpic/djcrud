from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

import djcrud
from djcrud.model import ModelMixin
from djcrud.views.action import ActionMixin
from djcrud.views.object import ObjectMixin


class PublishView(ActionMixin, ObjectMixin, ModelMixin, djcrud.View):
    """Publish a draft article — gated by ``publish`` in the permission registry."""

    permission_shortcode = "publish"
    tags = ["object"]
    title = _("Publish")
    icon = "send"
    color = "success"

    def unpoly_attributes(self, context=None):
        attrs = super().unpoly_attributes(context)
        attrs["up-method"] = "post"
        return attrs

    def post(self, request, *args, **kwargs):
        self.object.publish()
        messages.success(request, _("Article published."))
        detail_route = self.router.find_route("detail")
        detail_view = type(detail_route)(request=request, object=self.object)
        return HttpResponseRedirect(detail_view.url)