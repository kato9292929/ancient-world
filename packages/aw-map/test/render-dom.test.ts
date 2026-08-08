import { describe, it, expect } from "vitest";
import { buildMapSvg, pinsSvg } from "../src/map.js";
import { renderDetail } from "../src/detail.js";
import { renderClusters } from "../src/clusters.js";
import type { Site, Cluster } from "@aw/data";

function site(overrides: Partial<Site> = {}): Site {
  return {
    id: "eridu",
    name_ja: "エリドゥ",
    name_en: "Eridu",
    cluster: "sumer",
    country: "イラク",
    lat: null,
    lng: null,
    coord_source: null,
    coord_ref: null,
    coord_status: "unfetched",
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

describe("buildMapSvg", () => {
  it("は同梱地形から多数の国境パスを描く（外部タイル不要）", () => {
    const svg = buildMapSvg();
    expect(svg).toContain("<svg");
    expect((svg.match(/class="country"/g) ?? []).length).toBeGreaterThan(100);
  });
});

describe("pinsSvg", () => {
  it("は verified 地点をピンにする", () => {
    const svg = pinsSvg([site({ id: "g", name_ja: "ギョベクリ", coord_status: "verified", lat: 37.2, lng: 38.9 })], null);
    expect((svg.match(/class="pin[ "]/g) ?? []).length).toBe(1);
    expect(svg).toContain('data-id="g"');
  });
  it("は選択中のピンに印を付ける", () => {
    const svg = pinsSvg([site({ id: "g", coord_status: "verified", lat: 1, lng: 1 })], "g");
    expect(svg).toContain("is-selected");
  });
});

describe("renderDetail", () => {
  it("は未選択で案内を出す（準備中は出さない）", () => {
    const html = renderDetail(null);
    expect(html).toContain("地点を選ぶ");
    expect(html).not.toContain("準備中");
    expect(html).not.toContain("Coming");
  });
  it("は名称・国・年代の但し書きを出す", () => {
    const html = renderDetail(site({ era_start: -9600, era_status: "sourced", era_note: "最古の層" }));
    expect(html).toContain("エリドゥ");
    expect(html).toContain("前9600年");
    expect(html).toContain("最古の層");
  });
  it("は洪水層 absent と unknown を区別して出す", () => {
    const absent = renderDetail(site({ attributes: { flood_layer: "absent", layer_period: null, layer_note: null } }));
    expect(absent).toContain("なし（調査済み）");
    const unknown = renderDetail(site({ attributes: { flood_layer: "unknown", layer_period: null, layer_note: null } }));
    expect(unknown).toContain("不明");
  });
  it("は summary が空なら出さない、あれば出す", () => {
    expect(renderDetail(site({ summary: [] }))).not.toContain("<ul class=\"summary\">");
    expect(renderDetail(site({ summary: ["一文。"] }))).toContain("一文。");
  });
  it("は article_url があれば詳しくリンク、null なら出さない", () => {
    expect(renderDetail(site({ article_url: "https://note.com/x" }))).toContain("詳しく");
    expect(renderDetail(site({ article_url: null }))).not.toContain("詳しく");
  });
  it("は verified の座標を出し、未取得はラベルを出す", () => {
    expect(renderDetail(site({ coord_status: "verified", coord_source: "wikidata", lat: 30.81, lng: 46 }))).toContain("30.8100");
    expect(renderDetail(site({ coord_status: "unlocated" }))).toContain("所在未特定");
  });
});

describe("renderClusters", () => {
  const clusters: Cluster[] = [
    { id: "sumer", name_ja: "シュメール" },
    { id: "japan", name_ja: "日本" },
  ];
  it("は全地点を一覧に出し、状態バッジを付ける", () => {
    const sites = [
      site({ id: "a", cluster: "sumer", coord_status: "unfetched" }),
      site({ id: "b", cluster: "sumer", coord_status: "unlocated" }),
      site({ id: "c", cluster: "japan", coord_status: "verified", lat: 1, lng: 1 }),
    ];
    const html = renderClusters(sites, clusters, null, null);
    expect((html.match(/data-site=/g) ?? []).length).toBe(3);
    expect(html).toContain("座標未取得");
    expect(html).toContain("所在未特定");
    expect(html).toContain("全 3 地点");
  });
});
