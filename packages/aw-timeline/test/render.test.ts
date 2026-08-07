import { describe, it, expect } from "vitest";
import { renderTimelineHtml, escapeHtml } from "../src/render.js";
import type { AwEvent, Site } from "@aw/data";

const opts = {
  currentYear: 2026,
  mapBase: "https://aw-map.example/",
  css: "/*css*/",
  enhanceJs: "/*js*/",
};

function ev(overrides: Partial<AwEvent> = {}): AwEvent {
  return {
    id: "younger-dryas",
    title: "ヤンガードリアス",
    description: "急激な寒冷化。",
    era_start: -9600,
    era_end: null,
    era_status: "sourced",
    era_note: "頃",
    site_ids: [],
    article_url: null,
    ...overrides,
  };
}

function site(overrides: Partial<Site> = {}): Site {
  return {
    id: "gobekli-tepe",
    name_ja: "ギョベクリ・テペ",
    name_en: "Göbekli Tepe",
    cluster: "c",
    country: "トルコ",
    lat: null,
    lng: null,
    coord_source: null,
    coord_ref: null,
    coord_status: "unfetched",
    era_start: -9600,
    era_end: null,
    era_status: "sourced",
    era_note: "",
    attributes: {},
    article_url: null,
    summary: [],
    ...overrides,
  };
}

describe("renderTimelineHtml", () => {
  it("は全出来事を出す", () => {
    const html = renderTimelineHtml(
      [ev({ id: "a", title: "出来事A" }), ev({ id: "b", title: "出来事B", era_start: -3000 })],
      [],
      opts,
    );
    expect(html).toContain("出来事A");
    expect(html).toContain("出来事B");
  });

  it("は但し書き（頃）を表示に残す", () => {
    const html = renderTimelineHtml([ev({ era_note: "頃" })], [], opts);
    expect(html).toContain("頃");
  });

  it("は関連地点を aw-map の ?site= にリンクする", () => {
    const html = renderTimelineHtml(
      [ev({ site_ids: ["gobekli-tepe"] })],
      [site()],
      opts,
    );
    expect(html).toContain('href="https://aw-map.example/?site=gobekli-tepe"');
    expect(html).toContain("ギョベクリ・テペ");
  });

  it("は article_url があればリンクを出し、null なら出さない", () => {
    const withUrl = renderTimelineHtml([ev({ article_url: "https://note.com/x/1" })], [], opts);
    expect(withUrl).toContain("記事を読む");
    const withoutUrl = renderTimelineHtml([ev({ article_url: null })], [], opts);
    expect(withoutUrl).not.toContain("記事を読む");
  });

  it("は era_status が unfetched の項目を出さず、件数を注記する", () => {
    const html = renderTimelineHtml(
      [ev({ id: "shown" }), ev({ id: "hidden", title: "隠す出来事", era_status: "unfetched" })],
      [],
      opts,
    );
    expect(html).not.toContain("隠す出来事");
    expect(html).toContain("1 件");
  });

  it("は幅のある年代に band を描く（点にしない）", () => {
    const html = renderTimelineHtml([ev({ era_start: -4000, era_end: -2000 })], [], opts);
    expect(html).toContain('class="band"');
  });

  it("は no-js クラスを付け、JS 有効化スクリプトを埋める", () => {
    const html = renderTimelineHtml([ev()], [], opts);
    expect(html).toContain('class="no-js"');
    expect(html).toContain("classList.remove('no-js')");
  });

  it("は出来事が空でも壊れず、空の注記を出す", () => {
    const html = renderTimelineHtml([], [], opts);
    expect(html).toContain("まだ出来事のデータが入っていません");
  });

  it("は CSS と enhance スクリプトを埋め込む（外部依存なし）", () => {
    const html = renderTimelineHtml([ev()], [], { ...opts, css: "BODY{}", enhanceJs: "VAR X" });
    expect(html).toContain("BODY{}");
    expect(html).toContain("VAR X");
    // 外部 CDN への参照が無いこと。
    expect(html).not.toMatch(/https?:\/\/[^"']*\.(?:css|js|woff2?)/);
  });

  it("は HTML を電気的に無害化する", () => {
    const html = renderTimelineHtml([ev({ title: "<script>x</script>" })], [], opts);
    expect(html).not.toContain("<script>x</script>");
    expect(html).toContain("&lt;script&gt;");
  });
});

describe("escapeHtml", () => {
  it("は特殊文字を実体参照にする", () => {
    expect(escapeHtml('<a href="x">&</a>')).toBe("&lt;a href=&quot;x&quot;&gt;&amp;&lt;/a&gt;");
  });
});
