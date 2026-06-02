/**
 * E2e tests for the HEP Packaging Coordination landing page.
 *
 * These run against the production build (astro preview) at
 * http://localhost:4321/.github/ so the base:"/.github/" path is exercised.
 * Any missed withBase() call shows up here as a 404.
 */

import { expect, test } from "@playwright/test";

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Navigate to the site root and wait for the Svelte island to hydrate.
 *
 * Use "./" (relative) so Playwright resolves it against baseURL
 * (http://localhost:4321/.github/) rather than navigating to the root path.
 */
async function goto(page: Parameters<typeof test>[2]["page"]) {
  await page.goto("./");
  // Wait for the island to hydrate: the search input should be interactive.
  await page.waitForSelector("#tool-search", { timeout: 10_000 });
}

// ── Tests ─────────────────────────────────────────────────────────────────────

test("page loads with no console 404 errors", async ({ page }) => {
  const failures: string[] = [];
  page.on("response", (res) => {
    if (res.status() === 404) failures.push(res.url());
  });

  await goto(page);

  expect(failures, `404 responses: ${failures.join(", ")}`).toHaveLength(0);
});

test("island hydrates and shows tool list", async ({ page }) => {
  await goto(page);

  // The result count paragraph should be visible and show > 0 tools.
  const count = page.locator('[aria-live="polite"]');
  await expect(count).toBeVisible();
  const text = await count.textContent();
  expect(text).toMatch(/\d+ tools? found/);
  const n = parseInt(text!.match(/\d+/)![0]);
  expect(n).toBeGreaterThan(0);
});

test("typing a query narrows results", async ({ page }) => {
  await goto(page);

  const input = page.locator("#tool-search");
  await input.fill("pyhf");

  // Result count should drop and "pyhf" card should be visible.
  await expect(page.locator('[aria-live="polite"]')).toContainText("found");
  await expect(page.locator('a[href*="pyhf-feedstock"]').first()).toBeVisible();
});

test("typing gibberish shows empty state", async ({ page }) => {
  await goto(page);

  await page.locator("#tool-search").fill("zzznomatch99999");

  // Empty state message.
  await expect(page.locator("text=No tools found")).toBeVisible();
  // The "Clear filters" button inside empty state should appear.
  await expect(page.locator("button", { hasText: "Clear filters" }).last()).toBeVisible();
});

test("category chip filters results", async ({ page }) => {
  await goto(page);

  // Click the first category chip (Analysis).
  const chip = page.locator('[role="group"] button').first();
  const chipLabel = await chip.textContent();
  await chip.click();

  // Only cards tagged with that category should remain.
  const cards = page.locator("article");
  await expect(cards.first()).toBeVisible();

  // All remaining cards should show the selected category tag.
  const tagCount = await page.locator(`span:text("${chipLabel?.trim()}")`).count();
  const cardCount = await cards.count();
  expect(tagCount).toBe(cardCount);
});

test("clear filters chip removes category filter", async ({ page }) => {
  await goto(page);

  // Activate a filter.
  await page.locator('[role="group"] button').first().click();
  await expect(page.locator("button", { hasText: "Clear filters" })).toBeVisible();

  // Count filtered results.
  const filteredText = await page.locator('[aria-live="polite"]').textContent();
  const filteredCount = parseInt(filteredText!.match(/\d+/)![0]);

  // Clear.
  await page.locator("button", { hasText: "Clear filters" }).click();

  // Count should be back to the original total.
  const totalText = await page.locator('[aria-live="polite"]').textContent();
  const totalCount = parseInt(totalText!.match(/\d+/)![0]);
  expect(totalCount).toBeGreaterThan(filteredCount);
});

test("'Add a tool' link points to the issues page", async ({ page }) => {
  await goto(page);

  const issueLink = page.locator('a[href*="hep-packaging-coordination/.github/issues"]').first();
  await expect(issueLink).toBeVisible();
  const href = await issueLink.getAttribute("href");
  expect(href).toContain("hep-packaging-coordination/.github/issues");
});

test("shields.io badge images have absolute external src", async ({ page }) => {
  await goto(page);

  // At least one badge image should exist.
  const badge = page.locator('img[src*="img.shields.io"]').first();
  await expect(badge).toBeVisible();
  const src = await badge.getAttribute("src");
  expect(src).toMatch(/^https:\/\/img\.shields\.io\//);
});
