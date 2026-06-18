// Web Component for Bulma dropdown with event delegation
export class BulmaDropdown extends HTMLElement {
    connectedCallback() {
        // Event delegation: listen on the component itself
        this.addEventListener('click', (event) => {
            const button = event.target.closest('.dropdown-trigger button');
            if (!button) return;

            event.stopPropagation();
            const wasActive = this.classList.contains('is-active');

            // Close all other dropdowns
            document.querySelectorAll('bulma-dropdown.is-active').forEach(dropdown => {
                if (dropdown !== this) {
                    dropdown.classList.remove('is-active');
                }
            });

            // Toggle current dropdown
            if (!wasActive) {
                this.classList.add('is-active');
                this.positionDropdown();
            } else {
                this.classList.remove('is-active');
            }
        });
    }

    positionDropdown() {
        const rect = this.getBoundingClientRect();
        const spaceBelow = window.innerHeight - rect.bottom;
        const spaceAbove = rect.top;

        // If not enough space below but more space above, add is-up class
        if (spaceBelow < 200 && spaceAbove > spaceBelow) {
            this.classList.add('is-up');
        } else {
            this.classList.remove('is-up');
        }
    }
}

// Register the custom element
if (!customElements.get('bulma-dropdown')) {
    customElements.define('bulma-dropdown', BulmaDropdown);
}
