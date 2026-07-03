"""Frontend asset helpers (primarily Vite manifest resolution for hashed filenames).

SPAView subclasses declare their client bundles using Django's forms.Media /
Script objects. To avoid stale browser caches after a frontend rebuild, the
served filenames must contain content hashes while developer code continues to
refer to stable logical paths.

This module provides ``vite_asset()`` which rewrites a logical path such as
``"spa_example/js/app.js"`` into the hashed filename recorded in the adjacent
Vite manifest (``.vite/manifest.json`` or ``manifest.json``) produced by
``npm run build``.

The helper falls back to the original path when no manifest is present so the
same declaration works in both "just built" and "pre-build" states.

Example::

    from django.forms.widgets import Script
    from djcrud.static import vite_asset
    from djcrud.views.spa import SPAView

    class MySPA(SPAView):
        class Media(SPAView.Media):
            js = SPAView.Media.js + (
                Script(vite_asset("myspa/js/app.js"), type="module"),
            )
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from django.contrib.staticfiles import finders

VITE_MANIFEST_CANDIDATES = (".vite/manifest.json", "manifest.json")


@lru_cache(maxsize=32)
def _load_vite_manifest(static_subdir: str) -> dict | None:
    """Return the parsed Vite manifest dict for a static sub-directory, or None."""
    for candidate in VITE_MANIFEST_CANDIDATES:
        rel = f"{static_subdir}/{candidate}"
        abs_path = finders.find(rel)
        if abs_path:
            try:
                with open(abs_path, encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                return None
    return None


def vite_asset(path: str) -> str:
    """Return a cache-busting (hashed) static path for a Vite-built entry.

    *path* is the stable name you would use without hashing, e.g.
    ``"spa_example/js/app.js"``. The directory portion is used to locate a
    co-located Vite manifest; the filename is then replaced by the hashed
    version recorded in the manifest.

    Falls back to returning *path* unchanged when:
    - no manifest is present under that directory, or
    - no matching entry is found.

    Absolute URLs, protocol-relative, and root-absolute paths are returned
    as-is.
    """
    if not path:
        return path
    if path.startswith(("http://", "https://", "/")):
        return path

    p = Path(path)
    directory = str(p.parent)
    wanted_name = p.name

    manifest = _load_vite_manifest(directory)
    if not manifest:
        return path

    # Match by stripping the typical Vite hash segment (.<hex> or -<hex>)
    for entry in manifest.values():
        if not isinstance(entry, dict):
            continue
        file = entry.get("file")
        if not isinstance(file, str):
            continue
        unhashed = re.sub(r"[-.][0-9a-fA-F]{5,}(?=\.[^.]+$)", "", file)
        if unhashed == wanted_name or file == wanted_name:
            return str(p.parent / file)

    # Common single-entry SPA fallback
    for entry in manifest.values():
        if isinstance(entry, dict) and entry.get("isEntry"):
            file = entry.get("file")
            if isinstance(file, str):
                return str(p.parent / Path(file).name)

    return path
