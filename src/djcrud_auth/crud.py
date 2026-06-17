from django.contrib.auth.models import User, Group

from djcrud import views
from djcrud import mixins
from djcrud import attribute


class UserListView(mixins.Tables2Mixin, views.ListView):
    template_name = 'djcrud/list.html'
    body_class = 'small-margin'
    menus = ['main', 'model']
    urlpath = ''

    def title(self):
        # this needs to be translated
        return self.model._meta.verbose_name_plural.capitalize()

    # we want this computed once and for all: we'll be accessing it as a
    # property
    @attribute.cached
    def icon(self):
        return getattr(self.model, 'djcrud_icon', 'list')

    # @property here to desguise the possibility of having a subclass that
    # Allow sub-classing with table_class = some_namespace.ImportedTable.
    @attribute.cached
    def table_class(self):
        import django_tables2 as tables

        class UserTable(tables.Table):
            class Meta:
                model = User
                fields = ('username', 'email')

        return UserTable


class UserCreateView(views.ListView):
    urlpath = 'create'
    template_name = 'djcrud/form.html'
    body_class = 'centered'

    def title(self):
        return f'Create {self.model._meta.verbose_name.capitalize()}'

    @attribute.getter
    def model_form(self):
        return modelform_factory(self.model)


class UserController(djcrud.Controller):
    urlpath = 'user'
    model = User
    views = [
        # djcrud.Controller.as_urls() return the joined list of urls from each
        # view's .as_urls()
        # a URL may declare multiple views, even though the default one is the
        # urlpath attribute
        UserListView,
        UserCreateView,
    ]


class AuthController(djcrud.Controller):
    urlpath = 'auth'
    views = [
        # this lets UserController return its urls for its own views in /auth/user
        UserController,
        # TODO: GroupController,
    ]
