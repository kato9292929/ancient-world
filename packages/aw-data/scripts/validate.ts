// CLI ラッパー。data/*.json と schema/*.json を読み、src/validate.ts に渡し、
// 結果に応じて終了コードを決める。CI で回す。
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { validateData } from "../src/validate.js";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "..");

function readJson(rel: string): unknown {
  return JSON.parse(readFileSync(resolve(root, rel), "utf8"));
}

function main(): void {
  const data = {
    sites: readJson("data/sites.json"),
    events: readJson("data/events.json"),
    clusters: readJson("data/clusters.json"),
  };
  const schemas = {
    sites: readJson("schema/sites.schema.json") as object,
    events: readJson("schema/events.schema.json") as object,
    clusters: readJson("schema/clusters.schema.json") as object,
  };

  const { errors, warnings } = validateData(data, schemas);

  for (const w of warnings) {
    process.stderr.write(`warning  ${w.where}: ${w.message}\n`);
  }
  for (const e of errors) {
    process.stderr.write(`error    ${e.where}: ${e.message}\n`);
  }

  const nSites = Array.isArray(data.sites) ? data.sites.length : 0;
  const nEvents = Array.isArray(data.events) ? data.events.length : 0;
  const nClusters = Array.isArray(data.clusters) ? data.clusters.length : 0;
  process.stdout.write(
    `checked: ${nSites} sites, ${nEvents} events, ${nClusters} clusters — ` +
      `${errors.length} error(s), ${warnings.length} warning(s)\n`,
  );

  if (errors.length > 0) {
    process.exit(1);
  }
}

main();
