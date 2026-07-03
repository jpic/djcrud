#!/usr/bin/env python3
import os
import sys
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djcrud_example.settings")
os.environ.setdefault("DEBUG", "1")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "djcrud_example"))

django.setup()

project = "djcrud"
copyright = "2026, James Pic & Contributors"
author = "James Pic & Contributors"

try:
    from importlib.metadata import version

    release = version("djcrud")
except Exception:
    release = "0.0.0"
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
pygments_style = "sphinx"
todo_include_todos = False

html_theme = "furo"
html_static_path = ["_static"]
html_baseurl = "/djcrud/"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": ("https://docs.djangoproject.com/en/stable/", "https://docs.djangoproject.com/en/stable/_objects/"),
}

napoleon_google_docstring = True
napoleon_include_init_with_doc = False
napoleon_attr_annotations = True
autoclass_content = "both"
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
    "member-order": "bysource",
}

htmlhelp_basename = "djcruddoc"
latex_documents = [
    (master_doc, "djcrud.tex", "djcrud Documentation", author, "manual"),
]
man_pages = [(master_doc, "djcrud", "djcrud Documentation", [author], 1)]
texinfo_documents = [
    (
        master_doc,
        "djcrud",
        "djcrud Documentation",
        author,
        "djcrud",
        "Django CRUD utilities.",
        "Miscellaneous",
    ),
]

epub_title = project
epub_author = author
epub_publisher = author
epub_copyright = copyright
epub_exclude_files = ["search.html"]