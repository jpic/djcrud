"""Screenshot helpers for djcrud_dal_topbar browser tests."""

from pathlib import Path

TOPBAR_SCREENSHOTS_DIR = Path(__file__).resolve().parent / "screenshots" / "topbar"


def prepare_browser(browser, width=1280, height=900):
    browser.driver.set_window_size(width, height)


def capture(browser, name):
    """Save a PNG to ``tests/screenshots/topbar/<name>.png``."""
    TOPBAR_SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    path = TOPBAR_SCREENSHOTS_DIR / f"{name}.png"
    browser.driver.save_screenshot(str(path))
    return path
