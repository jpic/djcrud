"""Bearer token middleware for djcrud_api.

``BearerCsrfMiddleware`` must run **before**
:class:`django.middleware.csrf.CsrfViewMiddleware`.
``BearerUserMiddleware`` must run **after**
:class:`django.contrib.auth.middleware.AuthenticationMiddleware`.
"""

from .models import Token


def parse_bearer_header(request):
    """Return the Bearer token from ``Authorization``, or ``None``."""
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if not header.startswith("Bearer "):
        return None
    return header[7:].strip() or None


def lookup_token(raw_key):
    """Validate *raw_key* and return the :class:`Token`, or ``None``."""
    return Token.authenticate(raw_key)


class BearerCsrfMiddleware:
    """Skip CSRF when a valid Bearer token is present."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        raw_key = parse_bearer_header(request)
        if raw_key:
            token = lookup_token(raw_key)
            if token is not None:
                request._djcrud_bearer_token = token
                request._dont_enforce_csrf_checks = True
        return self.get_response(request)


class BearerUserMiddleware:
    """Authenticate the request from a stashed Bearer token."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = getattr(request, "_djcrud_bearer_token", None)
        if token is not None:
            request.user = token.user
            request.auth = token
            token.touch_last_used()
        return self.get_response(request)
