from .errors import (
    bad_request_response,
    forbidden_response,
    layout_view_for_request,
    not_found_response,
    server_error_response,
)


def handler400(request, exception=None):
    return bad_request_response(request, view=layout_view_for_request(request))


def handler403(request, exception=None):
    return forbidden_response(request, view=layout_view_for_request(request))


def handler404(request, exception=None):
    return not_found_response(request, view=layout_view_for_request(request))


def handler500(request):
    return server_error_response(request, view=layout_view_for_request(request))
