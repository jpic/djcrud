from django.forms.widgets import Script

import djcrud
from djcrud.views.spa import SPAView


class SpaView(SPAView):
    title = "SPA demo"
    icon = "grid"

    class Media(SPAView.Media):
        js = SPAView.Media.js + (
            Script("spa_example/js/app.js", type="module"),
        )


djcrud.site.routes.append(SpaView)