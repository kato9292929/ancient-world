// ヒーローのモーション。装飾のための架空の図形を使わず、aw-data の実データから形を起こす。
//
// 採用案：案3 — クラスタごとの件数を点の密度で示す。
//   座標は全件 null で地理配置に使えず、era_start を持つのは 3 件だけ。全 38 地点で欠けなく
//   使えるデータは cluster（所属クラスタ）なので、これを採る。1 地点 = 1 点。クラスタごとに
//   点をまとめ、点の数（＝件数）がそのまま密度になる。点は順に出現する（CSS アニメーション）。
//
// 使うデータ項目：sites.cluster（全 38 件）、clusters.json（順序・id）、クラスタ別件数。
// SVG のみ。画像ファイルは置かない。
import type { Site, Cluster } from "@aw/data";

export interface HeroSize {
  width: number;
  height: number;
}

// クラスタごとの色（無地・落ち着いた 7 色）。装飾ではなくクラスタの区別のため。
const CLUSTER_COLORS = [
  "#7a5c3e",
  "#8a7a3c",
  "#4f6b57",
  "#7a4b4b",
  "#4b5e7a",
  "#6b5a7a",
  "#87643a",
];

const GOLDEN_ANGLE = 2.399963229728653; // ひまわり配置

/** クラスタ中心のまわりに、k 番目の点を決める（ひまわり充填。件数が多いほど広がる＝密度）。 */
function sunflower(k: number, spacing: number): { dx: number; dy: number } {
  const r = spacing * Math.sqrt(k + 0.5);
  const theta = k * GOLDEN_ANGLE;
  return { dx: r * Math.cos(theta), dy: r * Math.sin(theta) };
}

export function heroSvg(sites: Site[], clusters: Cluster[], size: HeroSize): string {
  const { width, height } = size;
  const cy = height / 2;
  const spacing = 7;
  const dotR = 3.2;

  let globalIndex = 0;
  const groups: string[] = [];

  clusters.forEach((cluster, ci) => {
    const members = sites.filter((s) => s.cluster === cluster.id);
    if (members.length === 0) return;
    const cx = (width * (ci + 0.5)) / clusters.length;
    const color = CLUSTER_COLORS[ci % CLUSTER_COLORS.length]!;
    const dots = members
      .map((_, k) => {
        const { dx, dy } = sunflower(k, spacing);
        const i = globalIndex++;
        return `<circle class="aw-dot" cx="${(cx + dx).toFixed(1)}" cy="${(cy + dy).toFixed(1)}" r="${dotR}" fill="${color}" style="--i:${i}" />`;
      })
      .join("");
    groups.push(`<g class="aw-cluster" data-cluster="${cluster.id}">${dots}</g>`);
  });

  return `<svg class="hero-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="クラスタごとの遺跡の件数を点の密度で示した図" preserveAspectRatio="xMidYMid meet">
${groups.join("\n")}
</svg>`;
}
