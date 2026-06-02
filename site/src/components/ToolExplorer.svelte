<script lang="ts">
  import { filterTools, countByCategory } from "../lib/search";
  import type { Category } from "../lib/tools";
  import ToolCard from "./ToolCard.svelte";

  interface Props {
    categories: Category[];
  }

  const { categories }: Props = $props();

  let query = $state("");
  let activeCategories = $state<string[]>([]);

  const results = $derived(filterTools(categories, { query, activeCategories }));
  const counts = $derived(countByCategory(categories));

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

  // True if any subcategory of cat is actively selected.
  function hasActiveSubcategory(cat: Category): boolean {
    return (
      (cat.subcategories?.some((s) => activeCategories.includes(s.name)) ??
        false)
    );
  }

  function chipClass(name: string, active: boolean, isSubcategory = false) {
    const base = isSubcategory
      ? "inline-flex items-center gap-1 min-h-[36px] rounded-full border px-2.5 py-1 text-xs font-medium transition-colors"
      : "inline-flex items-center gap-1.5 min-h-[44px] rounded-full border px-3 py-1.5 text-sm font-medium transition-colors";
    const style = active
      ? "border-[var(--color-cf-primary)] bg-[var(--color-cf-primary)] text-white"
      : "border-[var(--color-cf-border)] bg-[var(--color-cf-card)] text-[var(--color-cf-text)] hover:border-[var(--color-cf-primary)] hover:text-[var(--color-cf-primary)]";
    return `${base} ${style}`;
  }

  function countBadgeClass(active: boolean) {
    return active
      ? "rounded-full bg-white/25 px-1.5 py-0.5 text-xs tabular-nums leading-none"
      : "rounded-full bg-black/10 dark:bg-white/15 px-1.5 py-0.5 text-xs tabular-nums leading-none";
  }
</script>

<section aria-label="Feedstock explorer">
  <!-- Search box -->
  <div class="relative mb-4">
    <label for="tool-search" class="sr-only">Search HEP feedstocks</label>
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

  <!-- Category chips -->
  <div class="mb-4 flex flex-wrap items-center gap-2" role="group" aria-label="Filter by category">
    {#each categories as cat (cat.name)}
      {#if cat.subcategories && cat.subcategories.length > 0}
        <!--
          Category with subcategories: parent chip + dropdown on hover/focus-within.
          The wrapper div is the CSS group — hovering anywhere inside it (including
          the absolutely-positioned dropdown) keeps the dropdown visible.
        -->
        <div class="group relative">
          <!-- Parent chip: toggles parent category filter; chevron shows dropdown is available -->
          <button
            type="button"
            onclick={() => toggleCategory(cat.name)}
            aria-pressed={activeCategories.includes(cat.name)}
            aria-haspopup="true"
            class={[
              chipClass(cat.name, activeCategories.includes(cat.name)),
              hasActiveSubcategory(cat) && !activeCategories.includes(cat.name)
                ? "border-[var(--color-cf-primary-light)]"
                : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {cat.name}
            <span class={countBadgeClass(activeCategories.includes(cat.name))}>
              {counts[cat.name]}
            </span>
            <!-- Chevron rotates 180° on hover to indicate dropdown direction -->
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-3 w-3 transition-transform duration-150 group-hover:rotate-180"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="2.5"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
            </svg>
          </button>

          <!--
            Dropdown panel: hidden by default, shown on group hover or focus-within.
            flush with parent (top-full, no gap) so mouse can move into it without
            the hover state being interrupted.
          -->
          <div
            class="pointer-events-none invisible absolute left-0 top-full z-20 opacity-0 transition-[opacity,visibility] duration-150
              group-hover:pointer-events-auto group-hover:visible group-hover:opacity-100
              group-focus-within:pointer-events-auto group-focus-within:visible group-focus-within:opacity-100"
          >
            <!-- Small bridge element fills any sub-pixel gap between button and panel -->
            <div class="h-1 w-full"></div>
            <div
              class="min-w-max rounded-xl border border-[var(--color-cf-border)] bg-[var(--color-cf-card)] p-2 shadow-lg"
            >
              <p class="mb-1.5 px-1 text-xs text-[var(--color-cf-text-muted)]">
                Filter by sub-experiment:
              </p>
              <div class="flex flex-wrap gap-1.5">
                {#each cat.subcategories as sub (sub.name)}
                  <button
                    type="button"
                    onclick={() => toggleCategory(sub.name)}
                    aria-pressed={activeCategories.includes(sub.name)}
                    class={chipClass(sub.name, activeCategories.includes(sub.name), true)}
                  >
                    {sub.name}
                    <span class={countBadgeClass(activeCategories.includes(sub.name))}>
                      {counts[sub.name]}
                    </span>
                  </button>
                {/each}
              </div>
            </div>
          </div>
        </div>
      {:else}
        <!-- Flat category: simple chip, no dropdown -->
        <button
          type="button"
          onclick={() => toggleCategory(cat.name)}
          aria-pressed={activeCategories.includes(cat.name)}
          class={chipClass(cat.name, activeCategories.includes(cat.name))}
        >
          {cat.name}
          <span class={countBadgeClass(activeCategories.includes(cat.name))}>
            {counts[cat.name]}
          </span>
        </button>
      {/if}
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

  <!-- Result count -->
  <p
    aria-live="polite"
    aria-atomic="true"
    class="mb-4 text-sm text-[var(--color-cf-text-muted)]"
  >
    {results.length} feedstock{results.length === 1 ? "" : "s"} found
  </p>

  <!-- Results grid -->
  {#if results.length > 0}
    <ul class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3" role="list">
      {#each results as { feedstock, categoryNames } (feedstock.name)}
        <li>
          <ToolCard {feedstock} {categoryNames} />
        </li>
      {/each}
    </ul>
  {:else}
    <div class="rounded-2xl border border-dashed border-[var(--color-cf-border)] py-16 text-center">
      <p class="text-lg font-semibold text-[var(--color-cf-text)]">No feedstocks found</p>
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
