import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'happy-dom',
    globals: true,
    include: [
      'src/djcrud_bulma/static/djcrud_bulma/js/form-focus.test.js',
      'src/djcrud_bulma/static/djcrud_bulma/js/filter-sidebar.test.js',
      'src/djcrud_bulma/static/djcrud_bulma/js/hamburger.test.js',
      'src/djcrud_bulma/static/djcrud_bulma/js/list-action-bar.test.js',

      'src/djcrud_bulma/static/djcrud_bulma/js/toast.test.js',
    ],
  },
})