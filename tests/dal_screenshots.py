"""Screenshot helpers for DAL browser tests."""

from pathlib import Path

DAL_SCREENSHOTS_DIR = Path(__file__).resolve().parent / "screenshots" / "dal"


def prepare_browser(browser, width=1280, height=900):
    browser.driver.set_window_size(width, height)


def capture(browser, name):
    """Save a PNG to ``tests/screenshots/dal/<name>.png``."""
    DAL_SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    path = DAL_SCREENSHOTS_DIR / f"{name}.png"
    browser.driver.save_screenshot(str(path))
    return path
