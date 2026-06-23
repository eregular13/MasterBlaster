<script>
  let target = 'example.com';
  const adapters = [
    {
      id: 'a0.fixture.inventory',
      tier: 'A0',
      mode: 'offline_fixture',
      description: 'Offline fixture parser with no network transport.'
    },
    {
      id: 'a1.tls.assessment',
      tier: 'A1',
      mode: 'fake_transport',
      description: 'TLS parser exercised behind a fake transport.'
    }
  ];
</script>

<main>
  <section class="topbar">
    <div>
      <h1>MasterBlaster P0 Simulator</h1>
      <p>Reviewed manifests, scope policy, signed jobs, and fixture evidence only.</p>
    </div>
    <label>
      Target binding
      <input bind:value={target} placeholder="example.com" />
    </label>
  </section>

  <section class="grid">
    {#each adapters as adapter}
      <article>
        <span>{adapter.tier}</span>
        <h2>{adapter.id}</h2>
        <p>{adapter.description}</p>
        <dl>
          <dt>Mode</dt>
          <dd>{adapter.mode}</dd>
          <dt>Target</dt>
          <dd>{target}</dd>
        </dl>
      </article>
    {/each}
  </section>
</main>

<style>
  :global(body) {
    margin: 0;
    background: #111;
    color: #e8f7ef;
    font-family: Inter, ui-sans-serif, system-ui, sans-serif;
  }

  main {
    min-height: 100vh;
    padding: 24px;
  }

  .topbar {
    display: flex;
    gap: 24px;
    align-items: end;
    justify-content: space-between;
    border-bottom: 1px solid #2c2c2c;
    padding-bottom: 18px;
  }

  h1 {
    margin: 0;
    color: #00ff9d;
    font-size: 28px;
  }

  p {
    margin: 8px 0 0;
    color: #b7c7bf;
  }

  label {
    display: grid;
    gap: 6px;
    min-width: 280px;
    color: #b7c7bf;
  }

  input {
    background: #0a0a0a;
    border: 1px solid #333;
    color: #e8f7ef;
    padding: 10px 12px;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 12px;
    margin-top: 20px;
  }

  article {
    border: 1px solid #333;
    border-radius: 6px;
    padding: 16px;
    background: #1a1a1a;
  }

  span {
    color: #111;
    background: #00ff9d;
    padding: 2px 6px;
    font-weight: 700;
  }

  h2 {
    margin: 12px 0 0;
    font-size: 18px;
  }

  dl {
    display: grid;
    grid-template-columns: 80px 1fr;
    gap: 6px;
    margin: 16px 0 0;
  }

  dt {
    color: #8fa79a;
  }

  dd {
    margin: 0;
  }
</style>
