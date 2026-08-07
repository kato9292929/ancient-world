import { describe, it, expect } from "vitest";
import { validateData, type DataSet, type Schemas } from "../src/validate.js";
import sitesSchema from "../schema/sites.schema.json" with { type: "json" };
import eventsSchema from "../schema/events.schema.json" with { type: "json" };
import clustersSchema from "../schema/clusters.schema.json" with { type: "json" };

const schemas: Schemas = {
  sites: sitesSchema,
  events: eventsSchema,
  clusters: clustersSchema,
};

function baseSite(overrides: Record<string, unknown> = {}) {
  return {
    id: "eridu",
    name_ja: "エリドゥ",
    name_en: "Eridu",
    cluster: "flood-layer",
    country: "イラク",
    lat: null,
    lng: null,
    coord_source: null,
    coord_status: "unfetched",
    era_start: -5400,
    era_end: null,
    era_status: "sourced",
    era_note: "最古の層",
    attributes: { flood_layer: "absent", layer_period: null, layer_note: null },
    article_url: null,
    summary: [],
    ...overrides,
  };
}

const clusters = [{ id: "flood-layer", name_ja: "洪水層", name_en: "Flood layer" }];

function dataOf(sites: unknown[], events: unknown[] = []): DataSet {
  return { sites, events, clusters };
}

describe("validateData", () => {
  it("は空データ（骨組み状態）で通る", () => {
    const { errors } = validateData({ sites: [], events: [], clusters: [] }, schemas);
    expect(errors).toEqual([]);
  });

  it("は正しいデータで通る", () => {
    const { errors } = validateData(dataOf([baseSite()]), schemas);
    expect(errors).toEqual([]);
  });

  it("は flood_layer の absent と unknown を両方許す（区別を潰さない）", () => {
    const absent = baseSite({ id: "eridu", attributes: { flood_layer: "absent", layer_period: null, layer_note: null } });
    const unknown = baseSite({ id: "other", attributes: { flood_layer: "unknown", layer_period: null, layer_note: null } });
    const { errors } = validateData(dataOf([absent, unknown]), schemas);
    expect(errors).toEqual([]);
  });

  it("は coord_status verified なのに lat が null なら落とす", () => {
    const bad = baseSite({ coord_status: "verified", coord_source: "wikidata", lat: null, lng: 46 });
    const { errors } = validateData(dataOf([bad]), schemas);
    expect(errors.some((e) => /coord_status/.test(e.message))).toBe(true);
  });

  it("は未知の cluster を参照したら落とす", () => {
    const bad = baseSite({ cluster: "no-such-cluster" });
    const { errors } = validateData(dataOf([bad]), schemas);
    expect(errors.some((e) => /clusters\.json に無い/.test(e.message))).toBe(true);
  });

  it("は event が未知の site を参照したら落とす", () => {
    const event = {
      id: "some-event",
      title: "出来事",
      description: "説明。",
      era_start: -9600,
      era_end: null,
      era_status: "sourced",
      era_note: "頃",
      site_ids: ["ghost-site"],
      article_url: null,
    };
    const { errors } = validateData(dataOf([baseSite()], [event]), schemas);
    expect(errors.some((e) => /sites\.json に無い/.test(e.message))).toBe(true);
  });

  it("は era_start が正なのに era_note が空なら警告（落とさない）", () => {
    const s = baseSite({ era_start: 79, era_note: "" });
    const { errors, warnings } = validateData(dataOf([s]), schemas);
    expect(errors).toEqual([]);
    expect(warnings.some((w) => /era_note/.test(w.message))).toBe(true);
  });

  it("は id の重複を落とす", () => {
    const { errors } = validateData(dataOf([baseSite(), baseSite()]), schemas);
    expect(errors.some((e) => /重複/.test(e.message))).toBe(true);
  });

  it("はスキーマ違反（余計なフィールド）を落とす", () => {
    const bad = baseSite({ extra_field: "nope" });
    const { errors } = validateData(dataOf([bad]), schemas);
    expect(errors.length).toBeGreaterThan(0);
  });
});
