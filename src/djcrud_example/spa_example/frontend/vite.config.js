import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  plugins: [svelte()],
  build: {
    outDir: '../static/spa_example/js',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: 'src/main.js',
      output: {
        entryFileNames: 'app.[hash].js',
        assetFileNames: 'app.[hash].[ext]',
      },
    },
  },
})