import time

INPUT_SELECTOR = "autocomplete-select-input input"
DROPDOWN_SELECTOR = ".autocomplete-light-box"
OPTION_SELECTOR = ".autocomplete-light-box [data-value]:not([data-create])"


def scroll_into_view(browser, css):
    """Scroll a field into view before Selenium interacts with it."""
    browser.execute_script(
        """
        const el = document.querySelector(arguments[0]);
        el?.scrollIntoView({block: 'center', inline: 'nearest'});
        """,
        css,
    )


def ensure_navbar_menu_visible(browser):
    """Bulma may hide navbar-menu in headless viewports; force it open for tests."""
    browser.execute_script(
        """
        const menu = document.querySelector('.navbar-menu');
        if (menu) {
            menu.classList.add('is-active');
        }
        """,
    )


def wait_input_interactable(browser, input_css, timeout=15):
    deadline = time.time() + timeout
    state = None
    while time.time() < deadline:
        state = browser.execute_script(
            """
            const el = document.querySelector(arguments[0]);
            if (!el) {
                return null;
            }
            const rect = el.getBoundingClientRect();
            const style = getComputedStyle(el);
            return {
                width: rect.width,
                height: rect.height,
                display: style.display,
                visibility: style.visibility,
                disabled: el.disabled,
            };
            """,
            input_css,
        )
        if (
            state
            and state["width"] > 0
            and state["height"] > 0
            and state["display"] != "none"
            and state["visibility"] != "hidden"
            and not state["disabled"]
        ):
            return
        time.sleep(0.15)
    raise AssertionError(
        f"Input not interactable: {input_css!r} (last state: {state!r})",
    )


def wait_alight_ready(browser, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if browser.evaluate_script(
                "customElements.get('autocomplete-select') !== undefined"
                " && customElements.get('autocomplete-light') !== undefined"
                " && !document.querySelector("
                "'autocomplete-select-input:not([data-bound]),"
                " autocomplete-select:not([data-bound]),"
                " autocomplete-light:not([data-bound])')"
            ):
                return
        except Exception:
            pass
        time.sleep(0.15)
    raise AssertionError("autocomplete-select was not ready")


def open_autocomplete(browser, input_css=INPUT_SELECTOR):
    scroll_into_view(browser, input_css)
    browser.execute_script(
        """
        const el = document.querySelector(arguments[0]);
        if (!el) {
            throw new Error(`Missing autocomplete input: ${arguments[0]}`);
        }
        el.scrollIntoView({block: 'center', inline: 'nearest'});
        if (document.activeElement === el) {
            el.blur();
        }
        el.focus();
        el.click();
        """,
        input_css,
    )


def type_autocomplete_query(browser, text, *, input_css):
    """Type into an autocomplete field without choosing a result."""
    wait_alight_ready(browser)
    open_autocomplete(browser, input_css)
    browser.execute_script(
        """
        const el = document.querySelector(arguments[0]);
        if (!el) {
            throw new Error(`Missing autocomplete input: ${arguments[0]}`);
        }
        el.focus();
        el.value = '';
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.value = arguments[1];
        el.dispatchEvent(new Event('input', {bubbles: true}));
        """,
        input_css,
        text,
    )


def type_and_select(
    browser, text, *, container_css="autocomplete-select", input_css=None
):
    if input_css is None:
        input_css = f"{container_css} {INPUT_SELECTOR}"
    wait_alight_ready(browser)
    type_autocomplete_query(browser, text, input_css=input_css)

    deadline = time.time() + 5
    while time.time() < deadline:
        selected = browser.execute_script(
            """
            for (const option of document.querySelectorAll(arguments[0])) {
                if (option.dataset.create !== undefined) {
                    continue;
                }
                if (option.textContent.includes(arguments[1])) {
                    option.dispatchEvent(new MouseEvent('mousedown', {
                        bubbles: true,
                        cancelable: true,
                    }));
                    return true;
                }
            }
            return false;
            """,
            OPTION_SELECTOR,
            text,
        )
        if selected:
            return
        time.sleep(0.15)
    raise AssertionError(f"No autocomplete option matching {text!r}")


def selected_labels(browser, container_css="autocomplete-select"):
    selector = f"{container_css} [slot=deck] [data-value]"
    return [el.text.replace("×", "").strip() for el in browser.find_by_css(selector)]
