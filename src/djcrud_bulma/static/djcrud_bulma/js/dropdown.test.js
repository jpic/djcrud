import { describe, it, expect, beforeEach, vi } from 'vitest'
import { BulmaDropdown } from './dropdown.js'

describe('BulmaDropdown Web Component', () => {
    beforeEach(() => {
        // Register the custom element
        if (!customElements.get('bulma-dropdown')) {
            customElements.define('bulma-dropdown', BulmaDropdown)
        }
        // Clean up the DOM
        document.body.innerHTML = ''
    })

    const createDropdown = (additionalClasses = '') => {
        const dropdown = document.createElement('bulma-dropdown')
        dropdown.className = `dropdown ${additionalClasses}`.trim()
        dropdown.innerHTML = `
            <div class="dropdown-trigger">
                <button class="button">Click me</button>
            </div>
            <div class="dropdown-menu">
                <div class="dropdown-content">
                    <a class="dropdown-item">Item 1</a>
                    <a class="dropdown-item">Item 2</a>
                </div>
            </div>
        `
        document.body.appendChild(dropdown)
        return dropdown
    }

    describe('initialization', () => {
        it('should be defined as a custom element', () => {
            expect(customElements.get('bulma-dropdown')).toBe(BulmaDropdown)
        })

        it('should render with children present', () => {
            const dropdown = createDropdown()
            const button = dropdown.querySelector('.dropdown-trigger button')
            expect(button).toBeTruthy()
            expect(button.textContent).toBe('Click me')
        })
    })

    describe('opening and closing', () => {
        it('should open dropdown when button is clicked', () => {
            const dropdown = createDropdown()
            const button = dropdown.querySelector('.dropdown-trigger button')

            expect(dropdown.classList.contains('is-active')).toBe(false)

            button.click()

            expect(dropdown.classList.contains('is-active')).toBe(true)
        })

        it('should close dropdown when button is clicked again', () => {
            const dropdown = createDropdown()
            const button = dropdown.querySelector('.dropdown-trigger button')

            button.click()
            expect(dropdown.classList.contains('is-active')).toBe(true)

            button.click()
            expect(dropdown.classList.contains('is-active')).toBe(false)
        })

        it('should toggle dropdown state on multiple clicks', () => {
            const dropdown = createDropdown()
            const button = dropdown.querySelector('.dropdown-trigger button')

            button.click()
            expect(dropdown.classList.contains('is-active')).toBe(true)

            button.click()
            expect(dropdown.classList.contains('is-active')).toBe(false)

            button.click()
            expect(dropdown.classList.contains('is-active')).toBe(true)
        })
    })

    describe('multiple dropdowns', () => {
        it('should close other dropdowns when opening a new one', () => {
            const dropdown1 = createDropdown()
            const dropdown2 = createDropdown()

            const button1 = dropdown1.querySelector('button')
            const button2 = dropdown2.querySelector('button')

            // Open first dropdown
            button1.click()
            expect(dropdown1.classList.contains('is-active')).toBe(true)
            expect(dropdown2.classList.contains('is-active')).toBe(false)

            // Open second dropdown
            button2.click()
            expect(dropdown1.classList.contains('is-active')).toBe(false)
            expect(dropdown2.classList.contains('is-active')).toBe(true)
        })

        it('should handle three or more dropdowns', () => {
            const dropdown1 = createDropdown()
            const dropdown2 = createDropdown()
            const dropdown3 = createDropdown()

            const button1 = dropdown1.querySelector('button')
            const button2 = dropdown2.querySelector('button')
            const button3 = dropdown3.querySelector('button')

            button1.click()
            button2.click()

            expect(dropdown1.classList.contains('is-active')).toBe(false)
            expect(dropdown2.classList.contains('is-active')).toBe(true)
            expect(dropdown3.classList.contains('is-active')).toBe(false)

            button3.click()

            expect(dropdown1.classList.contains('is-active')).toBe(false)
            expect(dropdown2.classList.contains('is-active')).toBe(false)
            expect(dropdown3.classList.contains('is-active')).toBe(true)
        })
    })

    describe('positioning', () => {
        it('should add is-up class when not enough space below', () => {
            const dropdown = createDropdown()
            const button = dropdown.querySelector('button')

            // Mock getBoundingClientRect to simulate bottom of viewport
            vi.spyOn(dropdown, 'getBoundingClientRect').mockReturnValue({
                top: 500,
                bottom: 600,
            })

            // Mock window.innerHeight
            Object.defineProperty(window, 'innerHeight', {
                writable: true,
                configurable: true,
                value: 650,
            })

            button.click()

            // spaceBelow = 650 - 600 = 50 (< 200)
            // spaceAbove = 500 (> 50)
            // Should add is-up class
            expect(dropdown.classList.contains('is-up')).toBe(true)
        })

        it('should not add is-up class when enough space below', () => {
            const dropdown = createDropdown()
            const button = dropdown.querySelector('button')

            // Mock getBoundingClientRect to simulate top of viewport
            vi.spyOn(dropdown, 'getBoundingClientRect').mockReturnValue({
                top: 100,
                bottom: 200,
            })

            Object.defineProperty(window, 'innerHeight', {
                writable: true,
                configurable: true,
                value: 800,
            })

            button.click()

            // spaceBelow = 800 - 200 = 600 (> 200)
            // Should not add is-up class
            expect(dropdown.classList.contains('is-up')).toBe(false)
        })

        it('should remove is-up class when repositioning with enough space', () => {
            const dropdown = createDropdown('is-up')
            const button = dropdown.querySelector('button')

            vi.spyOn(dropdown, 'getBoundingClientRect').mockReturnValue({
                top: 100,
                bottom: 200,
            })

            Object.defineProperty(window, 'innerHeight', {
                writable: true,
                configurable: true,
                value: 800,
            })

            button.click()

            expect(dropdown.classList.contains('is-up')).toBe(false)
        })
    })

    describe('event handling', () => {
        it('should stop propagation when button is clicked', () => {
            const dropdown = createDropdown()
            const button = dropdown.querySelector('button')

            const clickHandler = vi.fn()
            document.body.addEventListener('click', clickHandler)

            button.click()

            // Click should not propagate to body
            expect(clickHandler).not.toHaveBeenCalled()

            document.body.removeEventListener('click', clickHandler)
        })

        it('should not react to clicks outside dropdown-trigger button', () => {
            const dropdown = createDropdown()
            const menu = dropdown.querySelector('.dropdown-menu')

            expect(dropdown.classList.contains('is-active')).toBe(false)

            menu.click()

            expect(dropdown.classList.contains('is-active')).toBe(false)
        })

        it('should work when dynamically added to DOM (unpoly/htmx simulation)', () => {
            // Create dropdown element but don't add to DOM yet
            const container = document.createElement('div')
            container.innerHTML = `
                <bulma-dropdown class="dropdown">
                    <div class="dropdown-trigger">
                        <button class="button">Dynamic</button>
                    </div>
                    <div class="dropdown-menu">
                        <div class="dropdown-content">
                            <a class="dropdown-item">Item</a>
                        </div>
                    </div>
                </bulma-dropdown>
            `

            // Now add to DOM (simulates unpoly/htmx fragment insertion)
            document.body.appendChild(container)

            const dropdown = container.querySelector('bulma-dropdown')
            const button = dropdown.querySelector('button')

            // Should work even though added dynamically
            button.click()
            expect(dropdown.classList.contains('is-active')).toBe(true)
        })
    })

    describe('edge cases', () => {
        it('should handle dropdown without trigger button gracefully', () => {
            const dropdown = document.createElement('bulma-dropdown')
            dropdown.className = 'dropdown'
            dropdown.innerHTML = '<div>No button here</div>'
            document.body.appendChild(dropdown)

            // Should not throw error
            expect(() => dropdown.click()).not.toThrow()
            expect(dropdown.classList.contains('is-active')).toBe(false)
        })

        it('should handle multiple clicks in rapid succession', () => {
            const dropdown = createDropdown()
            const button = dropdown.querySelector('button')

            button.click()
            button.click()
            button.click()
            button.click()

            expect(dropdown.classList.contains('is-active')).toBe(false)
        })
    })
})
