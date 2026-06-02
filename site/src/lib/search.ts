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
  /** Flat section label used for category filtering (parent name for nested). */
  categoryName: string;
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
 * Flatten all categories into SearchItems (feedstock + resolved category name).
 * Subcategories bubble up to the parent category name for chip filtering.
 */
export function flattenCategories(categories: Category[]): SearchItem[] {
  const items: SearchItem[] = [];
  for (const cat of categories) {
    if (cat.feedstocks) {
      for (const f of cat.feedstocks) {
        items.push({ feedstock: f, categoryName: cat.name });
      }
    }
    if (cat.subcategories) {
      for (const sub of cat.subcategories) {
        for (const f of sub.feedstocks) {
          // Parent category name, not subcategory name, so the top-level chip
          // "Experiment specific" shows all experiment-specific tools.
          items.push({ feedstock: f, categoryName: cat.name });
        }
      }
    }
  }
  return items;
}

/**
 * Filter the tool catalog by query and/or active category chips.
 *
 * Query and category are composed with AND: a result must satisfy both.
 * An empty query matches all items; an empty activeCategories list matches all.
 */
export function filterTools(
  categories: Category[],
  { query, activeCategories }: FilterOptions,
): SearchItem[] {
  const allItems = flattenCategories(categories);

  // Step 1: Apply category chip filter (fast exact match).
  const categoryFiltered =
    activeCategories.length === 0
      ? allItems
      : allItems.filter((item) => activeCategories.includes(item.categoryName));

  // Step 2: Apply fuzzy query (only if non-empty).
  if (!query.trim()) {
    return categoryFiltered;
  }

  const fuse = new Fuse(categoryFiltered, FUSE_OPTIONS);
  return fuse.search(query).map((r) => r.item);
}
