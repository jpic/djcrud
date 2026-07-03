from django.forms.widgets import Script

import djcrud
from djcrud.static import vite_asset
from djcrud.views.spa import SPAView


class SpaView(SPAView):
    title = "SPA demo"
    icon = "grid"
    mount_element = '<div id="app"></div>'

    class Media(SPAView.Media):
        js = SPAView.Media.js + (
            Script(vite_asset("spa_example/js/app.js"), type="module"),
        )


djcrud.site.routes.append(SpaView)
