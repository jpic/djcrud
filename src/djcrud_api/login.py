import json
from datetime import timedelta

from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import Token

API_LOGIN_TOKEN_LIFETIME = timedelta(hours=1)
API_LOGIN_TOKEN_NAME = "API login"


def uses_drf_login():
    try:
        import rest_framework  # noqa: F401
    except ImportError:
        return False
    return True


def login_with_credentials(request):
    """Exchange username/password for a short-lived Bearer token.

    Returns ``(body, status_code)``. On success *body* contains ``token``,
    ``expires``, and ``prefix``.
    """
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {"detail": _("Invalid JSON")}, 400

    username = data.get("username", "")
    password = data.get("password", "")
    user = authenticate(
        request,
        username=username,
        password=password,
    )
    if user is None:
        return {"detail": _("Invalid username or password")}, 401

    expires = timezone.now() + API_LOGIN_TOKEN_LIFETIME
    token, raw_key = Token.generate(
        user=user,
        name=API_LOGIN_TOKEN_NAME,
        expires=expires,
    )
    return {
        "token": raw_key,
        "expires": expires.isoformat(),
        "prefix": token.prefix,
    }, 200