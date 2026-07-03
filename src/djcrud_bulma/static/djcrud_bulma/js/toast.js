export const TOAST_DURATION_MS = 4000;

export function registerToastCompiler(up) {
    up.compiler('[up-flashes] > .djcrud-toast', (toast) => {
        const dismiss = () => up.destroy(toast, { animation: 'fade-out', duration: 200 });
        const timer = setTimeout(dismiss, TOAST_DURATION_MS);
        const deleteButton = toast.querySelector('.delete');
        if (deleteButton) {
            deleteButton.addEventListener('click', () => {
                clearTimeout(timer);
                dismiss();
            });
        }
    });
}

if (typeof window !== 'undefined' && window.up) {
    registerToastCompiler(window.up);
}