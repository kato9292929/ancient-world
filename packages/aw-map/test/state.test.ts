import { describe, it, expect } from "vitest";
import { parseState, serializeState, clampYear } from "../src/state.js";

describe("parseState", () => {
  it("は ?site= を読む", () => {
    expect(parseState("?site=gobekli-tepe").site).toBe("gobekli-tepe");
  });
  it("は ?year= を整数で読む", () => {
    expect(parseState("?year=-5000").year).toBe(-5000);
  });
  it("は ?cluster= を読む", () => {
    expect(parseState("?cluster=sumer").cluster).toBe("sumer");
  });
  it("は 3 つ同時に読む", () => {
    expect(parseState("?site=ur&year=-3000&cluster=sumer")).toEqual({
      site: "ur",
      year: -3000,
      cluster: "sumer",
    });
  });
  it("は無い/空のキーを null にする", () => {
    expect(parseState("")).toEqual({ site: null, year: null, cluster: null });
    expect(parseState("?site=&year=&cluster=")).toEqual({ site: null, year: null, cluster: null });
  });
  it("は不正な year を null にする", () => {
    expect(parseState("?year=abc").year).toBeNull();
  });
});

describe("serializeState", () => {
  it("は null を出さない", () => {
    expect(serializeState({ site: null, year: null, cluster: null })).toBe("");
  });
  it("は year=0 を出す（負・ゼロも有効値）", () => {
    expect(serializeState({ site: null, year: 0, cluster: null })).toBe("?year=0");
  });
  it("は往復で一致する", () => {
    const s = { site: "ur", year: -3000, cluster: "sumer" };
    expect(parseState(serializeState(s))).toEqual(s);
  });
});

describe("clampYear", () => {
  it("は範囲内に丸める", () => {
    expect(clampYear(100, -9600, -54)).toBe(-54);
    expect(clampYear(-99999, -9600, -54)).toBe(-9600);
    expect(clampYear(-5000, -9600, -54)).toBe(-5000);
  });
});
