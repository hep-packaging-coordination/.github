/**
 * Pure search and filter logic for the ToolExplorer island.
 *
 * No Svelte state lives here — this module is independently unit-testable.
 * The island wires Svelte $state to these functions.
 */

import Fuse from "fuse.js";
import type { Category, Feedstock } from "./tools";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface SearchItem {
  feedstock: Feedstock;
  /**
   * All category labels that apply to this feedstock.
   * For flat categories: one entry, e.g. ["Analysis"].
   * For feedstocks in multiple categories: all of them, e.g. ["Simulation", "Scikit-HEP"].
   * For subcategory feedstocks: parent + subcategory, e.g. ["Experiment specific", "ATLAS"].
   */
  categoryNames: string[];
}

export interface FilterOptions {
  query: string;
  /** Category names that are toggled on.  Empty array = no filter applied. */
  activeCategories: string[];
}

// ── Fuse.js configuration ─────────────────────────────────────────────────────

const FUSE_OPTIONS: Fuse.IFuseOptions<SearchItem> = {
  keys: [
    { name: "feedstock.name", weight: 2 },
    { name: "feedstock.outputs", weight: 1 },
  ],
  threshold: 0.45, // allow ~1-2 character typos on short names
  includeScore: true,
  shouldSort: true,
  ignoreLocation: true,
};

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Flatten all categories into SearchItems, merging feedstocks that appear
 * in multiple categories into one item with multiple categoryNames entries.
 *
 * For subcategory feedstocks, both the parent category name AND the
 * subcategory name are included so each can be used as an independent filter.
 *
 * The resulting list has one entry per unique feedstock.name, making
 * feedstock.name a valid unique Svelte each key.
 */
export function flattenCategories(categories: Category[]): SearchItem[] {
  const byName = new Map<string, SearchItem>();

  function addFeedstock(f: Feedstock, ...names: string[]) {
    const existing = byName.get(f.name);
    if (existing) {
      for (const name of names) {
        if (!existing.categoryNames.includes(name)) {
          existing.categoryNames.push(name);
        }
      }
    } else {
      byName.set(f.name, { feedstock: f, categoryNames: [...names] });
    }
  }

  for (const cat of categories) {
    if (cat.feedstocks) {
      for (const f of cat.feedstocks) {
        addFeedstock(f, cat.name);
      }
    }
    if (cat.subcategories) {
      for (const sub of cat.subcategories) {
        for (const f of sub.feedstocks) {
          // Include BOTH parent category and subcategory name so both
          // the "Experiment specific" chip and the "ATLAS" chip filter correctly.
          addFeedstock(f, cat.name, sub.name);
        }
      }
    }
  }

  return Array.from(byName.values());
}

/**
 * Filter the feedstock catalog by query and/or active category chips.
 *
 * Query and category are composed with AND: a result must satisfy both.
 * An empty query matches all items; an empty activeCategories list matches all.
 * A feedstock matches the category filter if ANY of its categoryNames is active.
 */
export function filterTools(
  categories: Category[],
  { query, activeCategories }: FilterOptions,
): SearchItem[] {
  const allItems = flattenCategories(categories);

  // Step 1: Category chip filter — feedstock matches if any of its labels is active.
  const categoryFiltered =
    activeCategories.length === 0
      ? allItems
      : allItems.filter((item) =>
          item.categoryNames.some((cn) => activeCategories.includes(cn)),
        );

  // Step 2: Fuzzy query filter (only if non-empty).
  if (!query.trim()) {
    return categoryFiltered;
  }

  const fuse = new Fuse(categoryFiltered, FUSE_OPTIONS);
  return fuse.search(query).map((r) => r.item);
}
