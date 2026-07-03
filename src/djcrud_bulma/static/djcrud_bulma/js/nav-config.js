/** Navigation-specific Unpoly compilers (shell config lives in unpoly-config.js). */
export function registerNavConfig(_up) {}

if (typeof window !== 'undefined' && window.up) {
    registerNavConfig(window.up);
}