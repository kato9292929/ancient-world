import { describe, it, expect } from "vitest";
import { parseFaces, faceFor } from "../src/faces.js";

describe("parseFaces", () => {
  it("は空配列で空を返す（初期の空 faces.json）", () => {
    expect(parseFaces([])).toEqual([]);
  });
  it("は配列でないものを空にする", () => {
    expect(parseFaces(null)).toEqual([]);
    expect(parseFaces({})).toEqual([]);
  });
  it("は face 番号のある項目だけ拾う", () => {
    const faces = parseFaces([
      { face: 0, title: "第一面", body: "説明" },
      { title: "face 欠落" },
      { face: 2 },
    ]);
    expect(faces).toHaveLength(2);
    expect(faces[0]).toEqual({ face: 0, title: "第一面", body: "説明" });
    expect(faces[1]).toEqual({ face: 2, title: undefined, body: undefined });
  });
});

describe("faceFor", () => {
  it("は該当面を返し、無ければ null", () => {
    const faces = parseFaces([{ face: 1, title: "B" }]);
    expect(faceFor(faces, 1)?.title).toBe("B");
    expect(faceFor(faces, 0)).toBeNull();
  });
});
