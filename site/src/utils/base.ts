/**
 * Prepend the site's base URL to a path segment.
 *
 * In production, import.meta.env.BASE_URL is "/.github/".
 * Pass an explicit baseUrl in unit tests (where Astro's runtime is absent).
 *
 * @example
 * withBase("favicon.svg")        // "/.github/favicon.svg"
 * withBase("/data/tools.json")   // "/.github/data/tools.json"
 */
export function withBase(
  path: string,
  baseUrl: string = import.meta.env.BASE_URL ?? "/",
): string {
  // Ensure exactly one trailing slash on baseUrl, then strip any leading slash
  // from path so we never produce double slashes.
  const base = baseUrl.endsWith("/") ? baseUrl : baseUrl + "/";
  const stripped = path.startsWith("/") ? path.slice(1) : path;
  return base + stripped;
}
