from django.http import HttpResponseRedirect
from django.urls import reverse

# Disable Unpoly on links that must reload the full document (menus, session).
FULL_PAGE_LINK_ATTRIBUTES = {"up-follow": False}


def apply_unpoly_target(response, target):
    """Set Unpoly response headers so fragment requests update *target*."""
    if not target:
        return response
    response["X-Up-Target"] = target
    vary = response.get("Vary", "")
    if vary:
        if "X-Up-Target" not in vary:
            response["Vary"] = f"{vary}, X-Up-Target"
    else:
        response["Vary"] = "X-Up-Target"
    return response


def home_url(request):
    import djcrud

    if not hasattr(djcrud.site, "registry"):
        djcrud.site.build()
    home_route = djcrud.site.find_route("home")
    if home_route is not None:
        return type(home_route)(request=request).url
    return reverse("site:home")


def full_page_redirect(url):
    """Redirect after an identity-changing action (browser follows natively)."""
    return HttpResponseRedirect(url)


def full_page_redirect_home(request):
    return full_page_redirect(home_url(request))
