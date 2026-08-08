import { describe, it, expect } from "vitest";
import {
  computeDomain,
  positionFraction,
  formatYear,
  formatEra,
  shownEvents,
  eventBand,
  mapSiteUrl,
  axisTicks,
  resolveCollisions,
  DEFAULT_MIN_YEAR,
} from "../src/scale.js";
import type { AwEvent } from "@aw/data";

function ev(overrides: Partial<AwEvent> = {}): AwEvent {
  return {
    id: "e",
    title: "出来事",
    description: "説明。",
    era_start: -9600,
    era_end: null,
    era_status: "sourced",
    era_note: "頃",
    site_ids: [],
    article_url: null,
    ...overrides,
  };
}

describe("computeDomain", () => {
  it("は下限を前1万年、上限を現在にする（案A）", () => {
    const d = computeDomain([-9600, -54], 2026);
    expect(d).toEqual({ min: DEFAULT_MIN_YEAR, max: 2026 });
  });
  it("はデータが前1万年より古ければ広げる", () => {
    const d = computeDomain([-12000], 2026);
    expect(d.min).toBe(-12000);
  });
  it("はデータが空でも既定の下限を返す", () => {
    expect(computeDomain([], 2026)).toEqual({ min: DEFAULT_MIN_YEAR, max: 2026 });
  });
});

describe("positionFraction", () => {
  it("は下限で 0、上限で 1", () => {
    const d = { min: -10000, max: 2000 };
    expect(positionFraction(-10000, d)).toBe(0);
    expect(positionFraction(2000, d)).toBe(1);
  });
  it("は線形で中間を返す（案A：均等）", () => {
    const d = { min: -10000, max: 2000 };
    expect(positionFraction(-4000, d)).toBeCloseTo(0.5, 5);
  });
  it("は範囲外を 0..1 に丸める", () => {
    const d = { min: -10000, max: 2000 };
    expect(positionFraction(-20000, d)).toBe(0);
    expect(positionFraction(9999, d)).toBe(1);
  });
});

describe("formatYear", () => {
  it("は負を『前N年』", () => {
    expect(formatYear(-9600)).toBe("前9600年");
  });
  it("は正を『N年』", () => {
    expect(formatYear(79)).toBe("79年");
  });
});

describe("formatEra", () => {
  it("は但し書き（頃）を落とさない", () => {
    expect(formatEra(-9600, null, "頃")).toEqual({ yearLabel: "前9600年", note: "頃" });
  });
  it("は但し書き（以降）を落とさない", () => {
    expect(formatEra(-3500, null, "以降")).toEqual({ yearLabel: "前3500年", note: "以降" });
  });
  it("は幅のあるものを範囲で返す（点にしない）", () => {
    expect(formatEra(-1200, -1150, "頃").yearLabel).toBe("前1200年〜前1150年");
  });
});

describe("shownEvents", () => {
  it("は古い順に並べる", () => {
    const list = shownEvents([ev({ id: "a", era_start: -54 }), ev({ id: "b", era_start: -9600 })]);
    expect(list.map((e) => e.id)).toEqual(["b", "a"]);
  });
  it("は era_status が unfetched の項目を出さない（位置を推測しない）", () => {
    const list = shownEvents([
      ev({ id: "a", era_start: -9600, era_status: "sourced" }),
      ev({ id: "b", era_start: -3000, era_status: "unfetched" }),
    ]);
    expect(list.map((e) => e.id)).toEqual(["a"]);
  });
});

describe("eventBand", () => {
  it("は era_end が無ければ高さ 0（点）", () => {
    const d = { min: -10000, max: 2000 };
    expect(eventBand(ev({ era_start: -4000, era_end: null }), d).height).toBe(0);
  });
  it("は幅のあるものは高さを持つ（幅として描く）", () => {
    const d = { min: -10000, max: 2000 };
    const band = eventBand(ev({ era_start: -4000, era_end: -2000 }), d);
    expect(band.height).toBeGreaterThan(0);
    expect(band.top).toBeCloseTo(positionFraction(-4000, d), 5);
  });
});

describe("mapSiteUrl", () => {
  it("は aw-map の ?site= を指す", () => {
    expect(mapSiteUrl("gobekli-tepe", "https://aw-map.example/")).toBe(
      "https://aw-map.example/?site=gobekli-tepe",
    );
  });
  it("は base が / でも二重スラッシュにしない", () => {
    expect(mapSiteUrl("eridu", "/")).toBe("/?site=eridu");
  });
});

describe("resolveCollisions", () => {
  it("は離れているカードは真の位置のまま", () => {
    const tops = resolveCollisions(
      [
        { trueTop: 100, height: 80 },
        { trueTop: 400, height: 80 },
      ],
      14,
    );
    expect(tops).toEqual([100, 400]);
  });
  it("は重なるカードを最小間隔で下げる", () => {
    // 100 + 80 + 14 = 194 > 120 なので 2 つ目は 194 に押し下げる。
    const tops = resolveCollisions(
      [
        { trueTop: 100, height: 80 },
        { trueTop: 120, height: 80 },
      ],
      14,
    );
    expect(tops[0]).toBe(100);
    expect(tops[1]).toBe(194);
  });
  it("は押し下げが連鎖する", () => {
    const tops = resolveCollisions(
      [
        { trueTop: 0, height: 50 },
        { trueTop: 10, height: 50 },
        { trueTop: 20, height: 50 },
      ],
      10,
    );
    expect(tops).toEqual([0, 60, 120]);
  });
});

describe("axisTicks", () => {
  it("は 1000 年ごとに刻む", () => {
    const ticks = axisTicks({ min: -10000, max: 2000 });
    expect(ticks[0]).toBe(-10000);
    expect(ticks[ticks.length - 1]).toBe(2000);
    expect(ticks).toContain(0);
  });
});
