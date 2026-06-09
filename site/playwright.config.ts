import { defineConfig, devices } from "@playwright/test";

/**
 * E2e tests run against the production build (astro preview).
 * This exercises the real base:"/.github/" path and catches base-path bugs
 * that don't appear in dev mode.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: "html",
  use: {
    // Match the deployed base path exactly.
    baseURL: "http://localhost:4321/.github/",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    // astro preview serves the built dist/ at /.github/ when base is set.
    command: "npm run preview",
    url: "http://localhost:4321/.github/",
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
