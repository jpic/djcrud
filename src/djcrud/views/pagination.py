import functools

from django.core.paginator import InvalidPage
from django.http import Http404
from django.utils.translation import gettext as _


class PaginationMixin:
    """Page size and page navigation for list views.

    Attributes:
        paginate_by (int | None): Default rows per page. ``None`` disables
            pagination.
        per_page_options (str): Comma-separated allowed page sizes for the
            per-page selector.
        page_kwarg (str): GET parameter for the current page number.
        per_page_kwarg (str): GET parameter for the selected page size.
        pagination_target (str): Unpoly ``up-target`` for pagination controls.
    """

    paginate_by = 25
    per_page_options = "10,25,50,100"
    page_kwarg = "page"
    per_page_kwarg = "per_page"
    pagination_target = "[up-list]"

    def get_paginate_by(self, queryset=None):
        """Rows per page from GET or :attr:`paginate_by` default."""
        if self.paginate_by is None:
            return None
        return self.resolved_per_page

    @functools.cached_property
    def resolved_per_page(self):
        """Validated page size from GET or :attr:`paginate_by`."""
        allowed = {int(x) for x in self.per_page_options.split(",")}
        raw = self.request.GET.get(self.per_page_kwarg)
        if raw is not None and raw.isdigit():
            value = int(raw)
            if value in allowed:
                return value
        return self.paginate_by

    @property
    def page(self):
        """Current :class:`~django.core.paginator.Page` object, if paginated."""
        page_obj = getattr(self, "page_obj", None)
        if page_obj is not None:
            return page_obj
        return None

    @property
    def paginator(self):
        """Paginator for the current list queryset."""
        page = self.page
        if page is not None:
            return page.paginator
        return getattr(self, "_paginator", None)

    def pagination_url(self, page_number):
        """URL for *page_number* preserving other GET parameters."""
        return self.querystring(**{self.page_kwarg: str(page_number)})

    @property
    def pagination_form_attributes(self):
        """HTML attributes for pagination control forms."""
        return {
            "up-submit": True,
            "up-target": self.pagination_target,
            "up-history": True,
            "up-autosubmit": True,
        }

    def pagination_hidden_fields(self, *exclude):
        excluded = set(exclude)
        for key, values in self.request.GET.lists():
            if key in excluded:
                continue
            for value in values:
                yield key, value

    @property
    def per_page_option_list(self):
        """Allowed page sizes from :attr:`per_page_options`."""
        return self.per_page_options.split(",")

    @property
    def per_page_form_hidden_fields(self):
        return list(
            self.pagination_hidden_fields(
                self.per_page_kwarg,
                self.page_kwarg,
            )
        )

    @property
    def page_form_hidden_fields(self):
        return list(self.pagination_hidden_fields(self.page_kwarg))

    def clamp_page_number(self, page_number, paginator):
        num_pages = paginator.num_pages
        if num_pages < 1:
            return 1
        return min(max(page_number, 1), num_pages)

    def get_requested_page_number(self, paginator):
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        try:
            return int(page)
        except (TypeError, ValueError):
            if page == "last":
                return paginator.num_pages or 1
            raise Http404(
                _("Page is not “last”, nor can it be converted to an int."),
            )

    def paginate_queryset(self, queryset, page_size):
        paginator = self.get_paginator(
            queryset,
            page_size,
            orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty(),
        )
        page_number = self.clamp_page_number(
            self.get_requested_page_number(paginator),
            paginator,
        )
        try:
            page = paginator.page(page_number)
        except InvalidPage:
            page_number = self.clamp_page_number(page_number, paginator)
            page = paginator.page(page_number)
        self.page_obj = page
        self._paginator = paginator
        return paginator, page, page.object_list, page.has_other_pages()
