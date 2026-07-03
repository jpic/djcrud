"""Helpers for capturing browser screenshots used in Sphinx docs."""

from pathlib import Path

DOCS_SCREENSHOTS_DIR = (
    Path(__file__).resolve().parents[1] / "docs" / "_static" / "screenshots"
)

# PNGs referenced from Sphinx docs (tutorial + install + philosophy).
DOC_SCREENSHOTS = (
    "item-list",
    "success-toast",
    "bulk-delete-modal",
    "article-list",
    "article-detail",
    "duplicate-action-menu",
    "duplicate-action-success",
    "publish-action-menu",
    "publish-action-success",
    "list-action-bar",
    "set-category-modal",
    "site-search",
    "api-swagger-ui",
)


def prepare_browser(browser, width=1280, height=900):
    """Set a consistent viewport before capturing."""
    browser.driver.set_window_size(width, height)


def capture(browser, name):
    """Save a PNG to ``docs/_static/screenshots/<name>.png``."""
    DOCS_SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    path = DOCS_SCREENSHOTS_DIR / f"{name}.png"
    browser.driver.save_screenshot(str(path))
    return path


def assert_all_captured():
    """Verify every documented screenshot exists and is non-empty."""
    missing = []
    for name in DOC_SCREENSHOTS:
        path = DOCS_SCREENSHOTS_DIR / f"{name}.png"
        if not path.is_file() or path.stat().st_size == 0:
            missing.append(name)
    assert not missing, f"Missing or empty doc screenshots: {missing}"
