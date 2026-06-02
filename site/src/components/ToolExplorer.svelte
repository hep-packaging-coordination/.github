<script lang="ts">
  import { filterTools } from "../lib/search";
  import type { Category } from "../lib/tools";
  import ToolCard from "./ToolCard.svelte";

  interface Props {
    categories: Category[];
  }

  const { categories }: Props = $props();

  let query = $state("");
  let activeCategories = $state<string[]>([]);

  const results = $derived(filterTools(categories, { query, activeCategories }));

  function toggleCategory(name: string) {
    if (activeCategories.includes(name)) {
      activeCategories = activeCategories.filter((c) => c !== name);
    } else {
      activeCategories = [...activeCategories, name];
    }
  }

  function clearAll() {
    query = "";
    activeCategories = [];
  }

  const hasActiveFilters = $derived(
    query.trim().length > 0 || activeCategories.length > 0,
  );

  function chipClass(name: string, isSubcategory = false) {
    const active = activeCategories.includes(name);
    const base = isSubcategory
      ? "min-h-[36px] rounded-full border px-2.5 py-1 text-xs font-medium transition-colors"
      : "min-h-[44px] rounded-full border px-3 py-1.5 text-sm font-medium transition-colors";
    const style = active
      ? "border-[var(--color-cf-primary)] bg-[var(--color-cf-primary)] text-white"
      : "border-[var(--color-cf-border)] bg-[var(--color-cf-card)] text-[var(--color-cf-text)] hover:border-[var(--color-cf-primary)] hover:text-[var(--color-cf-primary)]";
    return `${base} ${style}`;
  }
</script>

<section aria-label="Feedstock explorer">
  <!-- Search box -->
  <div class="relative mb-4">
    <label for="tool-search" class="sr-only">Search HEP feedstocks</label>
    <!-- Search icon -->
    <svg
      class="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[var(--color-cf-text-muted)]"
      aria-hidden="true"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      stroke-width="1.5"
      stroke="currentColor"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 15.803 7.5 7.5 0 0 1 15.803 15.803Z"
      />
    </svg>
    <input
      id="tool-search"
      type="search"
      placeholder="Search feedstocks, e.g. pyhf, root, awkward…"
      bind:value={query}
      class="w-full rounded-xl border border-[var(--color-cf-border)] bg-[var(--color-cf-card)] py-3 pl-10 pr-4 text-base text-[var(--color-cf-text)] placeholder-[var(--color-cf-text-muted)] shadow-sm transition-shadow focus:outline-none focus:ring-2 focus:ring-[var(--color-cf-primary)]"
      autocomplete="off"
      spellcheck="false"
    />
  </div>

  <!-- Category chips — hierarchical: top-level chips + subcategory sub-chips -->
  <div class="mb-4 space-y-2" role="group" aria-label="Filter by category">
    <div class="flex flex-wrap gap-2">
      {#each categories as cat (cat.name)}
        <!-- Top-level category chip -->
        <button
          type="button"
          onclick={() => toggleCategory(cat.name)}
          aria-pressed={activeCategories.includes(cat.name)}
          class={chipClass(cat.name)}
        >
          {cat.name}
        </button>
      {/each}

      {#if hasActiveFilters}
        <button
          type="button"
          onclick={clearAll}
          class="min-h-[44px] rounded-full border border-transparent px-3 py-1.5 text-sm text-[var(--color-cf-text-muted)] underline-offset-2 hover:underline"
        >
          Clear filters
        </button>
      {/if}
    </div>

    <!-- Subcategory chips: shown for any category that has subcategories -->
    {#each categories as cat (cat.name)}
      {#if cat.subcategories && cat.subcategories.length > 0}
        <div class="flex flex-wrap items-center gap-1.5 pl-2">
          <span class="text-xs text-[var(--color-cf-text-muted)]">{cat.name}:</span>
          {#each cat.subcategories as sub (sub.name)}
            <button
              type="button"
              onclick={() => toggleCategory(sub.name)}
              aria-pressed={activeCategories.includes(sub.name)}
              class={chipClass(sub.name, true)}
            >
              {sub.name}
            </button>
          {/each}
        </div>
      {/if}
    {/each}
  </div>

  <!-- Result count (aria-live so screen readers announce filter changes) -->
  <p
    aria-live="polite"
    aria-atomic="true"
    class="mb-4 text-sm text-[var(--color-cf-text-muted)]"
  >
    {results.length} feedstock{results.length === 1 ? "" : "s"} found
  </p>

  <!-- Results grid -->
  {#if results.length > 0}
    <ul
      class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
      role="list"
    >
      {#each results as { feedstock, categoryNames } (feedstock.name)}
        <li>
          <ToolCard {feedstock} {categoryNames} />
        </li>
      {/each}
    </ul>
  {:else}
    <!-- Empty state -->
    <div class="rounded-2xl border border-dashed border-[var(--color-cf-border)] py-16 text-center">
      <p class="text-lg font-semibold text-[var(--color-cf-text)]">
        No feedstocks found
      </p>
      <p class="mt-1 text-sm text-[var(--color-cf-text-muted)]">
        Try a different search term or clear the category filter.
      </p>
      <button
        type="button"
        onclick={clearAll}
        class="mt-4 rounded-lg bg-[var(--color-cf-primary)] px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90"
      >
        Clear filters
      </button>
    </div>
  {/if}
</section>
