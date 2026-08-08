import { describe, it, expect } from "vitest";
import {
  eraBounds,
  visiblePins,
  clusterCounts,
  sitesInCluster,
  STATUS_LABEL,
} from "../src/filter.js";
import type { Site, Cluster } from "@aw/data";

function site(overrides: Partial<Site> = {}): Site {
  return {
    id: "s",
    name_ja: "地点",
    name_en: "Site",
    cluster: "c1",
    country: "国",
    lat: null,
    lng: null,
    coord_source: null,
    coord_ref: null,
    coord_status: "unfetched",
    note: null,
    era_start: null,
    era_end: null,
    era_status: "unfetched",
    era_note: "",
    attributes: {},
    article_url: null,
    summary: [],
    ...overrides,
  };
}

const clusters: Cluster[] = [
  { id: "c1", name_ja: "クラスタ1" },
  { id: "c2", name_ja: "クラスタ2" },
];

describe("eraBounds", () => {
  it("は null を除いて最小・最大を返す", () => {
    const b = eraBounds([site({ era_start: -9600 }), site({ era_start: -54 }), site({ era_start: null })]);
    expect(b).toEqual({ min: -9600, max: -54 });
  });
  it("は era が全て null なら既定を返す", () => {
    expect(eraBounds([site(), site()])).toEqual({ min: -10000, max: 0 });
  });
});

describe("visiblePins", () => {
  it("は verified で座標のある地点だけ返す", () => {
    const sites = [
      site({ id: "v", coord_status: "verified", lat: 37, lng: 38, era_start: -9600 }),
      site({ id: "u", coord_status: "unfetched", era_start: -9600 }),
      site({ id: "un", coord_status: "unlocated" }),
    ];
    const pins = visiblePins(sites, 0, null);
    expect(pins.map((s) => s.id)).toEqual(["v"]);
  });
  it("はスライダー値以前に成立した地点だけ出す", () => {
    const sites = [
      site({ id: "old", coord_status: "verified", lat: 1, lng: 1, era_start: -9600 }),
      site({ id: "new", coord_status: "verified", lat: 2, lng: 2, era_start: -54 }),
    ];
    expect(visiblePins(sites, -5000, null).map((s) => s.id)).toEqual(["old"]);
    expect(visiblePins(sites, 0, null).map((s) => s.id)).toEqual(["old", "new"]);
  });
  it("は era_start が null の verified は常に出す（年代不明で消さない）", () => {
    const sites = [site({ id: "v", coord_status: "verified", lat: 1, lng: 1, era_start: null })];
    expect(visiblePins(sites, -9999, null)).toHaveLength(1);
  });
  it("は cluster で絞れる", () => {
    const sites = [
      site({ id: "a", cluster: "c1", coord_status: "verified", lat: 1, lng: 1, era_start: -100 }),
      site({ id: "b", cluster: "c2", coord_status: "verified", lat: 2, lng: 2, era_start: -100 }),
    ];
    expect(visiblePins(sites, 0, "c2").map((s) => s.id)).toEqual(["b"]);
  });
});

describe("clusterCounts", () => {
  it("は clusters の順で件数と状態内訳を返す", () => {
    const sites = [
      site({ cluster: "c1", coord_status: "unfetched" }),
      site({ cluster: "c1", coord_status: "unlocated" }),
      site({ cluster: "c1", coord_status: "verified", lat: 1, lng: 1 }),
      site({ cluster: "c2", coord_status: "ambiguous" }),
    ];
    const counts = clusterCounts(sites, clusters);
    expect(counts[0]).toEqual({ id: "c1", total: 3, verified: 1, ambiguous: 0, unlocated: 1, unfetched: 1 });
    expect(counts[1]).toEqual({ id: "c2", total: 1, verified: 0, ambiguous: 1, unlocated: 0, unfetched: 0 });
  });
});

describe("sitesInCluster", () => {
  it("は sites.json の並びを保つ", () => {
    const sites = [site({ id: "a", cluster: "c1" }), site({ id: "b", cluster: "c2" }), site({ id: "c", cluster: "c1" })];
    expect(sitesInCluster(sites, "c1").map((s) => s.id)).toEqual(["a", "c"]);
  });
});

describe("STATUS_LABEL", () => {
  it("は unfetched / unlocated / ambiguous を区別する", () => {
    expect(STATUS_LABEL.unfetched).toBe("座標未取得");
    expect(STATUS_LABEL.unlocated).toBe("所在未特定");
    expect(STATUS_LABEL.ambiguous).toBe("候補が複数");
    expect(STATUS_LABEL.verified).toBe("");
  });
});
