import djcrud
from djcrud.views.spa import SPAView


class SpaView(SPAView):
    """Full-screen SPA shell for embedding client frameworks."""

    title = "SPA demo"
    icon = "grid"
    urlpath = "spa/"

    class Media(SPAView.Media):
        js = SPAView.Media.js + ("spa_example/js/app.js",)


djcrud.site.routes.append(SpaView)