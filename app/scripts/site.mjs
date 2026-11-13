// Gather the per-city builds into one static site: site/index.html (Sydney) and site/tokyo.html.
import { mkdirSync, copyFileSync } from "node:fs";
mkdirSync("site", { recursive: true });
copyFileSync("dist/sydney/index.html", "site/index.html");
copyFileSync("dist/tokyo/index.html", "site/tokyo.html");
console.log("site/ ready: index.html (Sydney), tokyo.html (Tokyo)");
