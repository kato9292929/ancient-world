// 形状の生成部分。表示（three）から切り離す。スキャンが後から入手できたら、ここを差し替える。
// 純粋な寸法・形状の記述のみ。three に依存しない。
//
// 寸法の出所（Weld-Blundell Prism、記録された寸法）:
//   高さ  約20cm
//   幅    約9cm
//   面    4面。各面に2欄
//   軸穴  中心を貫通
//
// 記載のない寸法は形状に推測で埋めない。ここでの扱い:
//   - 断面の奥行きは台帳に無い。「四面の角柱」で幅のみ記載のため、断面は一辺 = 幅 の正方形として
//     扱う（square prism）。奥行きを幅と別に推測しない。
//   - 軸穴の直径は記録に無い。穴の存在は記載があるので描くが、直径は出所のない“名目値”で、
//     実測ではない（下の HOLE_DIAMETER_NOMINAL のコメントを参照）。

export interface PrismSpec {
  /** 高さ(cm)。出所あり（約20cm）。 */
  height: number;
  /** 断面の一辺(cm)。幅（約9cm）。奥行きは記載が無いため同値（正方形断面）とする。 */
  crossSection: number;
  /**
   * 軸穴の半径(cm)。**出所なしの名目値。** 記録に直径が無いため実測ではない。
   * 穴が中心を貫通する構造自体は記載があるので描くが、太さは illustrative。
   */
  holeRadius: number;
  /** 面の数。出所あり（4面）。 */
  faceCount: 4;
  /** 面あたりの欄の数。出所あり（各面2欄）。刻文は再現せず、欄の区切りだけを示す。 */
  columnsPerFace: 2;
}

// 軸穴の名目直径(cm)。出所なし。断面 9cm に対して細めに取り、貫通していることが分かる程度。
const HOLE_DIAMETER_NOMINAL = 1.4;

export const WELD_BLUNDELL_PRISM: PrismSpec = {
  height: 20,
  crossSection: 9,
  holeRadius: HOLE_DIAMETER_NOMINAL / 2,
  faceCount: 4,
  columnsPerFace: 2,
};

/** 断面正方形の半辺。 */
export function halfSide(spec: PrismSpec): number {
  return spec.crossSection / 2;
}

/**
 * 面内の欄の区切り位置（面の幅方向のローカル座標、中心 0）。
 * 2欄なら中央に1本（[0]）。刻文は描かず、この区切りだけを示す。
 */
export function columnDividers(spec: PrismSpec): number[] {
  const n = spec.columnsPerFace;
  const half = halfSide(spec);
  const out: number[] = [];
  for (let i = 1; i < n; i++) {
    out.push(-half + (spec.crossSection * i) / n);
  }
  return out;
}

/** 穴が断面に収まっているか（名目値が過大でないか）の健全性チェック。 */
export function holeFits(spec: PrismSpec): boolean {
  return spec.holeRadius > 0 && spec.holeRadius < halfSide(spec);
}
