// 座標取得スクリプト。Wikidata の SPARQL と Pleiades の JSON を叩き、取得できた地点だけ
// coord_status を "verified" に更新する。
//
//   このスクリプトはサンドボックスでは実行できない（外部 API に到達できないため）。
//   未実行。実行手順は README を参照。動作確認は src/coords.ts のフィクスチャ単体テストで行う。
//
// 方針（指示書より）:
//   - 引くのは緯度経度と、参照した識別子（Q コードまたは Pleiades ID）
//   - 取得できた地点だけ verified に更新。取得できなかった地点は unfetched のまま
//   - 近隣の値・中心座標・デフォルト値で埋めない
//   - 複数候補が返った場合は自動選択せず、候補を標準出力に出して当該地点をスキップ
//   - 取得失敗（例外）は握りつぶさず、件数と地点 id を標準エラーに出して非ゼロで終了
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import {
  parseWikidataResponse,
  parsePleiadesResponse,
  resolveCoord,
  type CoordCandidate,
  type CoordResolution,
} from "../src/coords.js";
import type { Site } from "../src/types.js";

const WIKIDATA_SPARQL = "https://query.wikidata.org/sparql";
// Pleiades の 1 place リソースは /places/<id>/json で JSON が返る。名称検索はここでは扱わない。
// 名称からの解決は Wikidata に寄せ、Pleiades は attributes.pleiades_id のヒントがある地点にのみ使う。

/** 地点名（ラテン文字表記）で Wikidata を引く SPARQL を組む。 */
export function buildSparqlQuery(nameEn: string): string {
  const escaped = nameEn.replace(/["\\]/g, "\\$&");
  return `SELECT ?place ?coord WHERE {
  ?place rdfs:label "${escaped}"@en .
  ?place wdt:P625 ?coord .
} LIMIT 20`;
}

export interface FetchDeps {
  fetchWikidata: (site: Site) => Promise<CoordCandidate[]>;
  fetchPleiades: (site: Site) => Promise<CoordCandidate[]>;
}

/**
 * 1 地点分の解決。ネットワークは deps に注入する（テストではフィクスチャを注入する）。
 * Wikidata と Pleiades の候補を合わせて resolveCoord に渡す。
 */
export async function fetchSiteCoord(site: Site, deps: FetchDeps): Promise<CoordResolution> {
  const candidates: CoordCandidate[] = [];
  candidates.push(...(await deps.fetchWikidata(site)));
  candidates.push(...(await deps.fetchPleiades(site)));
  return resolveCoord(candidates);
}

// ---- ここから下は実ネットワーク実装。サンドボックスでは動かない。----

const realDeps: FetchDeps = {
  async fetchWikidata(site) {
    const query = buildSparqlQuery(site.name_en);
    const url = `${WIKIDATA_SPARQL}?query=${encodeURIComponent(query)}&format=json`;
    const res = await fetch(url, {
      headers: {
        Accept: "application/sparql-results+json",
        "User-Agent": "ancient-world/aw-data coord fetcher",
      },
    });
    if (!res.ok) throw new Error(`Wikidata HTTP ${res.status}`);
    return parseWikidataResponse(await res.json());
  },
  async fetchPleiades(site) {
    const id = (site.attributes as Record<string, unknown>)?.["pleiades_id"];
    if (typeof id !== "string" || id.length === 0) return [];
    const res = await fetch(`https://pleiades.stoa.org/places/${id}/json`, {
      headers: { "User-Agent": "ancient-world/aw-data coord fetcher" },
    });
    if (!res.ok) throw new Error(`Pleiades HTTP ${res.status}`);
    const c = parsePleiadesResponse(await res.json());
    return c ? [c] : [];
  },
};

async function main(): Promise<void> {
  const dryRun = process.argv.includes("--dry-run");
  const here = dirname(fileURLToPath(import.meta.url));
  const sitesPath = resolve(here, "..", "data", "sites.json");
  const sites = JSON.parse(readFileSync(sitesPath, "utf8")) as Site[];

  let updated = 0;
  const ambiguous: string[] = [];
  const failed: string[] = [];
  let stillUnfetched = 0;

  for (const site of sites) {
    if (site.coord_status === "verified") continue;

    let resolution: CoordResolution;
    try {
      resolution = await fetchSiteCoord(site, realDeps);
    } catch (err) {
      // 取得失敗は握りつぶさない。件数と id を後でまとめて stderr に出す。
      failed.push(site.id);
      process.stderr.write(`  fetch failed: ${site.id} — ${(err as Error).message}\n`);
      continue;
    }

    if (resolution.status === "verified") {
      site.lat = resolution.lat;
      site.lng = resolution.lng;
      site.coord_source = resolution.source;
      site.coord_status = "verified";
      updated += 1;
      // 参照した識別子は出所として stdout に残す（sites.json のスキーマには持たせない）。
      process.stdout.write(
        `  verified: ${site.id} <- ${resolution.identifier} (${resolution.lat}, ${resolution.lng})\n`,
      );
    } else if (resolution.status === "ambiguous") {
      // 自動選択しない。候補を出して当該地点はスキップ。unfetched のまま残す。
      ambiguous.push(site.id);
      process.stdout.write(`  ambiguous: ${site.id} — ${resolution.candidates.length} candidates:\n`);
      for (const c of resolution.candidates) {
        process.stdout.write(`      ${c.identifier}  (${c.lat}, ${c.lng})  [${c.source}]\n`);
      }
      stillUnfetched += 1;
    } else {
      // no-result。近隣や中心で埋めない。unfetched のまま。
      stillUnfetched += 1;
    }
  }

  if (updated > 0 && !dryRun) {
    writeFileSync(sitesPath, JSON.stringify(sites, null, 2) + "\n", "utf8");
  }

  process.stdout.write(
    `\nfetch-coords: ${updated} verified, ${ambiguous.length} ambiguous, ` +
      `${stillUnfetched} still unfetched, ${failed.length} failed` +
      (dryRun ? " (dry-run, not written)" : "") +
      "\n",
  );

  if (failed.length > 0) {
    process.stderr.write(`fetch-coords: ${failed.length} failure(s): ${failed.join(", ")}\n`);
    process.exit(1);
  }
}

// テストからの import では main を走らせない。直接実行のときだけ動かす。
if (process.argv[1] && fileURLToPath(import.meta.url) === resolve(process.argv[1])) {
  main().catch((err) => {
    process.stderr.write(`fetch-coords: fatal — ${(err as Error).message}\n`);
    process.exit(1);
  });
}
