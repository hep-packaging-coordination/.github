<script lang="ts">
  import type { Feedstock } from "../lib/tools";

  interface Props {
    feedstock: Feedstock;
    categoryNames: string[];
  }

  const { feedstock, categoryNames }: Props = $props();

  const feedstockUrl = `https://github.com/conda-forge/${feedstock.name}-feedstock`;
  const prPageUrl = `${feedstockUrl}/pulls`;

  const outputs = $derived(feedstock.outputs);
</script>

<article
  class="rounded-2xl border border-[var(--color-cf-border)] bg-[var(--color-cf-card)] p-5 transition-shadow duration-200 hover:shadow-md"
>
  <!-- Header row -->
  <div class="mb-3 flex items-start justify-between gap-2">
    <div class="min-w-0 flex-1">
      <h3 class="truncate font-display text-base font-semibold leading-tight">
        <a
          href={feedstockUrl}
          target="_blank"
          rel="noopener noreferrer"
          class="text-[var(--color-cf-primary)] hover:underline"
        >
          {feedstock.name}
        </a>
      </h3>
      <!-- Category badges: one per category the feedstock belongs to -->
      <div class="mt-1 flex flex-wrap gap-1">
        {#each categoryNames as name (name)}
          <span
            class="inline-block rounded-full bg-[var(--color-cf-primary-lightest)] px-2 py-0.5 text-xs font-medium text-[var(--color-cf-primary-darkest)]"
          >
            {name}
          </span>
        {/each}
      </div>
    </div>

    <!-- Open PRs badge (only when > 0) -->
    {#if feedstock.pr_count !== 0 && feedstock.pr_count !== "ERROR"}
      <a
        href={prPageUrl}
        target="_blank"
        rel="noopener noreferrer"
        class="shrink-0 rounded-full bg-[var(--color-cf-warning)] px-2.5 py-0.5 text-xs font-semibold text-white"
        aria-label={`${feedstock.pr_count} open pull requests for ${feedstock.name}`}
      >
        {feedstock.pr_count} PR{feedstock.pr_count === 1 ? "" : "s"}
      </a>
    {/if}
  </div>

  <!-- Per-output shields.io badges (live, external absolute URLs) -->
  {#if outputs.length > 0}
    <div class="flex flex-col gap-2">
      {#each outputs as output (output)}
        {@const anacondaUrl = `https://anaconda.org/conda-forge/${output}`}
        <div class="flex flex-wrap items-center gap-1.5">
          <span
            class="w-28 shrink-0 truncate text-xs text-[var(--color-cf-text-muted)]"
          >
            {output}
          </span>
          <div class="flex flex-wrap gap-1">
            <a href={anacondaUrl} target="_blank" rel="noopener noreferrer">
              <img
                src={`https://img.shields.io/conda/vn/conda-forge/${output}.svg`}
                alt={`Version of ${output} on conda-forge`}
                loading="lazy"
                height="20"
              />
            </a>
            <a href={anacondaUrl} target="_blank" rel="noopener noreferrer">
              <img
                src={`https://img.shields.io/conda/dn/conda-forge/${output}.svg`}
                alt={`Downloads of ${output} on conda-forge`}
                loading="lazy"
                height="20"
              />
            </a>
            <a href={anacondaUrl} target="_blank" rel="noopener noreferrer">
              <img
                src={`https://img.shields.io/conda/pn/conda-forge/${output}.svg`}
                alt={`Platforms for ${output} on conda-forge`}
                loading="lazy"
                height="20"
              />
            </a>
          </div>
        </div>
      {/each}
    </div>
  {:else}
    <p class="text-xs italic text-[var(--color-cf-text-muted)]">
      No outputs indexed yet.
    </p>
  {/if}
</article>
