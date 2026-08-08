import { describe, it, expect } from "vitest";
import { heroSvg } from "../src/hero.js";
import type { Site, Cluster } from "@aw/data";

function site(id: string, cluster: string): Site {
  return {
    id,
    name_ja: id,
    name_en: id,
    cluster,
    country: "国",
    lat: null,
    lng: null,
    coord_source: null,
    coord_ref: null,
    coord_status: "unfetched",
    era_start: null,
    era_end: null,
    era_status: "unfetched",
    era_note: "",
    note: null,
    attributes: {},
    article_url: null,
    summary: [],
  };
}

const clusters: Cluster[] = [
  { id: "a", name_ja: "A" },
  { id: "b", name_ja: "B" },
];

describe("heroSvg", () => {
  it("は 1 地点 = 1 点で全件を出す（件数＝密度）", () => {
    const sites = [site("s1", "a"), site("s2", "a"), site("s3", "b")];
    const svg = heroSvg(sites, clusters, { width: 900, height: 300 });
    expect((svg.match(/class="aw-dot"/g) ?? []).length).toBe(3);
  });
  it("はクラスタごとにまとめる", () => {
    const svg = heroSvg([site("s1", "a"), site("s2", "b")], clusters, { width: 900, height: 300 });
    expect(svg).toContain('data-cluster="a"');
    expect(svg).toContain('data-cluster="b"');
  });
  it("は出現順の --i を各点に振る（CSS の遅延に使う）", () => {
    const svg = heroSvg([site("s1", "a"), site("s2", "a")], clusters, { width: 900, height: 300 });
    expect(svg).toContain("--i:0");
    expect(svg).toContain("--i:1");
  });
  it("は空クラスタを出さない", () => {
    const svg = heroSvg([site("s1", "a")], clusters, { width: 900, height: 300 });
    expect(svg).toContain('data-cluster="a"');
    expect(svg).not.toContain('data-cluster="b"');
  });
  it("は inline SVG で、画像参照を含まない", () => {
    const svg = heroSvg([site("s1", "a")], clusters, { width: 900, height: 300 });
    expect(svg).not.toMatch(/<img|url\(|\.png|\.jpg|\.svg"/);
  });
});
