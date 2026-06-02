import { describe, expect, it } from "vitest";
import { withBase } from "./base";

// These tests run without Astro's runtime, so import.meta.env.BASE_URL is
// unavailable.  withBase accepts an explicit baseUrl parameter for testability.

describe("withBase", () => {
  it("prepends base URL to a plain path segment", () => {
    expect(withBase("favicon.svg", "/.github/")).toBe("/.github/favicon.svg");
  });

  it("strips a leading slash from the path to avoid double slashes", () => {
    expect(withBase("/favicon.svg", "/.github/")).toBe("/.github/favicon.svg");
  });

  it("works when baseUrl has no trailing slash", () => {
    expect(withBase("img.png", "/.github")).toBe("/.github/img.png");
  });

  it("works at root base (no base path)", () => {
    expect(withBase("favicon.svg", "/")).toBe("/favicon.svg");
  });

  it("returns baseUrl alone for an empty path", () => {
    expect(withBase("", "/.github/")).toBe("/.github/");
  });

  it("handles nested paths", () => {
    expect(withBase("data/tools.json", "/.github/")).toBe(
      "/.github/data/tools.json",
    );
  });
});
