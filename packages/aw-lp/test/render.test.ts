import { describe, it, expect } from "vitest";
import { renderLp, type Entrance } from "../src/render.js";
import { parseArticles } from "../src/articles.js";
import type { Site, Cluster } from "@aw/data";

const clusters: Cluster[] = [{ id: "a", name_ja: "A" }];
const sites: Site[] = [
  {
    id: "s1", name_ja: "地点", name_en: "Site", cluster: "a", country: "国",
    lat: null, lng: null, coord_source: null, coord_ref: null, coord_status: "unfetched",
    era_start: null, era_end: null, era_status: "unfetched", era_note: "", note: null,
    attributes: {}, article_url: null, summary: [],
  },
];

const entrances: Entrance[] = [
  { key: "map", title: "遺跡年代マップ", desc: "世界の遺跡を年代順に表示します。座標が未取得の地点は一覧に残します。", href: "/map" },
  { key: "timeline", title: "年表", desc: "前1万年から現在までを線形の尺度で並べます。空白は空白のまま表示します。", href: "/timeline" },
  { key: "objects", title: "遺物", desc: "記録された寸法から起こした模型を表示します。実物のスキャンではありません。", href: "/objects" },
];

function render(articles = parseArticles([])) {
  return renderLp(sites, clusters, { entrances, articles, css: "/*css*/" });
}

describe("renderLp", () => {
  it("は指定されたサイト名とリードを出す", () => {
    const html = render();
    expect(html).toContain("ancient world");
    expect(html).toContain("古代の遺跡と資料について、記録されている内容と、現在の研究状況を並べます。");
  });

  it("は 3 つの入口を、指定コピーとリンクで出す", () => {
    const html = render();
    expect(html).toContain("遺跡年代マップ");
    expect(html).toContain("座標が未取得の地点は一覧に残します");
    expect(html).toContain('href="/map"');
    expect(html).toContain('href="/timeline"');
    expect(html).toContain('href="/objects"');
  });

  it("は記事 0 件のときセクションを出さない（準備中も出さない）", () => {
    const html = render(parseArticles([]));
    expect(html).not.toContain('class="articles"');
    expect(html).not.toContain("記事");
    expect(html).not.toContain("準備中");
    expect(html).not.toContain("近日公開");
  });

  it("は記事 1 件でセクションを出す", () => {
    const html = render(parseArticles([{ title: "ギョベクリ・テペ", url: "https://note.com/x/1" }]));
    expect(html).toContain('class="articles"');
    expect(html).toContain("<h2>記事</h2>");
    expect(html).toContain("ギョベクリ・テペ");
    expect(html).toContain('href="https://note.com/x/1"');
  });

  it("は画像ファイルを一切参照しない", () => {
    const html = render();
    expect(html).not.toMatch(/<img|\.png|\.jpg|\.jpeg|\.webp|\.gif/);
  });

  it("は煽りの語を含まない", () => {
    const html = render(parseArticles([{ title: "記事", url: "/x" }]));
    for (const w of ["失われた文明", "隠された歴史", "驚くべき"]) {
      expect(html).not.toContain(w);
    }
  });

  it("は入口を配列から出す（4 つに増やせる）", () => {
    const four = [...entrances, { key: "compare", title: "比較", desc: "説明。", href: "/compare" }];
    const html = renderLp(sites, clusters, { entrances: four, articles: [], css: "" });
    expect((html.match(/class="entrance"/g) ?? []).length).toBe(4);
  });
});

describe("parseArticles", () => {
  it("は空配列で空", () => {
    expect(parseArticles([])).toEqual([]);
  });
  it("は title/url の無い項目を捨てる", () => {
    expect(parseArticles([{ title: "t" }, { url: "u" }, { title: "t", url: "u" }])).toHaveLength(1);
  });
});
