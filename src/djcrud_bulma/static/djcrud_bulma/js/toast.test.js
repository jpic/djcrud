import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { registerToastCompiler, TOAST_DURATION_MS } from './toast.js'

describe('toast notifications', () => {
    let compilerCallback
    const destroy = vi.fn()

    beforeEach(() => {
        destroy.mockClear()
        compilerCallback = null
        document.body.innerHTML = ''

        registerToastCompiler({
            compiler: (selector, callback) => {
                if (selector === '[up-flashes] > .djcrud-toast') {
                    compilerCallback = callback
                }
            },
            destroy,
        })
    })

    afterEach(() => {
        vi.useRealTimers()
    })

    const mountToast = () => {
        document.body.innerHTML = `
            <div up-flashes>
                <div class="notification djcrud-toast is-success">
                    <button class="delete" aria-label="dismiss"></button>
                    Create: Alice
                </div>
            </div>
        `
        const toast = document.querySelector('.djcrud-toast')
        compilerCallback(toast)
        return toast
    }

    it('registers the up-flashes toast compiler', () => {
        expect(compilerCallback).toBeTypeOf('function')
    })

    it('auto-dismisses after the configured duration', () => {
        vi.useFakeTimers()
        const toast = mountToast()

        vi.advanceTimersByTime(TOAST_DURATION_MS)

        expect(destroy).toHaveBeenCalledWith(toast, {
            animation: 'fade-out',
            duration: 200,
        })
    })

    it('dismisses immediately when the delete button is clicked', () => {
        vi.useFakeTimers()
        const toast = mountToast()

        toast.querySelector('.delete').click()

        expect(destroy).toHaveBeenCalledWith(toast, {
            animation: 'fade-out',
            duration: 200,
        })

        vi.advanceTimersByTime(TOAST_DURATION_MS)
        expect(destroy).toHaveBeenCalledTimes(1)
    })

    it('works without a delete button', () => {
        vi.useFakeTimers()
        document.body.innerHTML = `
            <div up-flashes>
                <div class="notification djcrud-toast is-danger">Error message</div>
            </div>
        `
        const toast = document.querySelector('.djcrud-toast')
        compilerCallback(toast)

        vi.advanceTimersByTime(TOAST_DURATION_MS)

        expect(destroy).toHaveBeenCalledWith(toast, {
            animation: 'fade-out',
            duration: 200,
        })
    })
})