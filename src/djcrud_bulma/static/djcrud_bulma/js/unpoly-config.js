/** Shared Unpoly + CSRF configuration for djcrud Bulma shells. */
export function configureUnpoly(up) {
    up.protocol.config.csrfHeader = 'X-CSRFToken';
    if (!up.feedback.config.currentClasses.includes('is-active')) {
        up.feedback.config.currentClasses.push('is-active');
    }
}

if (typeof window !== 'undefined' && window.up) {
    configureUnpoly(window.up);
}