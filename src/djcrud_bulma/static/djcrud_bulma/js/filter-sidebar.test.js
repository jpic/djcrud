import { describe, it, expect, beforeEach } from 'vitest'
import {
    FilterSidebarToggle,
    readPreference,
    storageKey,
    writePreference,
} from './filter-sidebar.js'

describe('FilterSidebarToggle Web Component', () => {
    beforeEach(() => {
        sessionStorage.clear()
        if (!customElements.get('filter-sidebar-toggle')) {
            customElements.define('filter-sidebar-toggle', FilterSidebarToggle)
        }
        document.body.innerHTML = ''
    })

    const createToggleWithSidebar = (options = {}) => {
        const sidebar = document.createElement('aside')
        sidebar.id = options.sidebarId || 'djcrud-filter-sidebar'
        if (options.startHidden) {
            sidebar.classList.add('is-hidden')
        }
        document.body.appendChild(sidebar)

        const toggle = document.createElement('filter-sidebar-toggle')
        toggle.setAttribute('target', `#${sidebar.id}`)
        toggle.className = options.buttonClass || 'button'
        toggle.innerHTML = '<span>Filters</span>'
        document.body.appendChild(toggle)

        return {
            toggle,
            sidebar,
            button: toggle.querySelector('button'),
        }
    }

    describe('initialization', () => {
        it('should be defined as a custom element', () => {
            expect(customElements.get('filter-sidebar-toggle')).toBe(FilterSidebarToggle)
        })

        it('should wrap children in a button', () => {
            const { toggle, button } = createToggleWithSidebar()

            expect(button).toBeTruthy()
            expect(button.tagName).toBe('BUTTON')
            expect(button.getAttribute('type')).toBe('button')
            expect(button.classList.contains('button')).toBe(true)
            expect(button.textContent).toContain('Filters')
            expect(toggle.className).toBe('')
        })

        it('should default target selector to #djcrud-filter-sidebar', () => {
            const toggle = document.createElement('filter-sidebar-toggle')
            document.body.appendChild(toggle)

            expect(toggle.targetSelector).toBe('#djcrud-filter-sidebar')
        })
    })

    describe('toggle functionality', () => {
        it('should toggle sidebar visibility when clicked', () => {
            const { button, sidebar } = createToggleWithSidebar({ startHidden: true })

            expect(sidebar.classList.contains('is-hidden')).toBe(true)
            expect(button.getAttribute('aria-expanded')).toBe('false')

            button.click()

            expect(sidebar.classList.contains('is-hidden')).toBe(false)
            expect(button.classList.contains('is-active')).toBe(true)
            expect(button.getAttribute('aria-expanded')).toBe('true')
            expect(readPreference()).toBe('open')
        })

        it('should toggle back when clicked again', () => {
            const { button, sidebar } = createToggleWithSidebar()

            button.click()
            expect(sidebar.classList.contains('is-hidden')).toBe(true)
            expect(readPreference()).toBe('closed')

            button.click()
            expect(sidebar.classList.contains('is-hidden')).toBe(false)
            expect(readPreference()).toBe('open')
        })
    })

    describe('sessionStorage persistence', () => {
        it('should restore open preference on syncState', () => {
            writePreference('open', '/auth/user/')
            const { toggle, sidebar } = createToggleWithSidebar({ startHidden: true })

            Object.defineProperty(window, 'location', {
                value: { pathname: '/auth/user/' },
                writable: true,
            })

            toggle.syncState()

            expect(sidebar.classList.contains('is-hidden')).toBe(false)
        })

        it('should restore closed preference on syncState', () => {
            writePreference('closed', '/auth/user/')
            const { toggle, sidebar } = createToggleWithSidebar()

            Object.defineProperty(window, 'location', {
                value: { pathname: '/auth/user/' },
                writable: true,
            })

            toggle.syncState()

            expect(sidebar.classList.contains('is-hidden')).toBe(true)
        })

        it('should use pathname-scoped storage keys', () => {
            expect(storageKey('/auth/user/')).toBe('djcrud:filter-sidebar:/auth/user/')
        })
    })

    describe('edge cases', () => {
        it('should handle missing target gracefully', () => {
            const toggle = document.createElement('filter-sidebar-toggle')
            toggle.setAttribute('target', '#nonexistent')
            document.body.appendChild(toggle)

            expect(() => toggle.querySelector('button').click()).not.toThrow()
        })

        it('should stop event propagation', () => {
            const { button } = createToggleWithSidebar({ startHidden: true })

            let propagated = false
            document.body.addEventListener('click', () => {
                propagated = true
            })

            button.click()

            expect(propagated).toBe(false)
        })
    })
})