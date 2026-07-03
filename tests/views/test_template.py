import djcrud


def test_get_context_data():
    view = djcrud.views.TemplateView()
    assert view.get_context_data()["view"] is view


def test_get_template_names():
    assert djcrud.site.routes["auth"].routes["login"].get_template_names() == [
        "djcrud/site/auth/login.html",
        "djcrud/auth/login.html",
        "djcrud/login.html",
        "djcrud/form.html",
        "site/auth/login.html",
        "auth/login.html",
        "login.html",
        "form.html",
    ]
