from django import forms
from django.utils.translation import gettext_lazy as _, ngettext

import djcrud

from .models import Post


class SetCategoryForm(forms.Form):
    category = forms.CharField(max_length=50, label=_("Category"))


class SetCategoryView(djcrud.generic.ListActionView):
    """Bulk-update category on selected rows."""

    permission_shortcode = "change"
    title = _("Set category")
    icon = "tag"
    color = "info"
    message = _("Choose a category for the selected posts.")
    form_class = SetCategoryForm

    def form_valid(self, form):
        self.object_list.update(category=form.cleaned_data["category"])
        return super().form_valid(form)

    def get_form_valid_message(self):
        count = self.object_list.count()
        return ngettext(
            "Updated category on %(count)d post.",
            "Updated category on %(count)d posts.",
            count,
        ) % {"count": count}


class PostRouter(djcrud.ModelRouter):
    model = Post
    icon = "chat-square-text"

    routes = djcrud.ModelRouter.routes + [
        SetCategoryView,
    ]


post_router = PostRouter