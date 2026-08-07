import { describe, it, expect } from "vitest";
import { buildSparqlQuery, fetchSiteCoord, type FetchDeps } from "../scripts/fetch-coords.js";
import { parseWikidataResponse, parsePleiadesResponse, type CoordCandidate } from "../src/coords.js";
import type { Site } from "../src/types.js";
import wikidataSingle from "./fixtures/wikidata-single.json" with { type: "json" };
import wikidataMultiple from "./fixtures/wikidata-multiple.json" with { type: "json" };
import wikidataEmpty from "./fixtures/wikidata-empty.json" with { type: "json" };

function site(overrides: Partial<Site> = {}): Site {
  return {
    id: "test-site",
    name_ja: "テスト",
    name_en: "Test Site",
    cluster: "test",
    country: "テスト国",
    lat: null,
    lng: null,
    coord_source: null,
    coord_status: "unfetched",
    era_start: -9000,
    era_end: null,
    era_status: "sourced",
    era_note: "",
    attributes: {},
    article_url: null,
    summary: [],
    ...overrides,
  };
}

const noPleiades = async (): Promise<CoordCandidate[]> => [];

describe("buildSparqlQuery", () => {
  it("は名称を label 条件に埋める", () => {
    expect(buildSparqlQuery("Eridu")).toContain('"Eridu"@en');
  });
  it("は引用符とバックスラッシュをエスケープする", () => {
    const q = buildSparqlQuery('A "quoted" \\ name');
    expect(q).toContain('\\"quoted\\"');
    expect(q).toContain("\\\\");
  });
});

describe("fetchSiteCoord（フィクスチャを注入）", () => {
  it("は単一候補で verified を返す", async () => {
    const deps: FetchDeps = {
      fetchWikidata: async () => parseWikidataResponse(wikidataSingle),
      fetchPleiades: noPleiades,
    };
    const r = await fetchSiteCoord(site(), deps);
    expect(r.status).toBe("verified");
    if (r.status === "verified") {
      expect(r.lat).toBe(37.223056);
      expect(r.source).toBe("wikidata");
    }
  });

  it("は複数候補で ambiguous を返す（勝手に選ばない）", async () => {
    const deps: FetchDeps = {
      fetchWikidata: async () => parseWikidataResponse(wikidataMultiple),
      fetchPleiades: noPleiades,
    };
    const r = await fetchSiteCoord(site(), deps);
    expect(r.status).toBe("ambiguous");
  });

  it("は候補ゼロで unfetched を返す（埋めない）", async () => {
    const deps: FetchDeps = {
      fetchWikidata: async () => parseWikidataResponse(wikidataEmpty),
      fetchPleiades: noPleiades,
    };
    const r = await fetchSiteCoord(site(), deps);
    expect(r.status).toBe("unfetched");
  });

  it("は Wikidata が空でも Pleiades のヒントで解決できる", async () => {
    const pleiades = parsePleiadesResponse({ id: "912986", reprPoint: [46.0, 30.816667] });
    const deps: FetchDeps = {
      fetchWikidata: async () => [],
      fetchPleiades: async () => (pleiades ? [pleiades] : []),
    };
    const r = await fetchSiteCoord(site({ attributes: { pleiades_id: "912986" } }), deps);
    expect(r.status).toBe("verified");
    if (r.status === "verified") expect(r.source).toBe("pleiades");
  });

  it("は Pleiades を優先し、両方から取れても ambiguous にしない", async () => {
    // 源をまたいで連結していたら 2 候補で ambiguous になるが、Pleiades 優先なので verified。
    const pleiades = parsePleiadesResponse({ id: "912986", reprPoint: [46.0, 30.816667] })!;
    let wikidataCalled = false;
    const deps: FetchDeps = {
      fetchWikidata: async () => {
        wikidataCalled = true;
        return parseWikidataResponse(wikidataSingle);
      },
      fetchPleiades: async () => [pleiades],
    };
    const r = await fetchSiteCoord(site(), deps);
    expect(r.status).toBe("verified");
    if (r.status === "verified") expect(r.source).toBe("pleiades");
    // Pleiades で決まったら Wikidata は見ない。
    expect(wikidataCalled).toBe(false);
  });

  it("は Pleiades が空のときだけ Wikidata を見る", async () => {
    let wikidataCalled = false;
    const deps: FetchDeps = {
      fetchWikidata: async () => {
        wikidataCalled = true;
        return parseWikidataResponse(wikidataSingle);
      },
      fetchPleiades: async () => [],
    };
    const r = await fetchSiteCoord(site(), deps);
    expect(wikidataCalled).toBe(true);
    expect(r.status).toBe("verified");
    if (r.status === "verified") expect(r.source).toBe("wikidata");
  });
});
