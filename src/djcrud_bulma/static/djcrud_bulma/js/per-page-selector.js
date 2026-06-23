/**
 * Per-Page Selector Web Component
 *
 * Handles changing the number of rows per page in a table with Unpoly navigation.
 *
 * Usage:
 *   <per-page-selector current="25" target="[up-table]"></per-page-selector>
 */
class PerPageSelector extends HTMLElement {
    connectedCallback() {
        // Don't initialize if already initialized
        if (this.hasAttribute('data-initialized')) {
            return;
        }
        this.setAttribute('data-initialized', 'true');

        const current = this.getAttribute('current') || '25';
        const target = this.getAttribute('target') || '[up-table]';
        const options = (this.getAttribute('options') || '10,25,50,100').split(',');

        // Generate unique ID
        const uid = `per-page-${Math.random().toString(36).substr(2, 9)}`;

        // Create elements using DOM methods
        const field = document.createElement('div');
        field.className = 'field has-addons';

        const labelControl = document.createElement('p');
        labelControl.className = 'control';
        const labelSpan = document.createElement('span');
        labelSpan.className = 'button is-static';
        labelSpan.textContent = 'Rows per page:';
        labelControl.appendChild(labelSpan);

        const selectControl = document.createElement('p');
        selectControl.className = 'control';
        const selectWrapper = document.createElement('div');
        selectWrapper.className = 'select is-small';

        const select = document.createElement('select');
        select.id = uid;
        select.setAttribute('data-target', target);

        // Add options
        options.forEach(opt => {
            const option = document.createElement('option');
            option.value = opt;
            option.textContent = opt;
            if (opt === current) {
                option.selected = true;
            }
            select.appendChild(option);
        });

        // Assemble
        selectWrapper.appendChild(select);
        selectControl.appendChild(selectWrapper);
        field.appendChild(labelControl);
        field.appendChild(selectControl);
        this.appendChild(field);
    }
}

// Define the custom element
customElements.define('per-page-selector', PerPageSelector);

// Use event delegation at document level to handle changes
// This ensures it works even if the component isn't fully initialized
document.addEventListener('change', function(e) {
    // Check if the change event came from a per-page-selector select
    const matchesDescendant = e.target.closest('per-page-selector') !== null;
    const matchesId = e.target.id && e.target.id.startsWith('per-page-');

    if (matchesDescendant || matchesId) {
        const url = new URL(window.location.href);
        url.searchParams.set('per_page', e.target.value);
        url.searchParams.set('page', '1');

        // Use full page navigation (more reliable than Unpoly in this case)
        window.location.href = url.toString();
    }
});
