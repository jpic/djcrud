import { describe, it, expect, beforeEach, vi } from 'vitest'
import { focusFirstInput, isFormVisible } from './form-focus.js'

describe('focusFirstInput', () => {
    beforeEach(() => {
        document.body.innerHTML = ''
    })

    it('focuses the first visible input', () => {
        document.body.innerHTML = `
            <form method="post">
                <input type="hidden" name="csrf" value="x">
                <input type="text" name="name" id="name-input">
                <input type="text" name="other">
            </form>
        `
        const form = document.querySelector('form')
        const nameInput = document.getElementById('name-input')

        const focusSpy = vi.spyOn(nameInput, 'focus')
        focusFirstInput(form)

        expect(focusSpy).toHaveBeenCalledWith({ preventScroll: true })
    })

    it('focuses select fields', () => {
        document.body.innerHTML = `
            <form method="post">
                <select name="category"><option>a</option></select>
            </form>
        `
        const form = document.querySelector('form')
        const select = form.querySelector('select')

        const focusSpy = vi.spyOn(select, 'focus')
        focusFirstInput(form)

        expect(focusSpy).toHaveBeenCalledWith({ preventScroll: true })
    })

    it('focuses autocomplete input inside custom element', () => {
        document.body.innerHTML = `
            <form class="djcrud-filter-form" method="get">
                <autocomplete-select>
                    <autocomplete-select-input>
                        <input type="text" name="groups-input">
                    </autocomplete-select-input>
                </autocomplete-select>
            </form>
        `
        const form = document.querySelector('form')
        const input = form.querySelector('autocomplete-select-input input')

        const focusSpy = vi.spyOn(input, 'focus')
        focusFirstInput(form)

        expect(focusSpy).toHaveBeenCalledWith({ preventScroll: true })
    })

    it('skips hidden forms', () => {
        document.body.innerHTML = `
            <aside class="is-hidden" style="display: none">
                <form class="djcrud-filter-form" method="get">
                    <input type="text" name="search">
                </form>
            </aside>
        `
        const form = document.querySelector('form')
        const input = form.querySelector('input')
        const focusSpy = vi.spyOn(input, 'focus')

        expect(isFormVisible(form)).toBe(false)
        focusFirstInput(form)

        expect(focusSpy).not.toHaveBeenCalled()
    })

    it('skips disabled fields', () => {
        document.body.innerHTML = `
            <form method="post">
                <input type="text" name="disabled" disabled>
                <input type="text" name="enabled" id="enabled">
            </form>
        `
        const form = document.querySelector('form')
        const enabled = document.getElementById('enabled')

        const focusSpy = vi.spyOn(enabled, 'focus')
        focusFirstInput(form)

        expect(focusSpy).toHaveBeenCalledWith({ preventScroll: true })
    })
})