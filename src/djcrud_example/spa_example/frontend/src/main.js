import { mount } from 'svelte'
import App from './App.svelte'
import '../../../../djcrud_bulma/static/djcrud_bulma/js/hamburger.js'

const target = document.getElementById('app')
if (target) {
  mount(App, { target })
}