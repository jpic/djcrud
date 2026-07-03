<script>
  import { onMount } from 'svelte'

  let products = $state([])
  let apiError = $state('')
  let loading = $state(true)

  onMount(async () => {
    try {
      const response = await fetch('/api/product/', {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      })
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      products = await response.json()
    } catch (err) {
      apiError = err.message
    } finally {
      loading = false
    }
  })
</script>

<div class="djcrud-spa-panel">
  <nav class="navbar djcrud-spa-toolbar" role="navigation" aria-label="Toggle navigation">
    <div class="navbar-brand">
      <div class="navbar-item">
        <hamburger-menu target="#sidebar"></hamburger-menu>
      </div>
    </div>
  </nav>

  <section class="p-5">
    <h1 class="title">SPA demo</h1>
    <p class="subtitle">
      The burger lives in your SPA; djcrud renders the collapsible sidebar in
      <code>base_spa.html</code>.
    </p>
    <p>
      Menu links use <code>up-follow="false"</code> so leaving the SPA reloads the
      standard shell with navbar and server sidebar.
    </p>

    <h2 class="title is-5 mt-5">API products</h2>
    {#if loading}
      <p>Loading <code>/api/product/</code>…</p>
    {:else if apiError}
      <p class="has-text-danger">
        Could not load products ({apiError}). Enable <code>djcrud[drf]</code> per
        <code>docs/tutorial/frontend.rst</code>, or run <code>npm run api</code> to
        generate a client from <code>/api/schema/</code>.
      </p>
    {:else if products.length === 0}
      <p>No products yet. Create one via the DRF API or HTML CRUD UI.</p>
    {:else}
      <ul>
        {#each products as product (product.id)}
          <li>{product.name}</li>
        {/each}
      </ul>
    {/if}
  </section>
</div>