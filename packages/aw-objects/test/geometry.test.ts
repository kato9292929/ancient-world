import { describe, it, expect } from "vitest";
import {
  WELD_BLUNDELL_PRISM,
  halfSide,
  columnDividers,
  holeFits,
  type PrismSpec,
} from "../src/geometry.js";

describe("WELD_BLUNDELL_PRISM", () => {
  it("は記録寸法（高さ20cm・幅9cm・4面・各2欄）を持つ", () => {
    expect(WELD_BLUNDELL_PRISM.height).toBe(20);
    expect(WELD_BLUNDELL_PRISM.crossSection).toBe(9);
    expect(WELD_BLUNDELL_PRISM.faceCount).toBe(4);
    expect(WELD_BLUNDELL_PRISM.columnsPerFace).toBe(2);
  });
  it("は軸穴を持つが、断面に収まる名目値である", () => {
    expect(WELD_BLUNDELL_PRISM.holeRadius).toBeGreaterThan(0);
    expect(holeFits(WELD_BLUNDELL_PRISM)).toBe(true);
  });
});

describe("halfSide", () => {
  it("は断面の半辺を返す", () => {
    expect(halfSide(WELD_BLUNDELL_PRISM)).toBe(4.5);
  });
});

describe("columnDividers", () => {
  it("は2欄なら中央に1本の区切りを返す", () => {
    expect(columnDividers(WELD_BLUNDELL_PRISM)).toEqual([0]);
  });
  it("は欄数に応じて区切り本数が変わる", () => {
    const three: PrismSpec = { ...WELD_BLUNDELL_PRISM, columnsPerFace: 2 };
    // 2欄 → 1本。将来 columnsPerFace を増やしても等分で返す。
    const spec4 = { ...three, columnsPerFace: 4 } as unknown as PrismSpec;
    expect(columnDividers(spec4)).toHaveLength(3);
  });
});

describe("holeFits", () => {
  it("は穴が半辺以上なら false", () => {
    const bad: PrismSpec = { ...WELD_BLUNDELL_PRISM, holeRadius: 10 };
    expect(holeFits(bad)).toBe(false);
  });
});
