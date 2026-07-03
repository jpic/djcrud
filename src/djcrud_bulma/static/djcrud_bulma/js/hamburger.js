// Web Component for hamburger menu toggle
export class HamburgerMenu extends HTMLElement {
    connectedCallback() {
        if (this._initialized) {
            this.syncState();
            return;
        }
        this._initialized = true;

        // Get target from data attribute or default to sidebar ID
        this.targetSelector = this.getAttribute('target') || '#sidebar';

        // Use <button> so Unpoly nav feedback won't strip is-active from <a> in <nav>
        this.innerHTML = `
            <button type="button" class="navbar-burger" aria-label="menu" aria-expanded="false">
                <span aria-hidden="true"></span>
                <span aria-hidden="true"></span>
                <span aria-hidden="true"></span>
                <span aria-hidden="true"></span>
            </button>
        `;

        const burger = this.querySelector('.navbar-burger');
        if (burger) {
            burger.addEventListener('click', (event) => {
                event.stopPropagation();
                this.toggle();
            });
        }

        this.syncState();
    }

    syncState() {
        const burger = this.querySelector('.navbar-burger');
        const target = document.querySelector(this.targetSelector);

        if (!burger || !target) {
            return;
        }

        const isOpen = !target.classList.contains('is-hidden');
        burger.classList.toggle('is-active', isOpen);
        burger.setAttribute('aria-expanded', String(isOpen));
    }

    toggle() {
        const target = document.querySelector(this.targetSelector);

        if (!this.querySelector('.navbar-burger') || !target) {
            return;
        }

        target.classList.toggle('is-hidden');
        this.syncState();
    }

    close() {
        const target = document.querySelector(this.targetSelector);

        if (!this.querySelector('.navbar-burger') || !target) {
            return;
        }

        target.classList.add('is-hidden');
        this.syncState();
    }
}

// Register the custom element
if (!customElements.get('hamburger-menu')) {
    customElements.define('hamburger-menu', HamburgerMenu);
}
