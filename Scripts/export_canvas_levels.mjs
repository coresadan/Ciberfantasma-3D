import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.dirname(here);
const sourcePath = path.resolve(projectRoot, "..", "Ciberfantasma Bros", "game.js");
const outputPath = path.join(projectRoot, "Design", "campaign_levels.json");
const source = fs.readFileSync(sourcePath, "utf8");
const marker = "const levelData = [";
const markerIndex = source.indexOf(marker);
if (markerIndex < 0) throw new Error(`No se encontro levelData en ${sourcePath}`);

const start = source.indexOf("[", markerIndex);
let depth = 0;
let quote = "";
let escaped = false;
let end = -1;
for (let index = start; index < source.length; index += 1) {
  const char = source[index];
  if (quote) {
    if (escaped) escaped = false;
    else if (char === "\\") escaped = true;
    else if (char === quote) quote = "";
    continue;
  }
  if (char === '"' || char === "'" || char === "`") {
    quote = char;
    continue;
  }
  if (char === "[") depth += 1;
  else if (char === "]") {
    depth -= 1;
    if (depth === 0) {
      end = index + 1;
      break;
    }
  }
}
if (end < 0) throw new Error("El array levelData no esta cerrado");

// levelData is a literal made only of arrays, objects, strings and numbers.
const levels = Function(`"use strict"; return (${source.slice(start, end)});`)();
if (!Array.isArray(levels) || levels.length !== 9) {
  throw new Error(`Se esperaban 9 actos y se obtuvieron ${levels?.length}`);
}
fs.writeFileSync(outputPath, `${JSON.stringify({ source_canvas: [1280, 720], levels }, null, 2)}\n`, "utf8");
console.log(`Exportados ${levels.length} actos a ${outputPath}`);
