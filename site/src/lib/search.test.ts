import { describe, expect, it } from "vitest";
import { filterTools } from "./search";
import type { Feedstock, Category } from "./tools";

// ── Test fixtures ─────────────────────────────────────────────────────────────

const PYHF: Feedstock = {
  name: "pyhf",
  outputs: ["pyhf"],
  pr_count: 0,
};

const ROOT: Feedstock = {
  name: "root",
  outputs: ["root", "root-binaries"],
  pr_count: 3,
};

const HISTFITTER: Feedstock = {
  name: "histfitter",
  outputs: ["histfitter"],
  pr_count: 1,
};

const CMS_COMBINE: Feedstock = {
  name: "cms-combine",
  outputs: ["cms-combine"],
  pr_count: 2,
};

// Flat categories.
const CAT_STATS: Category = {
  name: "Statistical Modeling",
  feedstocks: [PYHF],
  subcategories: null,
};
const CAT_ANALYSIS: Category = {
  name: "Analysis",
  feedstocks: [ROOT],
  subcategories: null,
};
// Nested category.
const CAT_EXP: Category = {
  name: "Experiment specific",
  feedstocks: null,
  subcategories: [
    { name: "ATLAS", feedstocks: [HISTFITTER] },
    { name: "CMS", feedstocks: [CMS_COMBINE] },
  ],
};

const ALL_CATEGORIES: Category[] = [CAT_STATS, CAT_ANALYSIS, CAT_EXP];

// ── filterTools tests ─────────────────────────────────────────────────────────

describe("filterTools", () => {
  describe("empty query", () => {
    it("returns all feedstocks when query and activeCategories are empty", () => {
      const result = filterTools(ALL_CATEGORIES, {
        query: "",
        activeCategories: [],
      });
      // 4 feedstocks across all categories
      expect(result).toHaveLength(4);
    });
  });

  describe("query matching", () => {
    it("returns feedstock by exact name match", () => {
      const result = filterTools(ALL_CATEGORIES, {
        query: "pyhf",
        activeCategories: [],
      });
      expect(result.map((r) => r.feedstock.name)).toContain("pyhf");
    });

    it("returns feedstock by fuzzy name match (single character substitution)", () => {
      // "pyhc" substitutes the last character — a realistic keyboard typo
      const result = filterTools(ALL_CATEGORIES, {
        query: "pyhc",
        activeCategories: [],
      });
      expect(result.map((r) => r.feedstock.name)).toContain("pyhf");
    });

    it("returns feedstock when query matches an output name", () => {
      const result = filterTools(ALL_CATEGORIES, {
        query: "root-binaries",
        activeCategories: [],
      });
      expect(result.map((r) => r.feedstock.name)).toContain("root");
    });

    it("returns empty array for a query that matches nothing", () => {
      const result = filterTools(ALL_CATEGORIES, {
        query: "zzznomatch9999",
        activeCategories: [],
      });
      expect(result).toHaveLength(0);
    });
  });

  describe("category chip filtering", () => {
    it("returns only feedstocks from the active category", () => {
      const result = filterTools(ALL_CATEGORIES, {
        query: "",
        activeCategories: ["Statistical Modeling"],
      });
      expect(result).toHaveLength(1);
      expect(result[0].feedstock.name).toBe("pyhf");
    });

    it("returns feedstocks from multiple active categories", () => {
      const result = filterTools(ALL_CATEGORIES, {
        query: "",
        activeCategories: ["Statistical Modeling", "Analysis"],
      });
      const names = result.map((r) => r.feedstock.name);
      expect(names).toContain("pyhf");
      expect(names).toContain("root");
      expect(result).toHaveLength(2);
    });

    it("includes feedstocks from nested subcategories when parent category active", () => {
      const result = filterTools(ALL_CATEGORIES, {
        query: "",
        activeCategories: ["Experiment specific"],
      });
      const names = result.map((r) => r.feedstock.name);
      expect(names).toContain("histfitter");
      expect(names).toContain("cms-combine");
    });
  });

  describe("query + category chip compose (AND)", () => {
    it("returns feedstocks matching both the query and an active category", () => {
      // pyhf is in "Statistical Modeling"; root is in "Analysis"
      const result = filterTools(ALL_CATEGORIES, {
        query: "pyhf",
        activeCategories: ["Statistical Modeling"],
      });
      expect(result).toHaveLength(1);
      expect(result[0].feedstock.name).toBe("pyhf");
    });

    it("returns empty when query matches but category chip excludes it", () => {
      const result = filterTools(ALL_CATEGORIES, {
        query: "pyhf",
        activeCategories: ["Analysis"], // pyhf is not in Analysis
      });
      expect(result).toHaveLength(0);
    });
  });

  describe("result shape", () => {
    it("each result carries the feedstock and its resolved category name", () => {
      const result = filterTools(ALL_CATEGORIES, {
        query: "pyhf",
        activeCategories: [],
      });
      expect(result[0]).toMatchObject({
        feedstock: { name: "pyhf" },
        categoryName: "Statistical Modeling",
      });
    });

    it("feedstock in a subcategory carries the parent category name", () => {
      const result = filterTools(ALL_CATEGORIES, {
        query: "histfitter",
        activeCategories: [],
      });
      expect(result[0]).toMatchObject({
        feedstock: { name: "histfitter" },
        categoryName: "Experiment specific",
      });
    });
  });
});
