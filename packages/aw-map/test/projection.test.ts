import { describe, it, expect } from "vitest";
import { project, geometryToPath } from "../src/projection.js";

const size = { width: 360, height: 180 };

describe("project", () => {
  it("は本初子午線・赤道を中央に置く", () => {
    expect(project(0, 0, size)).toEqual([180, 90]);
  });
  it("は西経180・北緯90 を左上に置く", () => {
    expect(project(-180, 90, size)).toEqual([0, 0]);
  });
  it("は東経180・南緯90 を右下に置く", () => {
    expect(project(180, -90, size)).toEqual([360, 180]);
  });
});

describe("geometryToPath", () => {
  it("は Polygon を M...L...Z にする", () => {
    const d = geometryToPath(
      { type: "Polygon", coordinates: [[[0, 0], [10, 0], [10, 10], [0, 0]]] },
      size,
    );
    expect(d.startsWith("M180.0 90.0")).toBe(true);
    expect(d.endsWith("Z")).toBe(true);
  });
  it("は MultiPolygon を連結する", () => {
    const d = geometryToPath(
      {
        type: "MultiPolygon",
        coordinates: [
          [[[0, 0], [1, 0], [1, 1], [0, 0]]],
          [[[5, 5], [6, 5], [6, 6], [5, 5]]],
        ],
      },
      size,
    );
    expect((d.match(/Z/g) ?? []).length).toBe(2);
  });
  it("は未対応ジオメトリで空文字", () => {
    expect(geometryToPath({ type: "Point", coordinates: [0, 0] }, size)).toBe("");
  });
});
