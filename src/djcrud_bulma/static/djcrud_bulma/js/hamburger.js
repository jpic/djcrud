// Web Component for hamburger menu toggle
export class HamburgerMenu extends HTMLElement {
    connectedCallback() {
        console.log('HamburgerMenu connected');

        // Get target from data attribute or default to sidebar ID
        this.targetSelector = this.getAttribute('target') || '#sidebar';
        console.log('Target selector:', this.targetSelector);

        // Create hamburger icon structure (using <a> as per Bulma docs)
        this.innerHTML = `
            <a class="navbar-burger" role="button" aria-label="menu" aria-expanded="false">
                <span aria-hidden="true"></span>
                <span aria-hidden="true"></span>
                <span aria-hidden="true"></span>
                <span aria-hidden="true"></span>
            </a>
        `;

        // Add click handler to the burger element
        const burger = this.querySelector('.navbar-burger');
        if (burger) {
            burger.addEventListener('click', (event) => {
                console.log('Hamburger clicked');
                event.preventDefault();
                event.stopPropagation();
                this.toggle();
            });
        }
    }

    toggle() {
        console.log('Toggle called');
        const burger = this.querySelector('.navbar-burger');
        const target = document.querySelector(this.targetSelector);

        console.log('Burger:', burger);
        console.log('Target:', target);

        if (!burger || !target) {
            console.log('Missing burger or target!');
            return;
        }

        // Toggle active state
        const isActive = burger.classList.toggle('is-active');
        burger.setAttribute('aria-expanded', isActive.toString());

        // Toggle target visibility
        target.classList.toggle('is-hidden-mobile');

        console.log('Toggled! isActive:', isActive);
    }

    close() {
        const burger = this.querySelector('.navbar-burger');
        const target = document.querySelector(this.targetSelector);

        if (!burger || !target) return;

        burger.classList.remove('is-active');
        burger.setAttribute('aria-expanded', 'false');
        target.classList.add('is-hidden-mobile');
    }
}

// Register the custom element
if (!customElements.get('hamburger-menu')) {
    customElements.define('hamburger-menu', HamburgerMenu);
}
