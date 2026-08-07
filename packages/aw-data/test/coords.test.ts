import { describe, it, expect } from "vitest";
import {
  parsePointWkt,
  qCodeFromUri,
  parseWikidataResponse,
  parsePleiadesResponse,
  resolveCoord,
} from "../src/coords.js";
import wikidataSingle from "./fixtures/wikidata-single.json" with { type: "json" };
import wikidataMultiple from "./fixtures/wikidata-multiple.json" with { type: "json" };
import wikidataEmpty from "./fixtures/wikidata-empty.json" with { type: "json" };
import wikidataDuplicate from "./fixtures/wikidata-duplicate.json" with { type: "json" };
import pleiadesPlace from "./fixtures/pleiades-place.json" with { type: "json" };

describe("parsePointWkt", () => {
  it("は Point(lng lat) を lat/lng に分解する", () => {
    expect(parsePointWkt("Point(38.922500 37.223056)")).toEqual({
      lat: 37.223056,
      lng: 38.9225,
    });
  });
  it("は負の値を扱う", () => {
    expect(parsePointWkt("Point(-71.5 -33.4)")).toEqual({ lat: -33.4, lng: -71.5 });
  });
  it("は形式が違えば null", () => {
    expect(parsePointWkt("38.9 37.2")).toBeNull();
    expect(parsePointWkt("")).toBeNull();
  });
});

describe("qCodeFromUri", () => {
  it("は URI から Q コードを取り出す", () => {
    expect(qCodeFromUri("http://www.wikidata.org/entity/Q1026254")).toBe("Q1026254");
  });
  it("は Q コードが無ければ null", () => {
    expect(qCodeFromUri("http://example.com/foo")).toBeNull();
  });
});

describe("parseWikidataResponse", () => {
  it("は単一候補を返す", () => {
    const c = parseWikidataResponse(wikidataSingle);
    expect(c).toHaveLength(1);
    expect(c[0]).toEqual({
      lat: 37.223056,
      lng: 38.9225,
      source: "wikidata",
      identifier: "Q1026254",
    });
  });
  it("は複数候補を返す", () => {
    expect(parseWikidataResponse(wikidataMultiple)).toHaveLength(2);
  });
  it("は空レスポンスで空配列", () => {
    expect(parseWikidataResponse(wikidataEmpty)).toEqual([]);
  });
  it("は同一エンティティの重複行を 1 件に畳む", () => {
    expect(parseWikidataResponse(wikidataDuplicate)).toHaveLength(1);
  });
});

describe("parsePleiadesResponse", () => {
  it("は reprPoint [lng, lat] を候補にする", () => {
    expect(parsePleiadesResponse(pleiadesPlace)).toEqual({
      lat: 30.816667,
      lng: 46.0,
      source: "pleiades",
      identifier: "pleiades:912986",
    });
  });
  it("は reprPoint が無ければ null", () => {
    expect(parsePleiadesResponse({ id: "x" })).toBeNull();
  });
});

describe("resolveCoord", () => {
  it("は 0 件で unfetched（近隣や中心で埋めない）", () => {
    expect(resolveCoord([])).toEqual({ status: "unfetched", reason: "no-result" });
  });
  it("は 1 件で verified", () => {
    const c = parseWikidataResponse(wikidataSingle);
    expect(resolveCoord(c)).toEqual({
      status: "verified",
      lat: 37.223056,
      lng: 38.9225,
      source: "wikidata",
      identifier: "Q1026254",
    });
  });
  it("は 2 件以上で ambiguous（自動選択しない）", () => {
    const c = parseWikidataResponse(wikidataMultiple);
    const r = resolveCoord(c);
    expect(r.status).toBe("ambiguous");
    if (r.status === "ambiguous") expect(r.candidates).toHaveLength(2);
  });
});
