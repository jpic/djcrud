import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

import djcrud
from djcrud.redirect import full_page_redirect
from djcrud.templatetags.djcrud import unpoly_attributes

User = get_user_model()


@pytest.fixture
def target_user(db):
    return User.objects.create_user(
        username="foo",
        email="foo@example.com",
        password="Download@123",
    )


@pytest.fixture
def su_user(db):
    return User.objects.get(username="su")


@pytest.fixture
def suuser(db):
    return User.objects.create_superuser(
        username="suuser",
        password="123",
        email="",
    )


def test_password_reverse(target_user):
    assert reverse("site:auth:user:password", args=[target_user.pk]) == (
        f"/auth/user/{target_user.pk}/password/"
    )


def test_become_reverse():
    assert reverse("site:auth:su") == "/auth/su/"


@pytest.mark.django_db
def test_user_password_get(admin_client, target_user):
    url = reverse("site:auth:user:password", args=[target_user.pk])
    response = admin_client.get(url)

    assert response.status_code == 200
    assert b"id_new_password2" in response.content


@pytest.mark.django_db
def test_user_password_post(admin_client, target_user):
    url = reverse("site:auth:user:password", args=[target_user.pk])
    response = admin_client.post(
        url,
        {
            "new_password1": "Download123",
            "new_password2": "Download123",
        },
    )

    assert response.status_code == 302
    assert response["Location"] == reverse(
        "site:auth:user:detail",
        args=[target_user.pk],
    )
    target_user.refresh_from_db()
    assert target_user.check_password("Download123")


@pytest.mark.django_db
def test_user_password_self(admin_client, admin_user):
    url = reverse("site:auth:user:password", args=[admin_user.pk])
    response = admin_client.get(url)

    assert response.status_code == 200
    assert b"id_old_password" in response.content


@pytest.mark.django_db
def test_become_user(admin_client, admin_user, su_user, suuser, target_user):
    assert admin_client.session.get("become_user") is None

    response = admin_client.get(
        reverse("site:auth:user:su", args=[admin_user.pk]),
        follow=True,
    )
    assert response.status_code == 200
    assert admin_client.session.get("become_user") == admin_user.pk

    response = admin_client.get(
        reverse("site:auth:user:su", args=[suuser.pk]),
        follow=True,
    )
    assert response.status_code == 200
    assert admin_client.session.get("become_user") == admin_user.pk

    response = admin_client.get(reverse("site:auth:su"), follow=True)
    assert response.status_code == 200
    assert admin_client.session.get("become_user") is None

    response = admin_client.get(
        reverse("site:auth:user:su", args=[target_user.pk]),
    )
    assert response.status_code == 302
    assert response.url == reverse("site:home")


@pytest.mark.django_db
def test_become_shows_in_menus_while_impersonating(rf, admin_user, su_user):
    djcrud.site.build()
    site = djcrud.site

    request = rf.get("/")
    request.user = admin_user
    request.session = {}

    def has_become(views):
        return any(type(view).__name__ == "Become" for view in views)

    assert not has_become(site.get_tagged_views("topbar", request=request))
    assert not has_become(site.get_tagged_views("navigation", request=request))

    request.session["become_user"] = admin_user.pk
    request.session["become_user_realname"] = str(admin_user)
    assert has_become(site.get_tagged_views("topbar", request=request))
    assert has_become(site.get_tagged_views("navigation", request=request))


@pytest.mark.django_db
def test_become_views_use_full_page_navigation(rf, admin_user, target_user):
    djcrud.site.build()
    user_router = djcrud.site.routes["auth"].routes["user"]
    request = rf.get("/")
    request.user = admin_user
    request.session = {
        "become_user": admin_user.pk,
        "become_user_realname": str(admin_user),
    }

    become = type(djcrud.site.routes["auth"].routes["su"])(request=request)
    become_user = type(user_router.routes["su"])(
        request=request,
        object=target_user,
        pk=target_user.pk,
    )

    from djcrud.redirect import FULL_PAGE_LINK_ATTRIBUTES

    assert unpoly_attributes(become, "topbar") == FULL_PAGE_LINK_ATTRIBUTES
    assert unpoly_attributes(become_user, "object_menu") == FULL_PAGE_LINK_ATTRIBUTES


@pytest.mark.django_db
def test_become_redirects_set_full_page_target(admin_client, admin_user, target_user):
    response = admin_client.get(
        reverse("site:auth:user:su", args=[target_user.pk]),
    )
    assert response.status_code == 302
    assert response.url == reverse("site:home")

    response = admin_client.get(reverse("site:auth:su"))
    assert response.status_code == 302


def test_full_page_redirect():
    response = full_page_redirect("/auth/user/")
    assert response.status_code == 302
    assert response.url == "/auth/user/"


@pytest.mark.django_db
def test_login_form_inherits_unpoly_modal_attributes(client):
    client.logout()
    response = client.get(reverse("site:auth:login"))
    content = response.content.decode()
    assert 'up-target="body"' in content
    assert 'up-history="false"' in content
    assert "up-submit" in content
    assert 'up-layer="any"' in content
    assert 'up-accept-location="*"' in content
    assert 'up-on-accepted="up.visit(response.url)"' in content


@pytest.mark.django_db
def test_logout_link_opens_in_modal(client, admin_user):
    client.force_login(admin_user)
    response = client.get(reverse("site:home"))
    content = response.content.decode()
    logout_url = reverse("site:auth:logout")
    assert logout_url in content
    assert 'up-layer="new modal"' in content


@pytest.mark.django_db
def test_logout_form_uses_full_page_submit(client, admin_user):
    client.force_login(admin_user)
    response = client.get(reverse("site:auth:logout"))
    content = response.content.decode()
    assert 'up-submit="false"' in content
    assert 'up-target="body"' not in content


@pytest.mark.django_db
def test_logout_post_redirects_home(client, admin_user):
    client.force_login(admin_user)
    response = client.post(reverse("site:auth:logout"), {"next": "/auth/user/"})
    assert response.status_code == 302
    assert response.url == reverse("site:home")


@pytest.mark.django_db
def test_become_user_link_disables_unpoly(client, admin_user, target_user):
    client.force_login(admin_user)
    response = client.get(reverse("site:auth:user:list"))
    su_url = reverse("site:auth:user:su", args=[target_user.pk])
    assert su_url in response.content.decode()
    assert (
        f'href="{su_url}"' in response.content.decode()
        or su_url in response.content.decode()
    )
    assert 'up-follow="false"' in response.content.decode()


@pytest.mark.django_db
def test_actions_column_aligns_right(client, admin_user):
    client.force_login(admin_user)
    response = client.get(reverse("site:auth:user:list"))
    content = response.content.decode()
    assert "Actions" in content
    assert "has-text-right" in content
    assert content.index("has-text-right") < content.index("Actions")


@pytest.mark.django_db
def test_become_user_object_menu(rf, admin_user, target_user):
    djcrud.site.build()
    user_router = djcrud.site.routes["auth"].routes["user"]

    request = rf.get("/")
    request.user = admin_user
    menu = user_router.get_tagged_views(
        "object",
        request=request,
        object=target_user,
    )
    codenames = {view.codename for view in menu}
    assert "su" in codenames
