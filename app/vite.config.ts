// One build per city: `vite build --mode tokyo` bundles app/data/tokyo.json into a single self-contained HTML file.
import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";
import { resolve } from "node:path";

export default defineConfig(({ mode }) => {
  const city = ["sydney", "tokyo"].includes(mode) ? mode : "sydney";
  return {
    base: "./",
    define: { __CITY__: JSON.stringify(city) },
    resolve: { alias: { "@city-data": resolve(__dirname, `data/${city}.json`) } },
    plugins: [viteSingleFile()],
    build: { outDir: `dist/${city}`, emptyOutDir: true, chunkSizeWarningLimit: 8000 },
  };
});
