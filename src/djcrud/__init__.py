from .controller import Controller
from .views.template import TemplateView


site = Controllers(
    views=[
        TemplateView.clone(
            icon='home',
            template_name='crudlfap/home.html',
            menus=['main'],
            title=_('Home'),
            title_menu=_('Home'),
            title_heading='',
            urlname='home',
            urlpath='',
            authenticate=False,
        ),
    ]
)
