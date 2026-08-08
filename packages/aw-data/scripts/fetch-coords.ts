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
 *
 * 取得元の優先順位は Pleiades → Wikidata。近東・地中海の遺跡は Pleiades の精度が高く、
 * 日本の遺跡は Wikidata にしかない、という題材の実態に合わせる。源をまたいで候補を単純に
 * 連結すると、両方から 1 件ずつ返っただけで「複数候補（ambiguous）」に化けてしまうため、
 * 源ごとに解決する。Pleiades が 1 件でも返せばそれで確定し、Wikidata は見ない。Pleiades が
 * 何も返さないときだけ Wikidata に問い合わせる。
 */
export async function fetchSiteCoord(site: Site, deps: FetchDeps): Promise<CoordResolution> {
  const pleiades = await deps.fetchPleiades(site);
  if (pleiades.length > 0) return resolveCoord(pleiades);
  const wikidata = await deps.fetchWikidata(site);
  return resolveCoord(wikidata);
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
  let changed = false;
  const ambiguous: string[] = [];
  const failed: string[] = [];
  let stillUnfetched = 0;

  for (const site of sites) {
    // 確定済み（verified）と、所在未特定（unlocated）は取得対象外。unlocated は取得しても
    // 埋まらないので、何度実行しても未取得件数に混ぜない。
    if (site.coord_status === "verified" || site.coord_status === "unlocated") continue;

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
      site.coord_ref = resolution.identifier;
      site.coord_status = "verified";
      updated += 1;
      changed = true;
      process.stdout.write(
        `  verified: ${site.id} <- ${resolution.identifier} (${resolution.lat}, ${resolution.lng})\n`,
      );
    } else if (resolution.status === "ambiguous") {
      // 自動選択しない。候補を出して、状態は "ambiguous" として残す（座標は入れない）。
      // これで unfetched（手つかず）と区別でき、地図側で別ラベル・別件数にできる。
      if (site.coord_status !== "ambiguous") changed = true;
      site.coord_status = "ambiguous";
      site.lat = null;
      site.lng = null;
      site.coord_source = null;
      site.coord_ref = null;
      ambiguous.push(site.id);
      process.stdout.write(`  ambiguous: ${site.id} — ${resolution.candidates.length} candidates:\n`);
      for (const c of resolution.candidates) {
        process.stdout.write(`      ${c.identifier}  (${c.lat}, ${c.lng})  [${c.source}]\n`);
      }
    } else {
      // no-result。近隣や中心で埋めない。unfetched のまま。
      stillUnfetched += 1;
    }
  }

  if (changed && !dryRun) {
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
