import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { ListActionBar, clearAllListActionSelections } from './list-action-bar.js'

describe('ListActionBar', () => {
    beforeEach(() => {
        sessionStorage.clear()
        window.history.replaceState({}, '', '/')
        if (!customElements.get('list-action-bar')) {
            customElements.define('list-action-bar', ListActionBar)
        }
        document.body.innerHTML = ''
    })

    afterEach(() => {
        sessionStorage.clear()
    })

    const createFixture = async () => {
        document.body.innerHTML = `
            <div class="djcrud-list">
                <table>
                    <thead>
                        <tr><th><input type="checkbox" data-master="1"></th></tr>
                    </thead>
                    <tbody>
                        <tr><td><input type="checkbox" data-pk="1"></td></tr>
                        <tr><td><input type="checkbox" data-pk="2"></td></tr>
                    </tbody>
                </table>
            </div>
            <list-action-bar table=".djcrud-list" scope="/users/">
                <span data-role="count"></span>
                <button type="button" data-role="clear">Clear selection</button>
                <a href="/users/deleteobjects/" data-list-action="urlupdate">Delete</a>
            </list-action-bar>
        `
        const bar = document.querySelector('list-action-bar')
        await Promise.resolve()
        return bar
    }

    it('shows count text for one and many selections', async () => {
        const bar = await createFixture()
        const cb1 = document.querySelector('[data-pk="1"]')

        cb1.checked = true
        cb1.dispatchEvent(new Event('change', { bubbles: true }))
        expect(bar.querySelector('[data-role="count"]').textContent).toBe('1 selected')
        expect(bar.hidden).toBe(false)

        const cb2 = document.querySelector('[data-pk="2"]')
        cb2.checked = true
        cb2.dispatchEvent(new Event('change', { bubbles: true }))
        expect(bar.querySelector('[data-role="count"]').textContent).toBe('2 selected')
    })

    it('clears selection and hides the bar', async () => {
        const bar = await createFixture()
        const cb1 = document.querySelector('[data-pk="1"]')
        cb1.checked = true
        cb1.dispatchEvent(new Event('change', { bubbles: true }))
        expect(bar.selectedPks.size).toBe(1)

        bar.clearSelection()

        expect(bar.hidden).toBe(true)
        expect(cb1.checked).toBe(false)
        expect(sessionStorage.getItem('djcrud:list-action:/users/')).toBeNull()
    })

    it('builds action URLs from the selection set', async () => {
        const bar = await createFixture()
        const link = bar.querySelector('[data-list-action="urlupdate"]')

        document.querySelector('[data-pk="1"]').checked = true
        document.querySelector('[data-pk="1"]').dispatchEvent(new Event('change', { bubbles: true }))
        document.querySelector('[data-pk="2"]').checked = true
        document.querySelector('[data-pk="2"]').dispatchEvent(new Event('change', { bubbles: true }))

        expect(link.getAttribute('href')).toBe('/users/deleteobjects/?pks=1&pks=2')
    })

    it('restores selection from sessionStorage', async () => {
        sessionStorage.setItem('djcrud:list-action:/users/', JSON.stringify(['1', '2']))
        const bar = await createFixture()

        expect(bar.storageKey).toBe('djcrud:list-action:/users/')
        expect(bar.selectedPks.size).toBe(2)
        expect(bar.hidden).toBe(false)
        expect(document.querySelector('[data-pk="1"]').checked).toBe(true)
        expect(document.querySelector('[data-pk="2"]').checked).toBe(true)
        expect(bar.querySelector('[data-role="count"]').textContent).toBe('2 selected')
    })

    it('keeps selection across simulated page fragment swap', async () => {
        const bar = await createFixture()
        document.querySelector('[data-pk="1"]').checked = true
        document.querySelector('[data-pk="1"]').dispatchEvent(new Event('change', { bubbles: true }))

        document.querySelector('.djcrud-list').innerHTML = `
            <table>
                <tbody>
                    <tr><td><input type="checkbox" data-pk="3"></td></tr>
                </tbody>
            </table>
        `
        const list = document.querySelector('.djcrud-list')
        list.dispatchEvent(new CustomEvent('up:fragment:inserted', {
            bubbles: true,
        }))

        const cb3 = document.querySelector('[data-pk="3"]')
        cb3.checked = true
        cb3.dispatchEvent(new Event('change', { bubbles: true }))

        const link = bar.querySelector('[data-list-action="urlupdate"]')
        expect(link.getAttribute('href')).toBe('/users/deleteobjects/?pks=1&pks=3')
    })

    it('sets master checkbox indeterminate for partial page selection', async () => {
        await createFixture()
        document.querySelector('[data-pk="1"]').checked = true
        document.querySelector('[data-pk="1"]').dispatchEvent(new Event('change', { bubbles: true }))

        const master = document.querySelector('[data-master]')
        expect(master.indeterminate).toBe(true)
        expect(master.checked).toBe(false)
    })

    it('clears selection when a list action link is accepted', async () => {
        const bar = await createFixture()
        document.querySelector('[data-pk="1"]').checked = true
        document.querySelector('[data-pk="1"]').dispatchEvent(new Event('change', { bubbles: true }))
        expect(bar.selectedPks.size).toBe(1)

        bar.querySelector('[data-list-action="urlupdate"]').dispatchEvent(
            new Event('up:layer:accepted', { bubbles: true }),
        )

        expect(bar.selectedPks.size).toBe(0)
        expect(bar.hidden).toBe(true)
        expect(sessionStorage.getItem('djcrud:list-action:/users/')).toBeNull()
    })

    it('clearAllListActionSelections clears storage before a fragment swap', async () => {
        const bar = await createFixture()
        document.querySelector('[data-pk="1"]').checked = true
        document.querySelector('[data-pk="1"]').dispatchEvent(new Event('change', { bubbles: true }))
        document.querySelector('[data-pk="2"]').checked = true
        document.querySelector('[data-pk="2"]').dispatchEvent(new Event('change', { bubbles: true }))
        expect(sessionStorage.getItem('djcrud:list-action:/users/')).not.toBeNull()

        clearAllListActionSelections()

        expect(sessionStorage.getItem('djcrud:list-action:/users/')).toBeNull()
        expect(bar.hidden).toBe(true)

        document.querySelector('.djcrud-list').innerHTML = `
            <table>
                <tbody>
                    <tr><td><input type="checkbox" data-pk="3"></td></tr>
                </tbody>
            </table>
        `
        document.body.innerHTML = `
            <div class="djcrud-list">
                <table>
                    <tbody>
                        <tr><td><input type="checkbox" data-pk="3"></td></tr>
                    </tbody>
                </table>
            </div>
            <list-action-bar table=".djcrud-list" scope="/users/" hidden>
                <span data-role="count"></span>
            </list-action-bar>
        `
        const newBar = document.querySelector('list-action-bar')
        await Promise.resolve()

        expect(newBar.selectedPks.size).toBe(0)
        expect(newBar.hidden).toBe(true)
    })

    it('exposes clearAllListActionSelections on window for form callbacks', () => {
        expect(window.djcrudClearListActionSelections).toBe(clearAllListActionSelections)
    })
})