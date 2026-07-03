export const FOCUSABLE_SELECTOR = [
    'input:not([type=hidden]):not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    'autocomplete-select-input input:not([disabled])',
].join(', ');

export function isFormVisible(form) {
    if (!form) {
        return false;
    }

    let element = form;
    while (element) {
        if (element.classList?.contains('is-hidden')) {
            return false;
        }
        const style = getComputedStyle(element);
        if (style.display === 'none' || style.visibility === 'hidden') {
            return false;
        }
        element = element.parentElement;
    }

    return true;
}

export function focusFirstInput(form) {
    if (!isFormVisible(form)) {
        return;
    }

    const field = form.querySelector(FOCUSABLE_SELECTOR);
    field?.focus({ preventScroll: true });
}

export function registerFormFocus(up) {
    up.compiler('form[method="post"], form.djcrud-filter-form', (form) => {
        queueMicrotask(() => focusFirstInput(form));
    });
}

if (typeof window !== 'undefined' && window.up) {
    registerFormFocus(window.up);
}