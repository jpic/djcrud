const STORAGE_PREFIX = 'djcrud:list-action:';

export function clearAllListActionSelections() {
    for (const key of Object.keys(sessionStorage)) {
        if (key.startsWith(STORAGE_PREFIX)) {
            sessionStorage.removeItem(key);
        }
    }
    for (const bar of document.querySelectorAll('list-action-bar')) {
        bar.clearSelection();
    }
}

function scopeKey(scope, search = window.location.search) {
    const params = new URLSearchParams(search);
    params.delete('page');
    const qs = params.toString();
    return qs ? `${scope}?${qs}` : scope;
}

function buildPksQuery(pks) {
    return [...pks].map((pk) => `pks=${encodeURIComponent(pk)}`).join('&');
}

export class ListActionBar extends HTMLElement {
    get scopePath() {
        return this.getAttribute('scope') || window.location.pathname;
    }

    connectedCallback() {
        this.tableSelector = this.getAttribute('table') || '.djcrud-list';
        this.selectedPks = new Set();
        this._table = null;
        this._onTableChange = this.onTableChange.bind(this);
        this._onClearClick = () => this.clearSelection();
        this._onActionAccepted = () => this.clearSelection();

        queueMicrotask(() => this.init());

        if (!ListActionBar._fragmentListener) {
            ListActionBar._fragmentListener = (event) => {
                const target = event.target;
                for (const bar of document.querySelectorAll('list-action-bar')) {
                    if (
                        target?.matches?.(bar.tableSelector)
                        || target?.querySelector?.(bar.tableSelector)
                    ) {
                        bar.bindTable();
                    }
                }
            };
            document.addEventListener('up:fragment:inserted', ListActionBar._fragmentListener);
        }
    }

    init() {
        if (this._initialized) {
            return;
        }
        this._initialized = true;
        this.loadFromStorage();
        this.bindClearButton();
        this.bindActionLinks();
        this.bindTable();
        this.syncBar();
    }

    disconnectedCallback() {
        this.unbindTable();
        this._initialized = false;
    }

    get storageKey() {
        return STORAGE_PREFIX + scopeKey(this.scopePath);
    }

    get table() {
        if (!this._table || !document.contains(this._table)) {
            this._table = document.querySelector(this.tableSelector);
        }
        return this._table;
    }

    loadFromStorage() {
        const stored = sessionStorage.getItem(this.storageKey);
        if (!stored) {
            return;
        }
        try {
            const pks = JSON.parse(stored);
            if (Array.isArray(pks)) {
                this.selectedPks = new Set(pks.map(String));
            }
        } catch {
            sessionStorage.removeItem(this.storageKey);
        }
    }

    saveToStorage() {
        if (this.selectedPks.size === 0) {
            sessionStorage.removeItem(this.storageKey);
            return;
        }
        sessionStorage.setItem(
            this.storageKey,
            JSON.stringify([...this.selectedPks]),
        );
    }

    bindClearButton() {
        const button = this.querySelector('[data-role="clear"]');
        if (!button || button._listActionBound) {
            return;
        }
        button.addEventListener('click', this._onClearClick);
        button._listActionBound = true;
    }

    bindActionLinks() {
        for (const link of this.querySelectorAll('[data-list-action="urlupdate"]')) {
            if (!link.dataset.listActionOrigurl) {
                const href = link.getAttribute('href') || '';
                link.dataset.listActionOrigurl = href.split('?')[0];
            }
            link.addEventListener('up:layer:accepted', this._onActionAccepted);
        }
    }

    bindTable() {
        this.unbindTable();
        const table = this.table;
        if (!table) {
            return;
        }
        if (this._boundTable === table) {
            this.restoreCheckboxes();
            this.updateMasterCheckbox();
            return;
        }
        table.addEventListener('change', this._onTableChange, true);
        this._boundTable = table;
        this.restoreCheckboxes();
        this.updateMasterCheckbox();
    }

    unbindTable() {
        if (this._boundTable) {
            this._boundTable.removeEventListener('change', this._onTableChange, true);
            this._boundTable = null;
        }
    }

    onTableChange(event) {
        const target = event.target;
        if (target.matches('[data-master]')) {
            this.onMasterChange(target);
            return;
        }
        if (!target.matches('[data-pk]')) {
            return;
        }
        const pk = target.getAttribute('data-pk');
        if (target.checked) {
            this.selectedPks.add(pk);
        } else {
            this.selectedPks.delete(pk);
        }
        this.saveToStorage();
        this.updateMasterCheckbox();
        this.syncBar();
    }

    onMasterChange(master) {
        const rowCheckboxes = this.visibleRowCheckboxes();
        for (const checkbox of rowCheckboxes) {
            const pk = checkbox.getAttribute('data-pk');
            checkbox.checked = master.checked;
            if (master.checked) {
                this.selectedPks.add(pk);
            } else {
                this.selectedPks.delete(pk);
            }
        }
        this.saveToStorage();
        this.updateMasterCheckbox();
        this.syncBar();
    }

    visibleRowCheckboxes() {
        const table = this.table;
        if (!table) {
            return [];
        }
        return [...table.querySelectorAll('[data-pk]')];
    }

    restoreCheckboxes() {
        for (const checkbox of this.visibleRowCheckboxes()) {
            const pk = checkbox.getAttribute('data-pk');
            checkbox.checked = this.selectedPks.has(pk);
        }
        this.updateAllowedActions();
    }

    updateMasterCheckbox() {
        const table = this.table;
        if (!table) {
            return;
        }
        const master = table.querySelector('[data-master]');
        if (!master) {
            return;
        }
        const rowCheckboxes = this.visibleRowCheckboxes();
        if (rowCheckboxes.length === 0) {
            master.checked = false;
            master.indeterminate = false;
            return;
        }
        const selectedVisible = rowCheckboxes.filter(
            (cb) => this.selectedPks.has(cb.getAttribute('data-pk')),
        ).length;
        master.checked = selectedVisible === rowCheckboxes.length;
        master.indeterminate = selectedVisible > 0 && selectedVisible < rowCheckboxes.length;
    }

    updateActionUrls() {
        const query = buildPksQuery(this.selectedPks);
        for (const link of this.querySelectorAll('[data-list-action="urlupdate"]')) {
            if (!link.dataset.listActionOrigurl) {
                const href = link.getAttribute('href') || '';
                link.dataset.listActionOrigurl = href.split('?')[0];
            }
            const base = link.dataset.listActionOrigurl;
            link.setAttribute('href', query ? `${base}?${query}` : base);
        }
    }

    updateAllowedActions() {
        const selectedCbs = this.visibleRowCheckboxes().filter((cb) => cb.checked);
        if (selectedCbs.length === 0) {
            this.showAllActions();
            return;
        }

        let intersection = null;
        for (const cb of selectedCbs) {
            const raw = cb.dataset.listActions || '';
            const allowed = raw.split(',').map((s) => s.trim()).filter(Boolean);
            if (intersection === null) {
                intersection = new Set(allowed);
            } else {
                intersection = new Set([...intersection].filter((code) => allowed.includes(code)));
            }
        }

        const allowedSet = intersection || new Set();
        for (const link of this.querySelectorAll('[data-codename]')) {
            const code = link.dataset.codename;
            link.hidden = !allowedSet.has(code);
        }
    }

    showAllActions() {
        for (const link of this.querySelectorAll('[data-codename]')) {
            link.hidden = false;
        }
    }

    selectionCountLabel(count) {
        if (count === 1) {
            return this.dataset.countLabelOne || '1 selected';
        }
        const template = this.dataset.countLabelOther || `${count} selected`;
        return template.replace('__COUNT__', String(count));
    }

    syncBar() {
        const count = this.selectedPks.size;
        const countEl = this.querySelector('[data-role="count"]');
        if (countEl) {
            countEl.textContent = this.selectionCountLabel(count);
        }
        this.hidden = count === 0;
        this.updateActionUrls();
        this.updateAllowedActions();
    }

    clearSelection() {
        this.selectedPks.clear();
        sessionStorage.removeItem(this.storageKey);
        for (const checkbox of this.visibleRowCheckboxes()) {
            checkbox.checked = false;
        }
        const table = this.table;
        const master = table?.querySelector('[data-master]');
        if (master) {
            master.checked = false;
            master.indeterminate = false;
        }
        this.syncBar();
    }
}

if (!customElements.get('list-action-bar')) {
    customElements.define('list-action-bar', ListActionBar);
}

if (typeof window !== 'undefined') {
    window.djcrudClearListActionSelections = clearAllListActionSelections;
}