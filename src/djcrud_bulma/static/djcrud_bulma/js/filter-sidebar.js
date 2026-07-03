import { focusFirstInput } from './form-focus.js';

const STORAGE_PREFIX = 'djcrud:filter-sidebar:';

function focusFilterForm(sidebar) {
    if (!sidebar || sidebar.classList.contains('is-hidden')) {
        return;
    }
    queueMicrotask(() => {
        focusFirstInput(sidebar.querySelector('form.djcrud-filter-form'));
    });
}

export function storageKey(pathname = window.location.pathname) {
    return STORAGE_PREFIX + pathname;
}

export function readPreference(pathname = window.location.pathname) {
    return sessionStorage.getItem(storageKey(pathname));
}

export function writePreference(value, pathname = window.location.pathname) {
    sessionStorage.setItem(storageKey(pathname), value);
}

export class FilterSidebarToggle extends HTMLElement {
    connectedCallback() {
        if (this._initialized) {
            this.syncState();
            return;
        }
        this._initialized = true;

        this.targetSelector = this.getAttribute('target') || '#djcrud-filter-sidebar';

        const button = document.createElement('button');
        button.type = 'button';
        button.className = this.className;
        button.setAttribute('aria-label', this.getAttribute('aria-label') || 'Filters');
        button.setAttribute('aria-expanded', 'false');
        while (this.firstChild) {
            button.appendChild(this.firstChild);
        }
        this.className = '';
        this.appendChild(button);

        button.addEventListener('click', (event) => {
            event.stopPropagation();
            this.toggle();
        });

        this.syncState();
    }

    get button() {
        return this.querySelector('button');
    }

    get target() {
        return document.querySelector(this.targetSelector);
    }

    syncState() {
        const button = this.button;
        const target = this.target;

        if (!button || !target) {
            return;
        }

        const preference = readPreference();
        if (preference === 'open') {
            target.classList.remove('is-hidden');
        } else if (preference === 'closed') {
            target.classList.add('is-hidden');
        }

        const isOpen = !target.classList.contains('is-hidden');
        button.classList.toggle('is-active', isOpen);
        button.setAttribute('aria-expanded', String(isOpen));
        if (isOpen) {
            focusFilterForm(target);
        }
    }

    toggle() {
        const button = this.button;
        const target = this.target;

        if (!button || !target) {
            return;
        }

        target.classList.toggle('is-hidden');
        writePreference(target.classList.contains('is-hidden') ? 'closed' : 'open');
        this.syncState();
    }
}

function syncAllFilterSidebarToggles() {
    for (const toggle of document.querySelectorAll('filter-sidebar-toggle')) {
        toggle.syncState();
    }
}

if (!FilterSidebarToggle._fragmentListener) {
    FilterSidebarToggle._fragmentListener = (event) => {
        const target = event.target;
        if (
            target?.matches?.('[up-list]')
            || target?.querySelector?.('[up-list]')
        ) {
            syncAllFilterSidebarToggles();
        }
    };
    document.addEventListener('up:fragment:inserted', FilterSidebarToggle._fragmentListener);
}

if (!customElements.get('filter-sidebar-toggle')) {
    customElements.define('filter-sidebar-toggle', FilterSidebarToggle);
}