// Build every city that has app/data/<city>.json into one static site: site/index.html (Sydney), site/<city>.html for the rest.
import { mkdirSync, copyFileSync, readdirSync, cpSync, existsSync } from "node:fs";
import { execSync } from "node:child_process";
const cities = readdirSync("data").filter((f) => f.endsWith(".json")).map((f) => f.replace(".json", ""));
const only = process.argv.includes("--copy-only");
mkdirSync("site", { recursive: true });
for (const c of cities) {
  if (!only) execSync(`npx vite build --mode ${c} --logLevel warn`, { stdio: "inherit" });
  copyFileSync(`dist/${c}/index.html`, c === "sydney" ? "site/index.html" : `site/${c}.html`);
}
if (existsSync("public/downloads")) cpSync("public/downloads", "site/downloads", { recursive: true });
if (existsSync("public/img")) cpSync("public/img", "site/img", { recursive: true });
for (const f of ["compare.html", "world.html"]) if (existsSync(`public/${f}`)) copyFileSync(`public/${f}`, `site/${f}`);
console.log(`site/ ready: ${cities.length} cities`);
