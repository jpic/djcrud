"""
Beautiful Django Management Command: show_urls

A clean, colorful management command to display all URL patterns
using only Django's built-in ANSI color support (no external dependencies).

Installation:
    1. Put this file in one of your Django apps:
       yourapp/management/commands/show_urls.py

    2. Make sure the __init__.py files exist:
       yourapp/management/__init__.py
       yourapp/management/commands/__init__.py

    3. Add 'yourapp' to INSTALLED_APPS (if not already)

Usage:
    python manage.py show_urls
    python manage.py show_urls --no-admin
    python manage.py show_urls --named-only
    python manage.py show_urls --search api
"""

import shutil
from django.core.management.base import BaseCommand
from django.urls import get_resolver, URLPattern, URLResolver
from django.utils.termcolors import make_style

# ====================== CUSTOM ANSI STYLES ======================

URL_STYLE = make_style(fg="cyan", opts=("bold",))
NAME_STYLE = make_style(fg="yellow", opts=("bold",))
VIEW_STYLE = make_style(fg="magenta")
NS_STYLE = make_style(fg="green")
HEADER_STYLE = make_style(fg="white", opts=("bold",))
SEPARATOR_STYLE = make_style(fg="blue")
SUCCESS_STYLE = make_style(fg="green", opts=("bold",))
DIM_STYLE = make_style(fg="blue")


class Command(BaseCommand):
    help = "Display all URL patterns in a beautiful colored format"

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-admin",
            action="store_true",
            help="Exclude admin site URLs",
        )
        parser.add_argument(
            "--named-only",
            action="store_true",
            help="Show only named URL patterns",
        )
        parser.add_argument(
            "--search",
            "-s",
            type=str,
            metavar="TERM",
            help="Filter results containing TERM (URL, name or view)",
        )

    def handle(self, *args, **options):
        exclude_admin = options["no_admin"]
        named_only = options["named_only"]
        search_term = options.get("search")

        resolver = get_resolver()
        urls = self._collect_urls(resolver)
        urls = sorted(urls, key=lambda x: x["url"].lower())

        if exclude_admin:
            urls = [u for u in urls if not u["url"].startswith(("/admin/", "admin/"))]

        if named_only:
            urls = [u for u in urls if u.get("name")]

        if search_term:
            term = search_term.lower()
            urls = [
                u
                for u in urls
                if term in u["url"].lower()
                or (u.get("name") and term in u["name"].lower())
                or (u.get("view") and term in u["view"].lower())
            ]

        self._print_beautiful_table(urls)

        self.stdout.write("")
        self.stdout.write(SUCCESS_STYLE(f"✨  Found {len(urls)} URL pattern(s)"))

    def _collect_urls(self, resolver, prefix="", namespace=None):
        collected = []
        for pattern in resolver.url_patterns:
            if isinstance(pattern, URLResolver):
                new_prefix = prefix + str(pattern.pattern)
                new_ns = pattern.namespace or namespace
                collected.extend(self._collect_urls(pattern, new_prefix, new_ns))
            elif isinstance(pattern, URLPattern):
                collected.append(
                    {
                        "url": prefix + str(pattern.pattern),
                        "name": pattern.name or "",
                        "view": self._get_view_representation(pattern.callback),
                        "namespace": namespace or "",
                    }
                )
        return collected

    def _get_view_representation(self, callback):
        if hasattr(callback, "view_class"):
            cls = callback.view_class
            return f"{cls.__module__}.{cls.__name__}.as_view()"

        if hasattr(callback, "__name__"):
            module = getattr(callback, "__module__", "")
            if module and module not in ("__main__", "django.views.generic.base"):
                return f"{module}.{callback.__name__}"
            return callback.__name__

        return str(callback)[:70]

    # ====================== BEAUTIFUL ANSI TABLE ======================

    def _print_beautiful_table(self, urls):
        if not urls:
            self.stdout.write(DIM_STYLE("No matching URLs found."))
            return

        # Get terminal size for responsive layout
        term_width = shutil.get_terminal_size(fallback=(140, 24)).columns
        available = max(term_width - 8, 80)  # leave some margin

        # Calculate natural max widths from data
        max_url = max(len(u["url"]) for u in urls)
        max_name = max(len(u.get("name", "")) for u in urls) or 5
        max_view = max(len(u["view"]) for u in urls)
        max_ns = max(len(u.get("namespace", "")) for u in urls) or 5

        # Distribute available width nicely (URL and View get more space)
        url_width = min(max_url, int(available * 0.32))
        name_width = min(max_name, int(available * 0.22))
        view_width = min(max_view, int(available * 0.36))
        ns_width = min(max_ns, int(available * 0.10))

        # Ensure minimum usable widths
        url_width = max(url_width, 25)
        name_width = max(name_width, 18)
        view_width = max(view_width, 30)
        ns_width = max(ns_width, 8)

        # Column headers
        header = (
            f"  {HEADER_STYLE('URL Pattern'.ljust(url_width))}  "
            f"{HEADER_STYLE('Name'.ljust(name_width))}  "
            f"{HEADER_STYLE('View'.ljust(view_width))}  "
            f"{HEADER_STYLE('NS'.ljust(ns_width))}"
        )
        self.stdout.write(header)
        self.stdout.write(
            SEPARATOR_STYLE(
                "  " + "─" * (url_width + name_width + view_width + ns_width + 8)
            )
        )

        for u in urls:
            # URL
            url = u["url"]
            if len(url) > url_width:
                url = url[: url_width - 1] + "…"
            colored_url = URL_STYLE(url.ljust(url_width))

            # Name with full namespace (site:usermodel:viewname)
            if u["namespace"] and u["name"]:
                name_display = f"{u['namespace']}:{u['name']}"
            else:
                name_display = u["name"] or "-"

            if len(name_display) > name_width:
                name_display = name_display[: name_width - 1] + "…"

            colored_name = (
                NAME_STYLE(name_display.ljust(name_width))
                if u["name"]
                else DIM_STYLE(name_display.ljust(name_width))
            )

            # View
            view = u["view"]
            if len(view) > view_width:
                view = view[: view_width - 1] + "…"
            colored_view = VIEW_STYLE(view.ljust(view_width))

            # Namespace
            ns_display = u["namespace"] or "-"
            if len(ns_display) > ns_width:
                ns_display = ns_display[: ns_width - 1] + "…"

            colored_ns = (
                NS_STYLE(ns_display.ljust(ns_width))
                if u["namespace"]
                else DIM_STYLE(ns_display.ljust(ns_width))
            )

            line = f"  {colored_url}  {colored_name}  {colored_view}  {colored_ns}"
            self.stdout.write(line)

        # Bottom separator
        self.stdout.write(
            SEPARATOR_STYLE(
                "  " + "─" * (url_width + name_width + view_width + ns_width + 8)
            )
        )


if __name__ == "__main__":
    print("Run via: python manage.py show_urls")
