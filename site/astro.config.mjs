import { defineConfig } from "astro/config";
import svelte from "@astrojs/svelte";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  // The site publishes as a project page under /.github/
  site: "https://hep-packaging-coordination.github.io",
  base: "/.github/",
  output: "static",
  integrations: [svelte()],
  vite: {
    plugins: [tailwindcss()],
  },
});
