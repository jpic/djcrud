from pathlib import Path
from types import SimpleNamespace

import djcrud
import pytest
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import generic

from django.forms import Media

from django.forms.widgets import Script

from djcrud.media import SpaShellMedia
from djcrud.redirect import FULL_PAGE_LINK_ATTRIBUTES, apply_unpoly_target
from djcrud.templatetags.djcrud import unpoly_attributes
from djcrud.view import ViewMixin, uses_spa_shell
from djcrud.views.spa import SPAView
from djcrud.views.template import TemplateViewMixin


class _SpaRoot:
    title = "Test"

    def get_tagged_views(self, tag, request=None):
        return []


class _SpaRouter:
    root = _SpaRoot()


class _SpaView:
    router = _SpaRouter()
    unpoly = SimpleNamespace(mode="")
    breadcrumbs = []
    media = Media(media=SpaShellMedia)
    mount_element = '<div id="app"></div>'


def test_spa_view_default_mount_element():
    assert SPAView.mount_element == '<div id="app"></div>'


def test_spa_view_mount_element_and_module_media():
    class DashboardView(SPAView):
        mount_element = '<div id="app"><p>Loading…</p></div>'

        class Media(SPAView.Media):
            js = SPAView.Media.js + (Script("myapp/js/dashboard.js", type="module"),)

    view = DashboardView()

    assert view.mount_element == '<div id="app"><p>Loading…</p></div>'
    rendered_js = "".join(view.media.render_js())
    assert 'type="module"' in rendered_js
    assert "myapp/js/dashboard.js" in rendered_js
    assert "unpoly-config.js" in rendered_js


def test_spa_template_is_minimal_shell():
    spa_view = _SpaView()
    html = render_to_string("djcrud/test_spa.html", {"view": spa_view})

    assert '<nav class="navbar"' not in html
    assert "djcrud-spa-body" in html
    assert "djcrud-main-spa" in html
    assert "spa-body" in html
    assert 'id="sidebar"' in html
    assert "is-hidden" in html
    assert "hamburger-menu" not in html
    assert "navigation-menu.js" not in html
    assert "unpoly-config.js" in html
    assert "djcrud-layout-immersive" not in html


def test_spa_css_layout_rules():
    css_path = (
        Path(__file__).resolve().parents[1]
        / "src/djcrud_bulma/static/djcrud_bulma/css/style.css"
    )
    css = css_path.read_text()

    assert ".djcrud-layout-spa" in css
    assert ".djcrud-layout-spa > .djcrud-sidebar" in css
    assert "overflow-y: auto" in css.split(".djcrud-layout-spa > .djcrud-sidebar")[1]
    assert "height: 100%" in css.split(".djcrud-layout-spa {")[1]
    assert ".djcrud-layout-immersive" not in css


@pytest.mark.django_db
def test_standard_layout_still_renders_navbar(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("site:item:list"))

    assert response.status_code == 200
    assert b'<nav class="navbar"' in response.content
    assert b"djcrud-layout-spa" not in response.content


class _MainShellView(ViewMixin):
    unpoly_target = None


class _BodyShellView(ViewMixin):
    unpoly_target = "body"


class _SpaTemplateView(ViewMixin):
    unpoly_target = "body"
    template_name = "djcrud/base_spa.html"
    media = Media(media=SpaShellMedia)
    mount_element = '<div id="app"></div>'


def test_uses_spa_shell_detects_template_suffix():
    assert uses_spa_shell(_SpaTemplateView()) is True
    assert uses_spa_shell(_MainShellView()) is False


def test_apply_unpoly_target_sets_headers():
    response = HttpResponse("ok")

    apply_unpoly_target(response, "body")

    assert response["X-Up-Target"] == "body"
    assert response["Vary"] == "X-Up-Target"


def test_apply_unpoly_target_appends_vary():
    response = HttpResponse("ok")
    response["Vary"] = "Accept-Language"

    apply_unpoly_target(response, "body")

    assert response["Vary"] == "Accept-Language, X-Up-Target"


class _BodyTargetTemplateView(TemplateViewMixin, generic.TemplateView):
    unpoly_target = "body"
    template_name = "djcrud/test_spa.html"
    mount_element = '<div id="app"></div>'

    @property
    def media(self):
        return Media(media=SpaShellMedia)


def test_unpoly_target_response_header(rf):
    request = rf.get("/editor/")
    view = _BodyTargetTemplateView()
    view.setup(request)
    view.request = request

    response = view.render_to_response({"view": view})

    assert response["X-Up-Target"] == "body"
    assert "X-Up-Target" in response["Vary"]


def test_unpoly_link_attributes_leaves_body_target(rf):
    request = rf.get("/editor/")
    source = _BodyShellView()
    source.request = request
    request._djcrud_view = source
    target = _MainShellView()
    target.request = request

    assert (
        source.unpoly_link_attributes(target, "navigation") == FULL_PAGE_LINK_ATTRIBUTES
    )


def test_unpoly_link_attributes_enters_body_target_uses_plain_link(rf):
    request = rf.get("/items/")
    source = _MainShellView()
    source.request = request
    request._djcrud_view = source
    target = _BodyShellView()
    target.request = request

    assert (
        source.unpoly_link_attributes(target, "navigation") == FULL_PAGE_LINK_ATTRIBUTES
    )


def test_unpoly_link_attributes_spa_template_uses_plain_link(rf):
    request = rf.get("/spa/")
    source = _SpaTemplateView()
    source.request = request
    request._djcrud_view = source
    target = _MainShellView()
    target.request = request

    assert (
        source.unpoly_link_attributes(target, "navigation") == FULL_PAGE_LINK_ATTRIBUTES
    )


def test_unpoly_link_attributes_same_body_target_keeps_unpoly(rf):
    request = rf.get("/editor/1/")
    source = _BodyShellView()
    source.request = request
    request._djcrud_view = source
    target = _BodyShellView()
    target.request = request

    assert source.unpoly_link_attributes(target, "navigation") == {
        "up-follow": True,
        "up-target": "[up-main]",
    }


def test_unpoly_attributes_filter_disables_unpoly_when_entering_body_target(rf):
    request = rf.get("/items/")
    source = _MainShellView()
    source.request = request
    request._djcrud_view = source
    target = _BodyShellView()
    target.request = request

    assert unpoly_attributes(target, "table_actions") == FULL_PAGE_LINK_ATTRIBUTES


def test_unpoly_attributes_filter_disables_unpoly_when_leaving_body_target(rf):
    request = rf.get("/editor/")
    source = _BodyShellView()
    source.request = request
    request._djcrud_view = source

    item_router = djcrud.site.routes["item"]
    list_route = item_router.routes["list"]
    target = type(list_route)(request=request)

    assert unpoly_attributes(target, "navigation") == FULL_PAGE_LINK_ATTRIBUTES


@pytest.mark.django_db
def test_spa_shell_navigation_links_full_reload(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("site:spa"))
    content = response.content.decode()
    item_link = content.split('href="/item/"', 1)[1].split("</a>", 1)[0]

    assert 'up-follow="false"' in item_link


def test_unpoly_link_attributes_from_spa_shell_always_plain_link(rf):
    request = rf.get("/spa/")
    source = _SpaTemplateView()
    source.request = request
    request._djcrud_view = source
    target = _SpaTemplateView()
    target.request = request

    assert (
        source.unpoly_link_attributes(target, "navigation") == FULL_PAGE_LINK_ATTRIBUTES
    )
