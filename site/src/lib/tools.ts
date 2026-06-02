/**
 * TypeScript types and Zod schema for tools.json.
 *
 * The schema here must stay in sync with render_tools_json() in
 * feedstock_data.py — the Python integration tests enforce this on the
 * Python side, and the site unit test (tools.test.ts) enforces it here
 * by parsing the committed tools.json through this schema.
 */

import { z } from "zod";

// ── Zod schema ────────────────────────────────────────────────────────────────

const FeedstockSchema = z.object({
  name: z.string(),
  outputs: z.array(z.string()),
  pr_count: z.union([z.number().int().nonnegative(), z.literal("ERROR")]),
});

const SubcategorySchema = z.object({
  name: z.string(),
  feedstocks: z.array(FeedstockSchema),
});

const CategorySchema = z.object({
  name: z.string(),
  // Flat category: feedstocks is an array, subcategories is null.
  // Nested category: feedstocks is null, subcategories is an array.
  feedstocks: z.array(FeedstockSchema).nullable(),
  subcategories: z.array(SubcategorySchema).nullable(),
});

export const ToolsDataSchema = z.object({
  generated_note: z.string(),
  categories: z.array(CategorySchema),
});

// ── TypeScript types (inferred from schema) ───────────────────────────────────

export type Feedstock = z.infer<typeof FeedstockSchema>;
export type Subcategory = z.infer<typeof SubcategorySchema>;
export type Category = z.infer<typeof CategorySchema>;
export type ToolsData = z.infer<typeof ToolsDataSchema>;
