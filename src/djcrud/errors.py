from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

DEFAULT_ERROR_PAGES = {
    400: (
        _("Bad request"),
        _("The request could not be understood by the server."),
    ),
    403: (
        _("Forbidden"),
        _("You don't have permission to view or edit anything."),
    ),
    404: (
        _("Page not found"),
        _("We're sorry, but the requested page could not be found."),
    ),
    500: (
        _("Server error"),
        _(
            "There's been an error. It's been reported to the site "
            "administrators via email and should be fixed shortly. "
            "Thanks for your patience."
        ),
    ),
}


def layout_view_for_request(request):
    import djcrud
    from .views.template import TemplateView

    if not hasattr(djcrud.site, "registry"):
        djcrud.site.ensure_built()

    class LayoutView(TemplateView):
        def has_permission(self):
            return True

    view_class = LayoutView.clone(router=djcrud.site)
    view = view_class()
    view.request = request
    view.kwargs = {}
    view.args = ()
    return view


def error_response(request, status, view=None, title=None, message=None):
    view = view or layout_view_for_request(request)
    default_title, default_message = DEFAULT_ERROR_PAGES[status]
    context = {
        "view": view,
        "error_status": status,
        "error_title": title or default_title,
        "error_message": message or default_message,
    }
    return TemplateResponse(
        request,
        [
            f"djcrud/{status}.html",
            "djcrud/error.html",
            f"{status}.html",
        ],
        context,
        status=status,
    )


def bad_request_response(request, view=None, title=None, message=None):
    return error_response(request, 400, view=view, title=title, message=message)


def forbidden_response(request, view=None, title=None, message=None):
    return error_response(request, 403, view=view, title=title, message=message)


def not_found_response(request, view=None, title=None, message=None):
    return error_response(request, 404, view=view, title=title, message=message)


def server_error_response(request, view=None, title=None, message=None):
    return error_response(request, 500, view=view, title=title, message=message)
