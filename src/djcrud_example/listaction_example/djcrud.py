from django import forms

import djcrud

from .models import Post


class SetCategoryForm(forms.Form):
    category = forms.CharField(max_length=50, label="Category")


class SetCategoryView(djcrud.views.ListActionView):
    permission_shortcode = "change"
    title = "Set category"
    icon = "tag"
    color = "info"
    message = "Choose a category for the selected posts."
    form_class = SetCategoryForm

    def form_valid(self, form):
        self.object_list.update(category=form.cleaned_data["category"])
        return super().form_valid(form)


class PostRouter(djcrud.ModelRouter):
    model = Post
    icon = "chat-square-text"

    routes = djcrud.ModelRouter.routes + [
        SetCategoryView,
    ]


djcrud.site.routes.append(PostRouter)