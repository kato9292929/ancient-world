// 検証の中身。スキーマ検証に加えて、指示書が求める個別ルールを見る。
// ファイル I/O はここに持たない（scripts/validate.ts が読み込んで渡す）。テスト可能にするため。
import Ajv from "ajv";
import addFormats from "ajv-formats";
import type { Site, AwEvent, Cluster } from "./types.js";

export interface Diagnostic {
  level: "error" | "warning";
  where: string;
  message: string;
}

export interface Schemas {
  sites: object;
  events: object;
  clusters: object;
}

export interface DataSet {
  sites: unknown;
  events: unknown;
  clusters: unknown;
}

export interface ValidateResult {
  errors: Diagnostic[];
  warnings: Diagnostic[];
}

function runSchema(
  ajv: Ajv,
  schema: object,
  data: unknown,
  label: string,
  errors: Diagnostic[],
): boolean {
  const validate = ajv.compile(schema);
  if (validate(data)) return true;
  for (const e of validate.errors ?? []) {
    errors.push({
      level: "error",
      where: `${label}${e.instancePath}`,
      message: `${e.message ?? "schema violation"}${
        e.params && Object.keys(e.params).length ? ` (${JSON.stringify(e.params)})` : ""
      }`,
    });
  }
  return false;
}

export function validateData(data: DataSet, schemas: Schemas): ValidateResult {
  const errors: Diagnostic[] = [];
  const warnings: Diagnostic[] = [];

  const ajv = new Ajv({ allErrors: true, strict: false });
  addFormats(ajv);

  const sitesOk = runSchema(ajv, schemas.sites, data.sites, "sites", errors);
  const eventsOk = runSchema(ajv, schemas.events, data.events, "events", errors);
  const clustersOk = runSchema(ajv, schemas.clusters, data.clusters, "clusters", errors);

  // スキーマが通った配列だけ、内容ルールを見る。
  const sites = sitesOk ? (data.sites as Site[]) : [];
  const events = eventsOk ? (data.events as AwEvent[]) : [];
  const clusters = clustersOk ? (data.clusters as Cluster[]) : [];

  const clusterIds = new Set(clusters.map((c) => c.id));
  const siteIds = new Set(sites.map((s) => s.id));

  // id の重複を落とす。
  checkDuplicateIds(sites, "sites", errors);
  checkDuplicateIds(events, "events", errors);
  checkDuplicateIds(clusters, "clusters", errors);

  for (const s of sites) {
    const at = `sites[${s.id}]`;

    // coord_status: "verified" なのに lat/lng が null なら落とす。
    if (s.coord_status === "verified" && (s.lat === null || s.lng === null)) {
      errors.push({
        level: "error",
        where: at,
        message: `coord_status が "verified" だが lat/lng が null`,
      });
    }
    // verified なのに出所がないのは不整合。警告に留める。
    if (s.coord_status === "verified" && s.coord_source === null) {
      warnings.push({
        level: "warning",
        where: at,
        message: `coord_status が "verified" だが coord_source が null`,
      });
    }
    // 参照整合。cluster が clusters.json に無ければ落とす。
    if (clustersOk && !clusterIds.has(s.cluster)) {
      errors.push({
        level: "error",
        where: at,
        message: `cluster "${s.cluster}" が clusters.json に無い`,
      });
    }
    // era_start が紀元後（正）なのに但し書きが無ければ警告。
    if (s.era_start > 0 && s.era_note.trim() === "") {
      warnings.push({
        level: "warning",
        where: at,
        message: `era_start が正（紀元後 ${s.era_start}）だが era_note が空`,
      });
    }
  }

  for (const e of events) {
    const at = `events[${e.id}]`;
    // 参照整合。site_ids が sites.json に無ければ落とす。
    if (sitesOk) {
      for (const sid of e.site_ids) {
        if (!siteIds.has(sid)) {
          errors.push({
            level: "error",
            where: at,
            message: `site_ids の "${sid}" が sites.json に無い`,
          });
        }
      }
    }
    if (e.era_start > 0 && e.era_note.trim() === "") {
      warnings.push({
        level: "warning",
        where: at,
        message: `era_start が正（紀元後 ${e.era_start}）だが era_note が空`,
      });
    }
  }

  return { errors, warnings };
}

function checkDuplicateIds(
  rows: Array<{ id: string }>,
  label: string,
  errors: Diagnostic[],
): void {
  const seen = new Set<string>();
  for (const r of rows) {
    if (seen.has(r.id)) {
      errors.push({ level: "error", where: label, message: `id "${r.id}" が重複` });
    }
    seen.add(r.id);
  }
}
