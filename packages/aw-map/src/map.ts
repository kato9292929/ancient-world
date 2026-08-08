// 中央の地図。同梱した Natural Earth の TopoJSON（world-atlas、パブリックドメイン）から
// 国境を SVG で描く。外部タイルサーバに依存しない。ピンも同じ投影で置く。
import { feature } from "topojson-client";
import countries110m from "world-atlas/countries-110m.json";
import { project, geometryToPath, type Size } from "./projection.js";
import type { Site } from "@aw/data";
import { escapeHtml } from "./detail.js";

export const MAP_SIZE: Size = { width: 1000, height: 500 };

/** 国境ポリゴンの path d 配列。 */
function countryPaths(): string[] {
  // topojson の型は緩いので any で受ける。
  const topo = countries110m as unknown as {
    objects: { countries: unknown };
  };
  const fc = feature(topo as never, topo.objects.countries as never) as unknown as {
    features: { geometry: { type: string; coordinates: unknown } }[];
  };
  return fc.features.map((f) => geometryToPath(f.geometry, MAP_SIZE)).filter((d) => d.length > 0);
}

/** 地図の SVG（国境 + 空のピン用グループ）。データ読み込みに失敗したら投げる。 */
export function buildMapSvg(): string {
  const paths = countryPaths();
  if (paths.length === 0) {
    // 地形データが読めないのに空の地図を出して正常終了しない。失敗として落とす。
    throw new Error("地形データ（world-atlas countries-110m）を描画できませんでした");
  }
  const land = paths.map((d) => `<path class="country" d="${d}" />`).join("");
  return `<svg class="worldmap" viewBox="0 0 ${MAP_SIZE.width} ${MAP_SIZE.height}" role="img" aria-label="世界地図と遺跡のピン" preserveAspectRatio="xMidYMid meet">
  <rect class="ocean" x="0" y="0" width="${MAP_SIZE.width}" height="${MAP_SIZE.height}" />
  <g class="land">${land}</g>
  <g class="pins"></g>
</svg>`;
}

/** verified 地点のピン群 SVG。呼び出し側が .pins グループに差し込む。 */
export function pinsSvg(sites: Site[], selectedId: string | null): string {
  return sites
    .map((s) => {
      const [x, y] = project(s.lng as number, s.lat as number, MAP_SIZE);
      const sel = s.id === selectedId ? " is-selected" : "";
      return `<g class="pin${sel}" data-id="${escapeHtml(s.id)}" transform="translate(${x.toFixed(1)} ${y.toFixed(1)})" tabindex="0" role="button" aria-label="${escapeHtml(s.name_ja)}">
      <circle class="pin-dot" r="6" />
      <title>${escapeHtml(s.name_ja)}</title>
    </g>`;
    })
    .join("");
}
