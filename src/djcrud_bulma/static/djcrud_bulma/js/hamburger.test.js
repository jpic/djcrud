import { describe, it, expect, beforeEach } from 'vitest'
import { HamburgerMenu } from './hamburger.js'

describe('HamburgerMenu Web Component', () => {
    beforeEach(() => {
        if (!customElements.get('hamburger-menu')) {
            customElements.define('hamburger-menu', HamburgerMenu)
        }
        document.body.innerHTML = ''
    })

    const createHamburgerWithSidebar = (targetId = 'sidebar') => {
        const sidebar = document.createElement('aside')
        sidebar.id = targetId
        sidebar.className = 'djcrud-sidebar'
        document.body.appendChild(sidebar)

        const hamburger = document.createElement('hamburger-menu')
        if (targetId !== 'sidebar') {
            hamburger.setAttribute('target', `#${targetId}`)
        }
        document.body.appendChild(hamburger)

        return {
            hamburger,
            sidebar,
            burger: hamburger.querySelector('.navbar-burger'),
        }
    }

    describe('initialization', () => {
        it('should be defined as a custom element', () => {
            expect(customElements.get('hamburger-menu')).toBe(HamburgerMenu)
        })

        it('should render hamburger with correct structure', () => {
            const { burger } = createHamburgerWithSidebar()

            expect(burger).toBeTruthy()
            expect(burger.tagName).toBe('BUTTON')
            expect(burger.getAttribute('type')).toBe('button')
            expect(burger.getAttribute('aria-label')).toBe('menu')
            expect(burger.getAttribute('aria-expanded')).toBe('true')
            expect(burger.classList.contains('is-active')).toBe(true)
            expect(burger.querySelectorAll('span[aria-hidden="true"]').length).toBe(4)
        })

        it('should use default target selector when not specified', () => {
            const hamburger = document.createElement('hamburger-menu')
            document.body.appendChild(hamburger)

            expect(hamburger.targetSelector).toBe('#sidebar')
        })

        it('should use custom target selector when specified', () => {
            const hamburger = document.createElement('hamburger-menu')
            hamburger.setAttribute('target', '#custom-menu')
            document.body.appendChild(hamburger)

            expect(hamburger.targetSelector).toBe('#custom-menu')
        })
    })

    describe('toggle functionality', () => {
        it('should toggle sidebar visibility when clicked', () => {
            const { burger, sidebar } = createHamburgerWithSidebar()

            expect(sidebar.classList.contains('is-hidden')).toBe(false)
            expect(burger.classList.contains('is-active')).toBe(true)

            burger.click()

            expect(sidebar.classList.contains('is-hidden')).toBe(true)
            expect(burger.classList.contains('is-active')).toBe(false)
            expect(burger.getAttribute('aria-expanded')).toBe('false')
        })

        it('should toggle back when clicked again', () => {
            const { burger, sidebar } = createHamburgerWithSidebar()

            burger.click()
            expect(sidebar.classList.contains('is-hidden')).toBe(true)

            burger.click()
            expect(sidebar.classList.contains('is-hidden')).toBe(false)
            expect(burger.classList.contains('is-active')).toBe(true)
            expect(burger.getAttribute('aria-expanded')).toBe('true')
        })

        it('should handle multiple clicks correctly', () => {
            const { burger, sidebar } = createHamburgerWithSidebar()

            burger.click()
            expect(sidebar.classList.contains('is-hidden')).toBe(true)

            burger.click()
            expect(sidebar.classList.contains('is-hidden')).toBe(false)

            burger.click()
            expect(sidebar.classList.contains('is-hidden')).toBe(true)
        })
    })

    describe('close method', () => {
        it('should close the menu when close() is called', () => {
            const { hamburger, burger, sidebar } = createHamburgerWithSidebar()

            burger.click()
            expect(sidebar.classList.contains('is-hidden')).toBe(true)

            hamburger.close()
            expect(sidebar.classList.contains('is-hidden')).toBe(true)
            expect(burger.classList.contains('is-active')).toBe(false)
            expect(burger.getAttribute('aria-expanded')).toBe('false')
        })

        it('should be idempotent when menu is already closed', () => {
            const { hamburger, burger, sidebar } = createHamburgerWithSidebar()

            hamburger.close()

            expect(sidebar.classList.contains('is-hidden')).toBe(true)
            expect(burger.classList.contains('is-active')).toBe(false)
        })
    })

    describe('custom targets', () => {
        it('should work with custom target selector', () => {
            const customSidebar = document.createElement('div')
            customSidebar.id = 'custom-menu'
            document.body.appendChild(customSidebar)

            const hamburger = document.createElement('hamburger-menu')
            hamburger.setAttribute('target', '#custom-menu')
            document.body.appendChild(hamburger)
            const burger = hamburger.querySelector('.navbar-burger')

            burger.click()

            expect(customSidebar.classList.contains('is-hidden')).toBe(true)
        })

        it('should handle multiple hamburger menus with different targets', () => {
            const sidebar1 = document.createElement('div')
            sidebar1.id = 'menu1'
            document.body.appendChild(sidebar1)

            const sidebar2 = document.createElement('div')
            sidebar2.id = 'menu2'
            document.body.appendChild(sidebar2)

            const hamburger1 = document.createElement('hamburger-menu')
            hamburger1.setAttribute('target', '#menu1')
            document.body.appendChild(hamburger1)

            const hamburger2 = document.createElement('hamburger-menu')
            hamburger2.setAttribute('target', '#menu2')
            document.body.appendChild(hamburger2)

            hamburger1.querySelector('.navbar-burger').click()
            expect(sidebar1.classList.contains('is-hidden')).toBe(true)
            expect(sidebar2.classList.contains('is-hidden')).toBe(false)

            hamburger2.querySelector('.navbar-burger').click()
            expect(sidebar1.classList.contains('is-hidden')).toBe(true)
            expect(sidebar2.classList.contains('is-hidden')).toBe(true)
        })
    })

    describe('edge cases', () => {
        it('should handle missing target gracefully', () => {
            const hamburger = document.createElement('hamburger-menu')
            hamburger.setAttribute('target', '#nonexistent')
            document.body.appendChild(hamburger)

            expect(() => hamburger.querySelector('.navbar-burger').click()).not.toThrow()
        })

        it('should handle dynamically added to DOM', () => {
            const sidebar = document.createElement('aside')
            sidebar.id = 'sidebar'
            document.body.appendChild(sidebar)

            const container = document.createElement('div')
            container.innerHTML = '<hamburger-menu></hamburger-menu>'
            document.body.appendChild(container)

            const hamburger = container.querySelector('hamburger-menu')
            const burger = hamburger.querySelector('.navbar-burger')

            burger.click()
            expect(sidebar.classList.contains('is-hidden')).toBe(true)
        })

        it('should stop event propagation', () => {
            const { burger } = createHamburgerWithSidebar()

            let propagated = false
            document.body.addEventListener('click', () => {
                propagated = true
            })

            burger.click()

            expect(propagated).toBe(false)
        })
    })
})